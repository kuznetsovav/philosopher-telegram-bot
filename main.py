from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from os import getenv
from pathlib import Path
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

from existentialism_full_text import EXISTENTIALISM_FULL_TEXT
from llm import ask_llm
from prompts import build_system_prompt_with_context
from texts import TEXTS, philosopher_intro, t

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

PHILOSOPHY_CATEGORIES: dict[str, dict] = {
    "existentialism": {
        "label": {"ru": "Экзистенциализм", "en": "Existentialism"},
        "blurb": {
            "ru": "Экзистенциализм — про выбор, свободу и ответственность.",
            "en": "Existentialism is about choice, freedom, and responsibility.",
        },
        "philosophers": ["sartre", "camus", "kierkegaard"],
    },
    "stoicism": {
        "label": {"ru": "Стоицизм", "en": "Stoicism"},
        "blurb": {
            "ru": "Стоицизм — про то, что от тебя зависит, и спокойствие там, где нет.",
            "en": "Stoicism is about what depends on you—and steady mind where it doesn't.",
        },
        "philosophers": ["marcus", "epictetus", "seneca"],
    },
    "nietzschean": {
        "label": {"ru": "Ницшеанство", "en": "Nietzschean"},
        "blurb": {
            "ru": "Ницшеанство — про силу, рост через трудности и правду без утешений.",
            "en": "Nietzschean is about strength, growing through difficulty, and truth without comfort.",
        },
        "philosophers": ["nietzsche"],
    },
    "buddhism": {
        "label": {"ru": "Буддизм", "en": "Buddhism"},
        "blurb": {
            "ru": "Буддизм — про страдание, привычки ума и более ясный взгляд.",
            "en": "Buddhism is about suffering, habits of mind, and seeing things more clearly.",
        },
        "philosophers": ["buddha"],
    },
    "pragmatism": {
        "label": {"ru": "Прагматизм", "en": "Pragmatism"},
        "blurb": {
            "ru": "Прагматизм — про то, что реально работает в жизни, а не красивые слова.",
            "en": "Pragmatism is about what actually works in life—not pretty words.",
        },
        "philosophers": ["william_james"],
    },
}
CATEGORY_ORDER = [
    "existentialism",
    "stoicism",
    "nietzschean",
    "buddhism",
    "pragmatism",
]
PHILOSOPHER_NAMES: dict[str, dict[str, str]] = {
    "nietzsche": {"ru": "Ницше", "en": "Nietzsche"},
    "sartre": {"ru": "Сартр", "en": "Sartre"},
    "camus": {"ru": "Камю", "en": "Camus"},
    "kierkegaard": {"ru": "Кьеркегор", "en": "Kierkegaard"},
    "marcus": {"ru": "Марк Аврелий", "en": "Marcus Aurelius"},
    "epictetus": {"ru": "Эпиктет", "en": "Epictetus"},
    "seneca": {"ru": "Сенека", "en": "Seneca"},
    "buddha": {"ru": "Будда", "en": "Buddha"},
    "william_james": {"ru": "Уильям Джеймс", "en": "William James"},
}


def get_philosopher_id_from_label(label: str, lang: str) -> str | None:
    for pid, names in PHILOSOPHER_NAMES.items():
        if names.get(lang) == label:
            return pid
    for pid, names in PHILOSOPHER_NAMES.items():
        for lg in ("en", "ru"):
            if names.get(lg) == label:
                return pid
    return None


def _canonical_philosopher_id(raw: str) -> str:
    if raw in PHILOSOPHER_NAMES:
        return raw
    pid = get_philosopher_id_from_label(raw, "en")
    if pid:
        return pid
    return get_philosopher_id_from_label(raw, "ru") or raw


def _localized_philosopher_label(philosopher_id: str, lang: str) -> str:
    pid = _canonical_philosopher_id(philosopher_id)
    row = PHILOSOPHER_NAMES.get(pid)
    if not row:
        return philosopher_id
    return row.get(lang) or row["en"]
LANG_BUTTONS = {"Русский": "ru", "English": "en"}

THINKING_DELAY = 1.5
MAX_HISTORY = 5
REMINDER_CHECK_INTERVAL = 3600
NOTIFICATION_CHECK_INTERVAL = 300
INACTIVE_THRESHOLD = 86400

FREE_DAILY_LIMIT = 20
MIN_INTERVAL_SECONDS = 2

# ── keyboards ──────────────────────────────────────────────────────────

def _problem_keyboard(lang: str) -> ReplyKeyboardMarkup:
    problems = TEXTS["problems"].get(lang, TEXTS["problems"]["en"])
    keyboard = [[KeyboardButton(text=p)] for p in problems]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _category_keyboard(lang: str) -> ReplyKeyboardMarkup:
    rows = []
    for cid in CATEGORY_ORDER:
        labels = PHILOSOPHY_CATEGORIES[cid]["label"]
        label = labels.get(lang) or labels["en"]
        rows.append([KeyboardButton(text=label)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _category_id_from_label(text: str, lang: str) -> str | None:
    for cid in CATEGORY_ORDER:
        labels = PHILOSOPHY_CATEGORIES[cid]["label"]
        if text == (labels.get(lang) or labels["en"]):
            return cid
    return None


def _category_blurb(category_id: str, lang: str) -> str:
    row = PHILOSOPHY_CATEGORIES[category_id]["blurb"]
    return row.get(lang) or row["en"]


def _philosopher_slugs_in_category(category_id: str) -> list[str]:
    return PHILOSOPHY_CATEGORIES[category_id]["philosophers"][:3]


def _philosopher_displays_in_category(category_id: str, lang: str) -> list[str]:
    return [_localized_philosopher_label(s, lang) for s in _philosopher_slugs_in_category(category_id)]


def _philosophers_in_category_keyboard(category_id: str, lang: str) -> ReplyKeyboardMarkup:
    names = _philosopher_displays_in_category(category_id, lang)
    keyboard = [[KeyboardButton(text=n) for n in names]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _resume_step_after_notif(state: dict) -> str:
    if state.get("philosopher"):
        return "conversation"
    if state.get("philosophy"):
        return "awaiting_philosopher_choice"
    if state.get("problem"):
        return "awaiting_philosophy_category"
    return "awaiting_problem"


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


WEEKDAYS = ["mon", "tue", "wed", "thu", "fri"]
WEEKENDS = ["sat", "sun"]
ALL_DAYS = WEEKDAYS + WEEKENDS
WEEKDAY_INDEX = {d: i for i, d in enumerate(ALL_DAYS)}

PRESET_TIMES = ["09:00", "13:00", "19:00"]
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
NOTIF_TIME_WINDOW = 30  # minutes


def _notif_enable_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [[
        KeyboardButton(text=t("notif_btn_enable", lang)),
        KeyboardButton(text=t("notif_btn_cancel", lang)),
    ]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _notif_days_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=t("notif_btn_weekdays", lang))],
        [KeyboardButton(text=t("notif_btn_weekends", lang))],
        [KeyboardButton(text=t("notif_btn_every_day", lang))],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _notif_time_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=h) for h in PRESET_TIMES],
        [KeyboardButton(text=t("notif_btn_custom", lang))],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def _notif_manage_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=t("notif_btn_change_days", lang)),
            KeyboardButton(text=t("notif_btn_change_time", lang)),
        ],
        [KeyboardButton(text=t("notif_btn_turn_off", lang))],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


UTC_OFFSETS = [
    ("UTC-8", -8), ("UTC-5", -5), ("UTC+0", 0),
    ("UTC+1", 1), ("UTC+2", 2), ("UTC+3", 3),
    ("UTC+4", 4), ("UTC+5", 5), ("UTC+8", 8),
    ("UTC+9", 9), ("UTC+10", 10),
]
UTC_OFFSET_MAP = {label: offset for label, offset in UTC_OFFSETS}


def _tz_keyboard() -> ReplyKeyboardMarkup:
    rows = []
    for i in range(0, len(UTC_OFFSETS), 3):
        chunk = UTC_OFFSETS[i:i + 3]
        rows.append([KeyboardButton(text=label) for label, _ in chunk])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def _tz_label(offset: int) -> str:
    if offset >= 0:
        return f"UTC+{offset}"
    return f"UTC{offset}"


NOTIF_BTN_KEYS = (
    "notif_btn_enable", "notif_btn_cancel",
    "notif_btn_weekdays", "notif_btn_weekends", "notif_btn_every_day",
    "notif_btn_custom", "notif_btn_turn_off",
    "notif_btn_change_days", "notif_btn_change_time",
)


def _match_notif_button(text: str, lang: str) -> str | None:
    for key in NOTIF_BTN_KEYS:
        if text == t(key, lang):
            return key
    return None


def _days_label(days: list[str], lang: str) -> str:
    s = set(days)
    if s == set(ALL_DAYS):
        return t("days_every_day", lang)
    if s == set(WEEKDAYS):
        return t("days_weekdays", lang)
    if s == set(WEEKENDS):
        return t("days_weekends", lang)
    return ", ".join(sorted(days, key=lambda d: WEEKDAY_INDEX.get(d, 99)))


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


_AGREEMENT_SIGNALS_EN = (
    "you're right", "you are right", "i agree", "makes sense", "true",
)
_AGREEMENT_SIGNALS_RU = (
    "ты прав", "согласен", "согласна", "да, это так", "имеет смысл",
)


_UNCERTAIN_EN = ("i don't know", "not sure", "no idea")
_UNCERTAIN_RU = ("не знаю", "не уверен", "не уверена")

_CONFUSED_EN = ("i don't understand", "what do you mean", "not clear")
_CONFUSED_RU = ("не понимаю", "что ты имеешь в виду", "не ясно")

_HELP_EN = (
    "help me",
    "i don't know what to do",
    "can you suggest",
    "what should i do",
)
_HELP_RU = (
    "помоги",
    "не знаю что делать",
    "подскажи",
    "что мне делать",
)


def is_confused_answer(text: str) -> bool:
    s = text.strip().lower()
    for ch in ("\u2019", "\u2018", "`"):
        s = s.replace(ch, "'")
    for phrase in _CONFUSED_EN:
        if phrase in s:
            return True
    for phrase in _CONFUSED_RU:
        if phrase in s:
            return True
    return False


def is_uncertain_answer(text: str) -> bool:
    s = text.strip().lower()
    for ch in ("\u2019", "\u2018", "`"):
        s = s.replace(ch, "'")
    for phrase in _UNCERTAIN_EN:
        if phrase in s:
            return True
    for phrase in _UNCERTAIN_RU:
        if phrase in s:
            return True
    return False


def is_help_request(text: str) -> bool:
    s = text.strip().lower()
    for ch in ("\u2019", "\u2018", "`"):
        s = s.replace(ch, "'")
    for phrase in _HELP_EN:
        if phrase in s:
            return True
    for phrase in _HELP_RU:
        if phrase in s:
            return True
    return False


def _latest_user_text_from_history(history: list) -> str:
    for m in reversed(history):
        if m.get("role") == "user":
            return (m.get("content") or "").strip()
    return ""


def detect_agreement(user_message: str) -> bool:
    s = user_message.strip().lower()
    for ch in ("\u2019", "\u2018", "`"):
        s = s.replace(ch, "'")
    for sig in _AGREEMENT_SIGNALS_EN:
        if sig in s:
            return True
    for sig in _AGREEMENT_SIGNALS_RU:
        if sig in s:
            return True
    return False


def _is_short_reply_for_closure(user_message: str) -> bool:
    s = user_message.strip()
    if not s:
        return False
    if len(s) <= 24:
        return True
    return len(s.split()) <= 4


def _update_conversation_phase(state: dict, user_message: str) -> None:
    phase = state.get("conversation_phase", "challenge")
    if phase == "challenge":
        if detect_agreement(user_message):
            state["conversation_phase"] = "reflection"
            state["closure_prompt_shown"] = False
        return
    if phase == "reflection":
        if detect_agreement(user_message) or _is_short_reply_for_closure(user_message):
            state["conversation_phase"] = "closure"
            state["closure_prompt_shown"] = False
        return


_USAGE_KEYS = ("daily_requests", "last_request_time", "last_reset_date")


def _default_usage() -> dict:
    return {
        "daily_requests": 0,
        "last_request_time": None,
        "last_reset_date": None,
    }


def _ensure_usage_fields(state: dict) -> None:
    d = _default_usage()
    for k, v in d.items():
        state.setdefault(k, v)


def reset_daily_usage(state: dict) -> None:
    _ensure_usage_fields(state)
    today = datetime.now(timezone.utc).date()
    last = state.get("last_reset_date")
    if last != today:
        state["daily_requests"] = 0
        state["last_reset_date"] = today


def is_rate_limited(state: dict) -> bool:
    _ensure_usage_fields(state)
    last = state.get("last_request_time")
    if last is None:
        return False
    return (time() - last) < MIN_INTERVAL_SECONDS


def is_daily_limit_reached(state: dict) -> bool:
    _ensure_usage_fields(state)
    return state["daily_requests"] >= FREE_DAILY_LIMIT


def register_request(state: dict) -> None:
    _ensure_usage_fields(state)
    state["daily_requests"] = state["daily_requests"] + 1
    state["last_request_time"] = time()


async def _handle_conversation_turn(message: Message, state: dict, uid: int) -> None:
    """Continue dialogue with the current philosopher (same as conversation branch)."""
    if state.get("philosopher"):
        canon = _canonical_philosopher_id(state["philosopher"])
        if canon in PHILOSOPHER_NAMES:
            state["philosopher"] = canon
    state.setdefault("history", [])
    _mark_user_activity(state)
    if not await _check_llm_limits(message, state, uid):
        return
    state.setdefault("conversation_phase", "challenge")
    state.setdefault("closure_prompt_shown", False)
    _update_conversation_phase(state, message.text)
    utext = message.text.strip()
    if is_help_request(utext):
        state["conversation_phase"] = "help"
        state["consecutive_uncertain_count"] = 0
    elif is_uncertain_answer(utext):
        n = state.get("consecutive_uncertain_count", 0) + 1
        state["consecutive_uncertain_count"] = n
        if n >= 2:
            state["conversation_phase"] = "help"
    else:
        state["consecutive_uncertain_count"] = 0
    _append_history(state, "user", message.text)
    ANALYTICS["current_sessions"][uid] = ANALYTICS["current_sessions"].get(uid, 0) + 1
    log.info("[user:%d] message: %s", uid, message.text)
    await _send_typing_and_reply(message, state, message.bot)


async def _check_llm_limits(message: Message, state: dict, uid: int) -> bool:
    reset_daily_usage(state)
    lang = state.get("language", "en")
    if is_rate_limited(state):
        log.info("[user:%d] RATE_LIMIT", uid)
        await message.answer(t("rate_limit", lang))
        return False
    if is_daily_limit_reached(state):
        log.info("[user:%d] DAILY_LIMIT", uid)
        await message.answer(t("daily_limit", lang))
        return False
    return True


async def _send_typing_and_reply(message: Message, state: dict, bot: Bot) -> None:
    lang = state.get("language", "en")
    phase = state.get("conversation_phase", "challenge")
    history = state.get("history") or []
    latest_user = _latest_user_text_from_history(history)
    confused = is_confused_answer(latest_user)
    uncertain = is_uncertain_answer(latest_user)
    canon = _canonical_philosopher_id(state["philosopher"])
    if canon in PHILOSOPHER_NAMES:
        state["philosopher"] = canon
    phil_id = state["philosopher"]
    phil_label = _localized_philosopher_label(phil_id, lang)

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    if phase == "help":
        system_prompt = build_system_prompt_with_context(
            phil_id,
            lang,
            "help",
            state.get("problem") or "",
        )
        reply = await ask_llm(system_prompt, state["history"])
        register_request(state)
        await asyncio.sleep(THINKING_DELAY)
        _append_history(state, "assistant", reply)
        _mark_bot_reply(state)
        state["conversation_phase"] = "reflection"
        state["consecutive_uncertain_count"] = 0
        log.info(
            "[user:%d] %s HELP_MODE reply (turn %d): %s",
            message.chat.id, phil_id,
            state["session"]["turns"], reply[:120],
        )
    elif confused:
        system_prompt = build_system_prompt_with_context(
            phil_id,
            lang,
            phase,
            state.get("problem") or "",
            confused=True,
        )
        reply = await ask_llm(system_prompt, state["history"])
        register_request(state)
        await asyncio.sleep(THINKING_DELAY)
        _append_history(state, "assistant", reply)
        _mark_bot_reply(state)
        log.info(
            "[user:%d] %s confused reply (turn %d, phase=%s): %s",
            message.chat.id, phil_id,
            state["session"]["turns"], phase, reply[:120],
        )
    elif uncertain:
        system_prompt = build_system_prompt_with_context(
            phil_id,
            lang,
            phase,
            state.get("problem") or "",
            uncertain=True,
        )
        reply = await ask_llm(system_prompt, state["history"])
        register_request(state)
        await asyncio.sleep(THINKING_DELAY)
        _append_history(state, "assistant", reply)
        _mark_bot_reply(state)
        log.info(
            "[user:%d] %s uncertain reply (turn %d, phase=%s): %s",
            message.chat.id, phil_id,
            state["session"]["turns"], phase, reply[:120],
        )
    else:
        system_prompt = build_system_prompt_with_context(
            phil_id,
            lang,
            phase,
            state.get("problem") or "",
        )
        reply = await ask_llm(system_prompt, state["history"])
        register_request(state)
        await asyncio.sleep(THINKING_DELAY)
        _append_history(state, "assistant", reply)
        _mark_bot_reply(state)
        log.info(
            "[user:%d] %s reply (turn %d, phase=%s): %s",
            message.chat.id, phil_id,
            state["session"]["turns"], phase, reply[:120],
        )
    if state.pop("lead_reply_separator", False):
        body = f"<b>{phil_label}</b>\n\n—\n\n{reply}"
    else:
        body = f"<b>{phil_label}</b>\n\n{reply}"
    await message.answer(
        body,
        reply_markup=_menu_keyboard(lang),
    )
    if phase == "closure" and not state.get("closure_prompt_shown"):
        await message.answer(t("closure_continue_prompt", lang))
        state["closure_prompt_shown"] = True


# ── commands ───────────────────────────────────────────────────────────

_PREF_KEYS = (
    "notifications_enabled", "notification_days",
    "notification_time", "utc_offset", "last_notification_sent",
)

_NOTIF_FILE = Path(__file__).parent / "notification_prefs.json"
_PERSIST_KEYS = ("notifications_enabled", "notification_days", "notification_time", "utc_offset", "language")


def _save_notif_prefs() -> None:
    data = {}
    for uid, state in user_state.items():
        if state.get("notifications_enabled"):
            entry = {k: state[k] for k in _PERSIST_KEYS if k in state}
            last = state.get("last_notification_sent")
            if last:
                entry["last_notification_sent"] = last.isoformat()
            data[str(uid)] = entry
    try:
        _NOTIF_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        log.exception("Failed to save notification prefs")


def _load_notif_prefs() -> None:
    if not _NOTIF_FILE.exists():
        return
    try:
        data = json.loads(_NOTIF_FILE.read_text())
    except Exception:
        log.exception("Failed to load notification prefs")
        return
    for uid_str, prefs in data.items():
        uid = int(uid_str)
        if uid not in user_state:
            user_state[uid] = {
                "step": "awaiting_problem",
                "language": prefs.get("language", "en"),
                "session": _new_session(),
                **_default_usage(),
            }
        last_str = prefs.pop("last_notification_sent", None)
        if last_str:
            try:
                prefs["last_notification_sent"] = datetime.fromisoformat(last_str)
            except (ValueError, TypeError):
                pass
        user_state[uid].update(prefs)
    log.info("Loaded notification prefs for %d user(s)", len(data))


def _carry_prefs(prev: dict | None) -> dict:
    """Extract persistent preferences from a previous state."""
    if not prev:
        return {}
    return {k: prev[k] for k in _PREF_KEYS if k in prev}


def _carry_usage(prev: dict | None) -> dict:
    if not prev:
        return _default_usage()
    out = _default_usage()
    for k in _USAGE_KEYS:
        if k in prev:
            out[k] = prev[k]
    return out


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
        **_carry_prefs(prev),
        **_carry_usage(prev),
    }
    log.info("[user:%d] START (lang=%s, total_users=%d)", uid, lang, get_total_users())
    await message.answer(t("start", lang), reply_markup=_problem_keyboard(lang))


@dp.message(Command("existentialism"))
async def existentialism_command_handler(message: Message) -> None:
    """Send the full verbatim existentialism reference (RU)."""
    uid = message.from_user.id
    lang = _get_lang(uid, message)
    body = EXISTENTIALISM_FULL_TEXT.get(lang) or EXISTENTIALISM_FULL_TEXT["ru"]
    log.info("[user:%d] EXISTENTIALISM_FULL_TEXT", uid)
    await message.answer(body)


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
        **_carry_prefs(prev),
        **_carry_usage(prev),
    }
    log.info("[user:%d] RESET", uid)
    await message.answer(t("reset", lang), reply_markup=_problem_keyboard(lang))


def _wipe_conversation_state(state: dict, uid: int) -> None:
    """Remove all in-bot conversation context for this user (prefs and usage unchanged)."""
    if state.get("session", {}).get("active"):
        _close_session(state, uid)
    # Stale counter from problem/category flow before session was "active"
    ANALYTICS["current_sessions"].pop(uid, None)

    state["session"] = _new_session()
    state["step"] = "awaiting_problem"
    state["problem"] = None
    state["philosophy"] = None
    state["philosopher"] = None
    state["history"] = []
    state["conversation_phase"] = "challenge"
    state["consecutive_uncertain_count"] = 0
    state["closure_prompt_shown"] = False
    for k in ("lead_reply_separator", "_last_confusion_template", "_last_uncertainty_template"):
        state.pop(k, None)
    # Drop any other underscore-prefixed conversation scratch (future-safe)
    for k in list(state.keys()):
        if k.startswith("_"):
            state.pop(k, None)


@dp.message(Command("clear"))
async def clear_command_handler(message: Message) -> None:
    uid = message.from_user.id
    state = user_state.get(uid)
    lang = _get_lang(uid, message)

    if not state:
        user_state[uid] = {
            "step": "awaiting_problem",
            "language": lang,
            "session": _new_session(),
            "history": [],
            **_default_usage(),
        }
        ANALYTICS["current_sessions"].pop(uid, None)
    else:
        _wipe_conversation_state(state, uid)

    log.info("[user:%d] CLEAR_HISTORY", uid)
    await message.answer(t("clear_history", lang), reply_markup=_problem_keyboard(lang))


@dp.message(Command("philosopher"))
async def philosopher_command_handler(message: Message) -> None:
    uid = message.from_user.id
    state = user_state.get(uid)
    lang = _get_lang(uid, message)

    if not state or not state.get("problem"):
        await message.answer(t("no_problem_yet", lang), reply_markup=ReplyKeyboardRemove())
        return

    state.pop("philosophy", None)
    state.pop("philosopher", None)
    state["step"] = "awaiting_philosophy_category"
    log.info("[user:%d] /philosopher — changing philosopher (category flow)", uid)
    await message.answer(
        f"{t('change_philosopher', lang)}\n\n{t('ask_philosophy_approach', lang)}",
        reply_markup=_category_keyboard(lang),
    )


@dp.message(Command("notifications"))
async def notifications_command_handler(message: Message) -> None:
    uid = message.from_user.id
    state = user_state.get(uid)
    lang = _get_lang(uid, message)

    if not state:
        user_state[uid] = {
            "step": "awaiting_problem",
            "language": lang,
            "session": _new_session(),
            **_default_usage(),
        }
        state = user_state[uid]

    if state.get("notifications_enabled"):
        days = state.get("notification_days", [])
        ntime = state.get("notification_time", "—")
        tz = _tz_label(state.get("utc_offset", 0))
        status = t("notif_status", lang, days=_days_label(days, lang), time=ntime, tz=tz)
        state["step"] = "notif_managing"
        await message.answer(status, reply_markup=_notif_manage_keyboard(lang))
    else:
        state["step"] = "notif_enabling"
        await message.answer(t("notif_ask_enable", lang), reply_markup=_notif_enable_keyboard(lang))


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

    phil_lines = "\n".join(
        f"  {name}: {phil[name]}"
        for name in sorted(phil.keys(), key=lambda k: (-phil[k], k))
    )
    if not phil_lines:
        phil_lines = "  (no data yet)"

    report = (
        f"<b>Total users:</b> {get_total_users()}\n"
        f"\n"
        f"<b>Problem input:</b>\n"
        f"  Typed: {events['entered_text']}\n"
        f"  Selected: {events['selected_option']}\n"
        f"\n"
        f"<b>Philosophers:</b>\n"
        f"{phil_lines}\n"
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
                **_default_usage(),
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

    # ── notification buttons & input ──
    notif_btn = _match_notif_button(text, lang)
    if notif_btn and state:
        _prev_step = _resume_step_after_notif(state)

        if notif_btn == "notif_btn_enable":
            state["step"] = "notif_choosing_days"
            await message.answer(t("notif_ask_days", lang), reply_markup=_notif_days_keyboard(lang))
            return
        if notif_btn == "notif_btn_cancel":
            state["step"] = _prev_step
            await message.answer(t("notif_cancelled", lang), reply_markup=ReplyKeyboardRemove())
            return
        if notif_btn in ("notif_btn_weekdays", "notif_btn_weekends", "notif_btn_every_day"):
            day_map = {
                "notif_btn_weekdays": WEEKDAYS,
                "notif_btn_weekends": WEEKENDS,
                "notif_btn_every_day": ALL_DAYS,
            }
            state["notification_days"] = list(day_map[notif_btn])
            state["step"] = "notif_choosing_tz"
            await message.answer(t("notif_ask_tz", lang), reply_markup=_tz_keyboard())
            return
        if notif_btn == "notif_btn_custom":
            state["step"] = "notif_custom_time"
            await message.answer(t("notif_ask_custom_time", lang), reply_markup=ReplyKeyboardRemove())
            return
        if notif_btn == "notif_btn_turn_off":
            state["notifications_enabled"] = False
            state["notification_days"] = []
            state["notification_time"] = None
            state["step"] = _prev_step
            _save_notif_prefs()
            log.info("[user:%d] notifications OFF", uid)
            await message.answer(t("notif_disabled", lang), reply_markup=ReplyKeyboardRemove())
            return
        if notif_btn == "notif_btn_change_days":
            state["step"] = "notif_choosing_days"
            await message.answer(t("notif_ask_days", lang), reply_markup=_notif_days_keyboard(lang))
            return
        if notif_btn == "notif_btn_change_time":
            state["step"] = "notif_choosing_time"
            await message.answer(t("notif_ask_time", lang), reply_markup=_notif_time_keyboard(lang))
            return

    # ── timezone selection ──
    if state and state.get("step") == "notif_choosing_tz" and text in UTC_OFFSET_MAP:
        state["utc_offset"] = UTC_OFFSET_MAP[text]
        state["step"] = "notif_choosing_time"
        await message.answer(t("notif_ask_time", lang), reply_markup=_notif_time_keyboard(lang))
        return

    # ── preset time selection ──
    if state and state.get("step") == "notif_choosing_time" and text in PRESET_TIMES:
        state["notification_time"] = text
        state["notifications_enabled"] = True
        days = state.get("notification_days", [])
        tz = _tz_label(state.get("utc_offset", 0))
        state["step"] = _resume_step_after_notif(state)
        _save_notif_prefs()
        log.info("[user:%d] notifications ON (%s, %s, %s)", uid, _days_label(days, lang), text, tz)
        await message.answer(
            t("notif_confirmed", lang, days=_days_label(days, lang), time=text, tz=tz),
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # ── custom time input ──
    if state and state.get("step") == "notif_custom_time":
        if TIME_RE.match(text):
            state["notification_time"] = text
            state["notifications_enabled"] = True
            days = state.get("notification_days", [])
            tz = _tz_label(state.get("utc_offset", 0))
            state["step"] = _resume_step_after_notif(state)
            _save_notif_prefs()
            log.info("[user:%d] notifications ON (%s, %s, %s)", uid, _days_label(days, lang), text, tz)
            await message.answer(
                t("notif_confirmed", lang, days=_days_label(days, lang), time=text, tz=tz),
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            await message.answer(t("notif_invalid_time", lang))
        return

    # ── catch-all for notification steps (prevents silent freeze) ──
    _NOTIF_STEPS = {
        "notif_enabling": lambda l: _notif_enable_keyboard(l),
        "notif_choosing_days": lambda l: _notif_days_keyboard(l),
        "notif_choosing_tz": lambda l: _tz_keyboard(),
        "notif_choosing_time": lambda l: _notif_time_keyboard(l),
        "notif_managing": lambda l: _notif_manage_keyboard(l),
    }
    if state and state.get("step") in _NOTIF_STEPS:
        kb_fn = _NOTIF_STEPS[state["step"]]
        log.warning(
            "[user:%d] unmatched input %r at step %s",
            uid, text, state["step"],
        )
        await message.answer(
            t("notif_ask_enable", lang) if state["step"] == "notif_enabling"
            else t("notif_ask_days", lang) if state["step"] == "notif_choosing_days"
            else t("notif_ask_tz", lang) if state["step"] == "notif_choosing_tz"
            else t("notif_ask_time", lang) if state["step"] == "notif_choosing_time"
            else t("notif_ask_enable", lang),
            reply_markup=kb_fn(lang),
        )
        return

    # ── repair stale step: never restart problem flow while a chat is active ──
    if (
        state
        and state.get("step") == "awaiting_problem"
        and state.get("philosopher")
        and state.get("history")
    ):
        state["step"] = "conversation"
    if (
        state
        and state.get("step") in ("awaiting_philosophy_category", "awaiting_philosopher_choice")
        and state.get("philosopher")
        and state.get("history")
    ):
        state["step"] = "conversation"

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
                **_carry_prefs(state),
                **_carry_usage(state),
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
            "step": "awaiting_philosophy_category",
            "problem": message.text,
            "language": lang,
            "session": state["session"] if state else _new_session(),
            **_carry_prefs(state),
            **_carry_usage(state),
        }
        state = user_state[uid]
        _mark_user_activity(state)
        ANALYTICS["current_sessions"][uid] = 1
        await message.answer(t("ask_philosophy_approach", lang), reply_markup=_category_keyboard(lang))
        return

    # ── awaiting clarification (after "I don't know") ──
    if state["step"] == "awaiting_clarification":
        ANALYTICS["events"]["entered_text"] += 1
        state["problem"] = message.text
        state["step"] = "awaiting_philosophy_category"
        _mark_user_activity(state)
        ANALYTICS["current_sessions"][uid] = 1
        log.info("[user:%d] ENTERED_TEXT: %s", uid, message.text)
        await message.answer(
            t("ask_philosophy_approach", state["language"]),
            reply_markup=_category_keyboard(state["language"]),
        )
        return

    # ── philosophy category (mindset) ──
    if state["step"] == "awaiting_philosophy_category":
        cid = _category_id_from_label(text, lang)
        if not cid:
            log.warning(
                "[user:%d] unmatched philosophy category %r at step %s",
                uid, text, state["step"],
            )
            await message.answer(
                t("ask_philosophy_approach", lang),
                reply_markup=_category_keyboard(lang),
            )
            return
        state["philosophy"] = cid
        state["step"] = "awaiting_philosopher_choice"
        _mark_user_activity(state)
        log.info("[user:%d] SELECTED_PHILOSOPHY: %s", uid, cid)
        blurb = _category_blurb(cid, lang)
        follow = t("choose_philosopher_in_category", lang)
        await message.answer(
            f"{blurb}\n\n{follow}",
            reply_markup=_philosophers_in_category_keyboard(cid, lang),
        )
        return

    # ── philosopher within category (voice) ──
    if state["step"] == "awaiting_philosopher_choice":
        category_id = state.get("philosophy")
        allowed_slugs = _philosopher_slugs_in_category(category_id) if category_id else []
        pid = get_philosopher_id_from_label(text, lang)
        if not pid or pid not in allowed_slugs:
            ulang = state.get("language", "en")
            await message.answer(
                t("pick_philosopher", ulang),
                reply_markup=_philosophers_in_category_keyboard(category_id, ulang)
                if category_id
                else _category_keyboard(lang),
            )
            return

        if not await _check_llm_limits(message, state, uid):
            return

        ANALYTICS["selected_philosopher"][pid] += 1
        log.info("[user:%d] SELECTED_PHILOSOPHER: %s", uid, pid)

        state["philosopher"] = pid
        state["step"] = "conversation"
        state["conversation_phase"] = "challenge"
        state["consecutive_uncertain_count"] = 0
        state["closure_prompt_shown"] = False
        state["history"] = [{"role": "user", "content": state["problem"]}]
        _mark_user_activity(state)

        lang = state.get("language", "en")
        chosen_name = _localized_philosopher_label(pid, lang)
        await message.answer(
            f"✓\n\n{t('philosopher_chosen', lang, name=chosen_name)}",
            reply_markup=ReplyKeyboardRemove(),
        )
        intro = philosopher_intro(pid, lang)
        if intro:
            await message.answer(intro)
            state["lead_reply_separator"] = True
        await _send_typing_and_reply(message, state, message.bot)
        return

    # ── conversation ──
    if state["step"] == "conversation":
        await _handle_conversation_turn(message, state, uid)
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


# ── daily notification loop ────────────────────────────────────────────

_WEEKDAY_ABBR = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _current_day_abbr(now: datetime) -> str:
    return _WEEKDAY_ABBR[now.weekday()]


def should_send_notification(state: dict, now_utc: datetime) -> bool:
    if not state.get("notifications_enabled"):
        return False
    days = state.get("notification_days")
    ntime = state.get("notification_time")
    if not days or not ntime:
        return False

    offset_hours = state.get("utc_offset", 0)
    local_now = now_utc + timedelta(hours=offset_hours)

    if _current_day_abbr(local_now) not in days:
        return False

    m = TIME_RE.match(ntime)
    if not m:
        return False
    target_min = int(m.group(1)) * 60 + int(m.group(2))
    current_min = local_now.hour * 60 + local_now.minute
    diff = abs(current_min - target_min)
    if diff > NOTIF_TIME_WINDOW:
        return False

    last_sent = state.get("last_notification_sent")
    if last_sent and last_sent.date() == local_now.date():
        return False

    return True


def get_notification_text(state: dict) -> str:
    return t("notif_daily", state.get("language", "en"))


async def _notification_loop(bot: Bot) -> None:
    first_run = True
    while True:
        try:
            if first_run:
                await asyncio.sleep(10)
                first_run = False
            else:
                await asyncio.sleep(NOTIFICATION_CHECK_INTERVAL)
            now_utc = datetime.now(timezone.utc)
            for uid, state in list(user_state.items()):
                if not should_send_notification(state, now_utc):
                    continue
                try:
                    await bot.send_message(uid, get_notification_text(state))
                    state["last_notification_sent"] = now_utc
                    _save_notif_prefs()
                    log.info("Daily notification sent to user %d", uid)
                except Exception:
                    log.exception("Failed to send notification to user %d", uid)
        except Exception:
            log.exception("Notification loop error")


# ── bot commands menu ──────────────────────────────────────────────────

async def set_commands(bot: Bot) -> None:
    en_commands = [
        BotCommand(command="start", description="Start conversation"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="reset", description="Start over"),
        BotCommand(command="clear", description="Clear conversation history"),
        BotCommand(command="existentialism", description="Full existentialism text (RU)"),
        BotCommand(command="philosopher", description="Choose philosopher"),
        BotCommand(command="notifications", description="Daily notifications"),
        BotCommand(command="stats", description="Analytics (admin)"),
    ]
    ru_commands = [
        BotCommand(command="start", description="Начать диалог"),
        BotCommand(command="language", description="Сменить язык"),
        BotCommand(command="reset", description="Начать заново"),
        BotCommand(command="clear", description="Очистить историю диалога"),
        BotCommand(command="existentialism", description="Полный текст об экзистенциализме"),
        BotCommand(command="philosopher", description="Выбрать философа"),
        BotCommand(command="notifications", description="Ежедневные уведомления"),
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
    _load_notif_prefs()
    try:
        bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await set_commands(bot)
        asyncio.create_task(_reminder_loop(bot))
        asyncio.create_task(_notification_loop(bot))
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
