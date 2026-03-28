from __future__ import annotations

import asyncio
import logging
import sys
from collections import defaultdict
from os import getenv
from time import time

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

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

THINKING_DELAY = 1.5  # seconds — brief pause before the LLM reply lands
SUPPORTED_LANGUAGES = {"ru"}


def _detect_language(language_code: str | None) -> str:
    if language_code and language_code.lower().startswith("ru"):
        return "ru"
    return "en"


def _language_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="English", callback_data="lang:en"),
    )
    return kb


def _problem_keyboard(lang: str) -> ReplyKeyboardMarkup:
    problems = TEXTS["problems"].get(lang, TEXTS["problems"]["en"])
    keyboard = [[KeyboardButton(text=p)] for p in problems]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


PHILOSOPHER_NAMES = list(PHILOSOPHERS.values())


def _philosopher_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=name) for name in PHILOSOPHER_NAMES]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )

MAX_HISTORY = 5
REMINDER_CHECK_INTERVAL = 3600  # seconds (1 hour)
INACTIVE_THRESHOLD = 86400      # seconds (24 hours)


# user_id -> {"step", "problem", "philosopher", "history", "session"}
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


async def _send_typing_and_reply(
    message: Message, state: dict, bot: Bot,
) -> None:
    """Show typing indicator, call LLM, and send the formatted reply."""
    system_prompt = get_prompt(state["philosopher"], state.get("language", "en"))
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    reply = await ask_llm(system_prompt, state["history"])
    await asyncio.sleep(THINKING_DELAY)
    _append_history(state, "assistant", reply)
    _mark_bot_reply(state)
    log.info(
        "[user:%d] %s reply (turn %d): %s",
        message.chat.id,
        state["philosopher"],
        state["session"]["turns"],
        reply[:120],
    )
    formatted = f"<b>{state['philosopher']}</b>\n\n{reply}"
    await message.answer(formatted)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    uid = message.from_user.id
    prev = user_state.get(uid)
    if prev and prev.get("session", {}).get("active"):
        _close_session(prev, uid)
    ANALYTICS["users"].add(uid)
    ANALYTICS["events"]["start"] += 1

    lang = _detect_language(message.from_user.language_code)
    user_state[uid] = {
        "step": "awaiting_problem",
        "language": lang,
        "session": _new_session(),
    }
    log.info("[user:%d] START (lang=%s, total_users=%d)", uid, lang, get_total_users())
    await message.answer(
        t("start", lang),
        reply_markup=_problem_keyboard(lang),
    )


@dp.message(Command("language"))
async def language_command_handler(message: Message) -> None:
    uid = message.from_user.id
    state = user_state.get(uid)
    lang = state["language"] if state else _detect_language(message.from_user.language_code)
    await message.answer(
        t("choose_language", lang),
        reply_markup=_language_keyboard().as_markup(),
    )


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


@dp.callback_query(F.data.startswith("lang:"))
async def language_chosen(callback: CallbackQuery) -> None:
    lang = callback.data.split(":")[1]
    if lang not in ("ru", "en"):
        await callback.answer()
        return

    uid = callback.from_user.id
    state = user_state.get(uid)
    if state:
        state["language"] = lang
    else:
        user_state[uid] = {
            "step": "awaiting_problem",
            "language": lang,
            "session": _new_session(),
        }

    await callback.answer()
    await callback.message.edit_text(t("language_set", lang))
    log.info("[user:%d] language changed to %s", uid, lang)


@dp.message()
async def text_handler(message: Message) -> None:
    if not message.text:
        return

    uid = message.from_user.id
    state = user_state.get(uid)

    if not state or state["step"] == "awaiting_problem":
        lang = state["language"] if state else _detect_language(message.from_user.language_code)
        predefined = TEXTS["problems"].get(lang, TEXTS["problems"]["en"])
        text = message.text.strip()

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
            await message.answer(
                t("idk_followup", lang),
                reply_markup=ReplyKeyboardRemove(),
            )
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
        await message.answer(
            t("choose_philosopher", state["language"]),
            reply_markup=_philosopher_keyboard(),
        )
        return

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

    if state["step"] == "awaiting_philosopher":
        philosopher = message.text.strip()
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

    if state["step"] == "conversation":
        _mark_user_activity(state)
        _append_history(state, "user", message.text)
        ANALYTICS["current_sessions"][uid] = ANALYTICS["current_sessions"].get(uid, 0) + 1
        log.info("[user:%d] message: %s", uid, message.text)
        await _send_typing_and_reply(message, state, message.bot)
        return


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
            # Only remind when bot replied more recently than the user
            if last_user and last_user >= last_reply:
                continue
            if now - last_reply >= INACTIVE_THRESHOLD:
                try:
                    lang = state.get("language", "en")
                    await bot.send_message(uid, t("reminder", lang))
                    session["reminder_sent"] = True
                    logging.info("Reminder sent to user %d", uid)
                except Exception:
                    logging.exception("Failed to send reminder to user %d", uid)


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
