TEXTS: dict[str, dict[str, str]] = {
    "start": {
        "en": "What is bothering you right now?\nYou can choose an option below or type your own.",
        "ru": "Что тебя сейчас больше всего мучает?\nМожешь выбрать вариант ниже или написать свой.",
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
}


def t(key: str, lang: str = "en", **kwargs: str) -> str:
    entry = TEXTS.get(key, {})
    text = entry.get(lang) or entry.get("en", key)
    if kwargs:
        text = text.format(**kwargs)
    return text
