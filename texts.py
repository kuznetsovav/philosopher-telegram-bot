TEXTS: dict[str, dict[str, str]] = {
    "start": {
        "en": (
            "What is bothering you right now?\n"
            "You can choose an option below or type your own.\n\n"
            "<i>Tip: type / to see available commands</i>"
        ),
        "ru": (
            "Что тебя сейчас больше всего мучает?\n"
            "Можешь выбрать вариант ниже или написать свой.\n\n"
            "<i>Подсказка: введи / чтобы увидеть команды</i>"
        ),
    },
    "menu_start_over": {
        "en": "Start over",
        "ru": "Начать заново",
    },
    "menu_change_lang": {
        "en": "Change language",
        "ru": "Сменить язык",
    },
    "menu_choose_phil": {
        "en": "Choose philosopher",
        "ru": "Выбрать философа",
    },
    "problems": {
        "en": [
            "I keep choosing comfort over what actually matters",
            "I said yes to a life I never wanted",
            "I'm pretending everything is fine and it's killing me",
            "I can't forgive someone and it's eating me alive",
            "I wasted years and can't get them back",
            "I don't know what's bothering me",
        ],
        "ru": [
            "Я раз за разом выбираю комфорт вместо того, что важно",
            "Я согласился на жизнь, которую не выбирал",
            "Я делаю вид, что всё нормально, и это меня разрушает",
            "Я не могу простить одного человека и это сжирает меня",
            "Я потратил годы впустую и не могу их вернуть",
            "Я не знаю, что меня мучает",
        ],
    },
    "idk_option": {
        "en": "I don't know what's bothering me",
        "ru": "Я не знаю, что меня мучает",
    },
    "idk_followup": {
        "en": "Alright. Then answer honestly: what have you been avoiding the most lately?",
        "ru": "Хорошо. Тогда ответь честно: что ты больше всего избегал в последнее время?",
    },
    "choose_philosopher": {
        "en": "Who do you want to respond?",
        "ru": "Кто ответит?",
    },
    "pick_philosopher": {
        "en": "Pick a philosopher from the buttons below.",
        "ru": "Выбери философа из кнопок ниже.",
    },
    "reminder": {
        "en": "We stopped at the most important part. Do you want to continue?",
        "ru": "Мы остановились на самом важном. Хочешь продолжить?",
    },
    "choose_language": {
        "en": "Choose your language",
        "ru": "Выбери язык",
    },
    "language_set": {
        "en": "Language set to English.",
        "ru": "Язык изменён на русский.",
    },
    "reset": {
        "en": "Let's start over. What is bothering you right now?",
        "ru": "Начнем сначала. Что тебя сейчас мучает?",
    },
    "change_philosopher": {
        "en": "Who do you want to respond now?",
        "ru": "Кто теперь ответит?",
    },
    "no_problem_yet": {
        "en": "Send /start first to describe your problem.",
        "ru": "Сначала отправь /start, чтобы описать проблему.",
    },
    "notif_ask_enable": {
        "en": "Do you want daily check-ins?",
        "ru": "Хочешь получать напоминания?",
    },
    "notif_btn_enable": {
        "en": "Enable",
        "ru": "Включить",
    },
    "notif_btn_cancel": {
        "en": "Cancel",
        "ru": "Отмена",
    },
    "notif_ask_days": {
        "en": "Choose days:",
        "ru": "Выбери дни:",
    },
    "notif_btn_weekdays": {
        "en": "Weekdays",
        "ru": "Будни",
    },
    "notif_btn_weekends": {
        "en": "Weekends",
        "ru": "Выходные",
    },
    "notif_btn_every_day": {
        "en": "Every day",
        "ru": "Каждый день",
    },
    "notif_ask_tz": {
        "en": "What's your timezone?",
        "ru": "Какой у тебя часовой пояс?",
    },
    "notif_ask_time": {
        "en": "Choose time (your local time):",
        "ru": "Выбери время (по твоему местному времени):",
    },
    "notif_btn_custom": {
        "en": "Custom",
        "ru": "Другое",
    },
    "notif_ask_custom_time": {
        "en": "Type time in HH:MM format (24h):",
        "ru": "Введи время в формате ЧЧ:ММ (24ч):",
    },
    "notif_invalid_time": {
        "en": "Invalid format. Please type time as HH:MM (e.g. 09:00 or 21:30).",
        "ru": "Неверный формат. Введи время как ЧЧ:ММ (например, 09:00 или 21:30).",
    },
    "notif_btn_turn_off": {
        "en": "Turn off",
        "ru": "Выключить",
    },
    "notif_btn_change_time": {
        "en": "Change time",
        "ru": "Изменить время",
    },
    "notif_btn_change_days": {
        "en": "Change days",
        "ru": "Изменить дни",
    },
    "notif_confirmed": {
        "en": "Notifications set: {days} at {time} ({tz}) ✓",
        "ru": "Уведомления настроены: {days}, {time} ({tz}) ✓",
    },
    "notif_disabled": {
        "en": "Notifications disabled",
        "ru": "Уведомления выключены",
    },
    "notif_cancelled": {
        "en": "OK, no notifications.",
        "ru": "Хорошо, без уведомлений.",
    },
    "notif_status": {
        "en": "Notifications are ON\nDays: {days}\nTime: {time} ({tz})",
        "ru": "Уведомления включены\nДни: {days}\nВремя: {time} ({tz})",
    },
    "notif_daily": {
        "en": "What is bothering you right now?",
        "ru": "Что тебя сейчас тревожит?",
    },
    "days_weekdays": {
        "en": "weekdays",
        "ru": "будни",
    },
    "days_weekends": {
        "en": "weekends",
        "ru": "выходные",
    },
    "days_every_day": {
        "en": "every day",
        "ru": "каждый день",
    },
}


def t(key: str, lang: str = "en", **kwargs: str) -> str:
    entry = TEXTS.get(key, {})
    text = entry.get(lang) or entry.get("en", key)
    if kwargs:
        text = text.format(**kwargs)
    return text
