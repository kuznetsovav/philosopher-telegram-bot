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
        "en": "Do you want to receive a daily check-in message?",
        "ru": "Хочешь получать ежедневное напоминание поговорить с философом?",
    },
    "notif_btn_enable": {
        "en": "Enable",
        "ru": "Включить",
    },
    "notif_btn_cancel": {
        "en": "Cancel",
        "ru": "Отмена",
    },
    "notif_ask_time": {
        "en": "When should I message you?",
        "ru": "Когда тебе удобнее?",
    },
    "notif_btn_morning": {
        "en": "Morning",
        "ru": "Утро",
    },
    "notif_btn_evening": {
        "en": "Evening",
        "ru": "Вечер",
    },
    "notif_btn_turn_off": {
        "en": "Turn off",
        "ru": "Выключить",
    },
    "notif_enabled": {
        "en": "Notifications enabled ✓",
        "ru": "Уведомления включены ✓",
    },
    "notif_disabled": {
        "en": "Notifications disabled",
        "ru": "Уведомления выключены",
    },
    "notif_cancelled": {
        "en": "OK, no notifications.",
        "ru": "Хорошо, без уведомлений.",
    },
    "notif_daily": {
        "en": "What is bothering you right now?",
        "ru": "Что тебя сейчас тревожит?",
    },
}


def t(key: str, lang: str = "en", **kwargs: str) -> str:
    entry = TEXTS.get(key, {})
    text = entry.get(lang) or entry.get("en", key)
    if kwargs:
        text = text.format(**kwargs)
    return text
