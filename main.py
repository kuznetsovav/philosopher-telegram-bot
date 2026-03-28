from __future__ import annotations

import asyncio
import logging
import sys
from collections import defaultdict
from os import getenv
from time import time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from llm import ask_llm
from prompts import get_prompt
from texts import TEXTS, t

log = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    value = getenv(name)
    if not value:
        print(f"FATAL: {name} environment variable is not set", file=sys.stderr)
        sys.exit(1)
    return value


TOKEN = _require_env("BOT_TOKEN")
_require_env("OPENAI_API_KEY")
ADMIN_USER_ID = int(getenv("ADMIN_USER_ID", "0"))

dp = Dispatcher()

PHILOSOPHERS = {
    "nietzsche": "Nietzsche",
    "camus": "Camus",
    "sartre": "Sartre",
}
PHILOSOPHER_NAMES = list(PHILOSOPHERS.values())

LANG_BUTTONS = {"Русский": "ru", "English": "en"}

THINKING_DELAY = 1.5
MAX_HISTORY = 5
REMINDER_CHECK_INTERVAL = 3600
INACTIVE_THRESHOLD = 86400

# ── keyboards ──────────────────────────────────────────────────────────

def _problem_keyboard(lang: str) -> ReplyKeyboardMarkup:
    problems = TEXTS["problems"].get(lang, TEXTS["problems"]["en"])
    keyboard = [[KeyboardButton(text=p)] for p in problems]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _philosopher_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=name) for name in PHILOSOPHER_NAMES]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _language_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=label) for label in LANG_BUTTONS]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=t("menu_start_over", lang))],
        [
            KeyboardButton(text=t("menu_change_lang", lang)),
            KeyboardButton(text=t("menu_choose_phil", lang)),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


MENU_ACTIONS = {
    "menu_start_over": "reset",
    "menu_change_lang": "language",
    "menu_choose_phil": "philosopher",
}


def _match_menu_button(text: str, lang: str) -> str | None:
    for key, action in MENU_ACTIONS.items():
        if text == t(key, lang):
            return action
    return None


# ── state & analytics ─────────────────────────────────────────────────

user_state: dict[int, dict] = {}

ANALYTICS: dict = {
    "users": set(),
    "events": defaultdict(int, {
        "start": 0,
        "selected_option": 0,
        "entered_text": 0,
    }),
    "selected_philosopher": defaultdict(int),
    "selected_options_breakdown": defaultdict(lambda: defaultdict(int)),
    "conversation_depth": [],
    "current_sessions": {},
}


def get_total_users() -> int:
    return len(ANALYTICS["users"])


def _detect_language(language_code: str | None) -> str:
    if language_code and language_code.lower().startswith("ru"):
        return "ru"
    return "en"


def _get_lang(uid: int, message: Message) -> str:
    state = user_state.get(uid)
    if state:
        return state.get("language", "en")
    return _detect_language(message.from_user.language_code)


def _new_session() -> dict:
    return {
        "active": False,
        "started_at": None,
        "last_bot_reply_at": None,
        "last_user_msg_at": None,
        "turns": 0,
        "reminder_sent": False,
    }


def _mark_user_activity(state: dict) -> None:
    state["session"]["last_user_msg_at"] = time()


def _mark_bot_reply(state: dict) -> None:
    session = state["session"]
    session["active"] = True
    session["last_bot_reply_at"] = time()
    session["turns"] += 1
    if session["started_at"] is None:
        session["started_at"] = time()


def _close_session(state: dict, uid: int | None = None) -> None:
    state["session"]["active"] = False
    if uid is not None and uid in ANALYTICS["current_sessions"]:
        depth = ANALYTICS["current_sessions"].pop(uid)
        ANALYTICS["conversation_depth"].append(depth)


def _append_history(state: dict, role: str, content: str) -> None:
    state["history"].append({"role": role, "content": content})
    state["history"] = state["history"][-(MAX_HISTORY * 2):]


async def _send_typing_and_reply(message: Message, state: dict, bot: Bot) -> None:
    system_prompt = get_prompt(state["philosopher"], state.get("language", "en"))
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    reply = await ask_llm(system_prompt, state["history"])
    await asyncio.sleep(THINKING_DELAY)
    _append_history(state, "assistant", reply)
    _mark_bot_reply(state)
    log.info(
        "[user:%d] %s reply (turn %d): %s",
        message.chat.id, state["philosopher"],
        state["session"]["turns"], reply[:120],
    )
    lang = state.get("language", "en")
    await message.answer(
        f"<b>{state['philosopher']}</b>\n\n{reply}",
        reply_markup=_menu_keyboard(lang),
    )


# ── commands ───────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    uid = message.from_user.id
    prev = user_state.get(uid)
    prev_lang = prev["language"] if prev else None
    if prev and prev.get("session", {}).get("active"):
        _close_session(prev, uid)

    ANALYTICS["users"].add(uid)
    ANALYTICS["events"]["start"] += 1

    lang = prev_lang or _detect_language(message.from_user.language_code)
    user_state[uid] = {
        "step": "awaiting_problem",
        "language": lang,
        "session": _new_session(),
    }
    log.info("[user:%d] START (lang=%s, total_users=%d)", uid, lang, get_total_users())
    await message.answer(t("start", lang), reply_markup=_problem_keyboard(lang))


@dp.message(Command("language"))
async def language_command_handler(message: Message) -> None:
    uid = message.from_user.id
    lang = _get_lang(uid, message)
    await message.answer(t("choose_language", lang), reply_markup=_language_keyboard())


@dp.message(Command("reset"))
async def reset_command_handler(message: Message) -> None:
    uid = message.from_user.id
    prev = user_state.get(uid)
    lang = prev["language"] if prev else _detect_language(message.from_user.language_code)
    if prev and prev.get("session", {}).get("active"):
        _close_session(prev, uid)

    user_state[uid] = {
        "step": "awaiting_problem",
        "language": lang,
        "session": _new_session(),
    }
    log.info("[user:%d] RESET", uid)
    await message.answer(t("reset", lang), reply_markup=_problem_keyboard(lang))


@dp.message(Command("philosopher"))
async def philosopher_command_handler(message: Message) -> None:
    uid = message.from_user.id
    state = user_state.get(uid)
    lang = _get_lang(uid, message)

    if not state or not state.get("problem"):
        await message.answer(t("no_problem_yet", lang), reply_markup=ReplyKeyboardRemove())
        return

    state["step"] = "awaiting_philosopher"
    log.info("[user:%d] /philosopher — changing philosopher", uid)
    await message.answer(t("change_philosopher", lang), reply_markup=_philosopher_keyboard())


@dp.message(Command("stats"))
async def stats_command_handler(message: Message) -> None:
    if message.from_user.id != ADMIN_USER_ID:
        return

    events = ANALYTICS["events"]
    phil = ANALYTICS["selected_philosopher"]

    all_options: dict[str, int] = {}
    for lang_opts in ANALYTICS["selected_options_breakdown"].values():
        for text, count in lang_opts.items():
            all_options[text] = all_options.get(text, 0) + count
    top = sorted(all_options.items(), key=lambda x: x[1], reverse=True)[:5]

    top_lines = "\n".join(f"  {text}: {count}" for text, count in top)
    if not top_lines:
        top_lines = "  (no data yet)"

    depths = ANALYTICS["conversation_depth"]
    total_sessions = len(depths)
    avg_depth = round(sum(depths) / total_sessions, 1) if total_sessions else 0
    max_depth = max(depths) if depths else 0
    d1 = sum(1 for d in depths if d == 1)
    d2 = sum(1 for d in depths if d == 2)
    d3 = sum(1 for d in depths if d >= 3)

    report = (
        f"<b>Total users:</b> {get_total_users()}\n"
        f"\n"
        f"<b>Problem input:</b>\n"
        f"  Typed: {events['entered_text']}\n"
        f"  Selected: {events['selected_option']}\n"
        f"\n"
        f"<b>Philosophers:</b>\n"
        f"  Nietzsche: {phil['nietzsche']}\n"
        f"  Camus: {phil['camus']}\n"
        f"  Sartre: {phil['sartre']}\n"
        f"\n"
        f"<b>Conversation depth:</b>\n"
        f"  Avg: {avg_depth}\n"
        f"  Max: {max_depth}\n"
        f"  Sessions: {total_sessions}\n"
        f"\n"
        f"<b>Depth breakdown:</b>\n"
        f"  1 message: {d1}\n"
        f"  2 messages: {d2}\n"
        f"  3+ messages: {d3}\n"
        f"\n"
        f"<b>Top selected problems:</b>\n"
        f"{top_lines}"
    )
    await message.answer(report)


# ── text handler ───────────────────────────────────────────────────────

@dp.message()
async def text_handler(message: Message) -> None:
    if not message.text:
        return

    uid = message.from_user.id
    state = user_state.get(uid)
    text = message.text.strip()

    # ── language selection (ReplyKeyboard) ──
    if text in LANG_BUTTONS:
        lang = LANG_BUTTONS[text]
        if state:
            state["language"] = lang
        else:
            user_state[uid] = {
                "step": "awaiting_problem",
                "language": lang,
                "session": _new_session(),
            }
        log.info("[user:%d] language changed to %s", uid, lang)
        await message.answer(t("language_set", lang), reply_markup=ReplyKeyboardRemove())
        return

    # ── menu button shortcuts ──
    lang = _get_lang(uid, message)
    action = _match_menu_button(text, lang)
    if action == "reset":
        await reset_command_handler(message)
        return
    if action == "language":
        await language_command_handler(message)
        return
    if action == "philosopher":
        await philosopher_command_handler(message)
        return

    # ── awaiting problem ──
    if not state or state["step"] == "awaiting_problem":
        lang = state["language"] if state else _detect_language(message.from_user.language_code)
        predefined = TEXTS["problems"].get(lang, TEXTS["problems"]["en"])

        idk = t("idk_option", lang)
        if text == idk:
            ANALYTICS["events"]["selected_option"] += 1
            ANALYTICS["selected_options_breakdown"][lang][text] += 1
            user_state[uid] = {
                "step": "awaiting_clarification",
                "language": lang,
                "session": state["session"] if state else _new_session(),
            }
            _mark_user_activity(user_state[uid])
            log.info("[user:%d] SELECTED_OPTION: %s", uid, text)
            await message.answer(t("idk_followup", lang), reply_markup=ReplyKeyboardRemove())
            return

        if text in predefined:
            ANALYTICS["events"]["selected_option"] += 1
            ANALYTICS["selected_options_breakdown"][lang][text] += 1
            log.info("[user:%d] SELECTED_OPTION: %s", uid, text)
        else:
            ANALYTICS["events"]["entered_text"] += 1
            log.info("[user:%d] ENTERED_TEXT: %s", uid, text)

        user_state[uid] = {
            "step": "awaiting_philosopher",
            "problem": message.text,
            "language": lang,
            "session": state["session"] if state else _new_session(),
        }
        state = user_state[uid]
        _mark_user_activity(state)
        ANALYTICS["current_sessions"][uid] = 1
        await message.answer(t("choose_philosopher", lang), reply_markup=_philosopher_keyboard())
        return

    # ── awaiting clarification (after "I don't know") ──
    if state["step"] == "awaiting_clarification":
        ANALYTICS["events"]["entered_text"] += 1
        state["problem"] = message.text
        state["step"] = "awaiting_philosopher"
        _mark_user_activity(state)
        ANALYTICS["current_sessions"][uid] = 1
        log.info("[user:%d] ENTERED_TEXT: %s", uid, message.text)
        await message.answer(
            t("choose_philosopher", state["language"]),
            reply_markup=_philosopher_keyboard(),
        )
        return

    # ── awaiting philosopher ──
    if state["step"] == "awaiting_philosopher":
        philosopher = text
        if philosopher not in PHILOSOPHER_NAMES:
            await message.answer(
                t("pick_philosopher", state.get("language", "en")),
                reply_markup=_philosopher_keyboard(),
            )
            return

        ANALYTICS["selected_philosopher"][philosopher.lower()] += 1
        log.info("[user:%d] SELECTED_PHILOSOPHER: %s", uid, philosopher)

        state["philosopher"] = philosopher
        state["step"] = "conversation"
        state["history"] = [{"role": "user", "content": state["problem"]}]
        _mark_user_activity(state)

        await message.answer("✓", reply_markup=ReplyKeyboardRemove())
        await _send_typing_and_reply(message, state, message.bot)
        return

    # ── conversation ──
    if state["step"] == "conversation":
        _mark_user_activity(state)
        _append_history(state, "user", message.text)
        ANALYTICS["current_sessions"][uid] = ANALYTICS["current_sessions"].get(uid, 0) + 1
        log.info("[user:%d] message: %s", uid, message.text)
        await _send_typing_and_reply(message, state, message.bot)
        return


# ── reminder loop ──────────────────────────────────────────────────────

async def _reminder_loop(bot: Bot) -> None:
    while True:
        await asyncio.sleep(REMINDER_CHECK_INTERVAL)
        now = time()
        for uid, state in list(user_state.items()):
            session = state.get("session")
            if not session or not session["active"] or session["reminder_sent"]:
                continue
            last_reply = session["last_bot_reply_at"]
            last_user = session["last_user_msg_at"]
            if last_reply is None:
                continue
            if last_user and last_user >= last_reply:
                continue
            if now - last_reply >= INACTIVE_THRESHOLD:
                try:
                    lang = state.get("language", "en")
                    await bot.send_message(uid, t("reminder", lang))
                    session["reminder_sent"] = True
                    log.info("Reminder sent to user %d", uid)
                except Exception:
                    log.exception("Failed to send reminder to user %d", uid)


# ── bot commands menu ──────────────────────────────────────────────────

async def set_commands(bot: Bot) -> None:
    en_commands = [
        BotCommand(command="start", description="Start conversation"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="reset", description="Start over"),
        BotCommand(command="philosopher", description="Choose philosopher"),
        BotCommand(command="stats", description="Analytics (admin)"),
    ]
    ru_commands = [
        BotCommand(command="start", description="Начать диалог"),
        BotCommand(command="language", description="Сменить язык"),
        BotCommand(command="reset", description="Начать заново"),
        BotCommand(command="philosopher", description="Выбрать философа"),
        BotCommand(command="stats", description="Аналитика (админ)"),
    ]
    await bot.set_my_commands(en_commands, scope=BotCommandScopeDefault())
    await bot.set_my_commands(ru_commands, language_code="ru")


# ── entry point ────────────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    log.info("Starting bot...")
    try:
        bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await set_commands(bot)
        asyncio.create_task(_reminder_loop(bot))
        await dp.start_polling(bot)
    except Exception:
        log.exception("Bot crashed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
