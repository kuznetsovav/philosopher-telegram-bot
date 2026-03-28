import random
from typing import Optional

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
    "rate_limit": {
        "en": "Slow down.",
        "ru": "Не так быстро.",
    },
    "daily_limit": {
        "en": "You've reached today's limit. Come back tomorrow.",
        "ru": "Ты достиг лимита на сегодня. Продолжим завтра.",
    },
    "closure_continue_prompt": {
        "en": "Do you want to continue or start a new topic?",
        "ru": "Хочешь продолжить или начать новую тему?",
    },
}

PHILOSOPHER_INFO: dict[str, dict[str, str]] = {
    "nietzsche": {
        "en": (
            "Friedrich Nietzsche (1844–1900, Germany)\n"
            "Philosopher of power, self-overcoming, and breaking illusions."
        ),
        "ru": (
            "Фридрих Ницше (1844–1900, Германия)\n"
            "Философ воли к силе, преодоления себя и разрушения иллюзий."
        ),
    },
    "sartre": {
        "en": (
            "Jean-Paul Sartre (1905–1980, France)\n"
            "Existentialist. You are fully responsible for your choices."
        ),
        "ru": (
            "Жан-Поль Сартр (1905–1980, Франция)\n"
            "Экзистенциализм. Ты полностью ответственен за свой выбор."
        ),
    },
    "camus": {
        "en": (
            "Albert Camus (1913–1960, France)\n"
            "Philosopher of the absurd. Life has no meaning — and that’s okay."
        ),
        "ru": (
            "Альбер Камю (1913–1960, Франция)\n"
            "Философ абсурда. У жизни нет смысла — и это нормально."
        ),
    },
}

UNCERTAINTY_RESPONSES: dict[str, dict[str, list[str]]] = {
    "nietzsche": {
        "en": [
            (
                "You say you don't know — that's not ignorance, it's a refusal to look. "
                "Narrow the fog to one room in your life. What are you pretending is still ambiguous?"
            ),
            (
                '"I don\'t know" is cheap comfort. You know enough to feel the wound. '
                "Which single choice this week did you avoid naming out loud?"
            ),
            (
                "Not knowing is your alibi. Strip it: what would you have to do tomorrow "
                "if you admitted you already know what you're avoiding?"
            ),
            (
                "The abyss isn't empty — you're leaning back. Pick one concrete failure from the last month "
                "you refuse to call by its real name. What is it?"
            ),
            (
                "Spare me the fog. You act anyway; that means you know something. "
                "What truth about your situation would force you to change if you stopped dodging it?"
            ),
            (
                "Weakness hides behind vagueness. Cut the scope: one relationship, one habit, one fear — "
                "which is it, and what are you protecting by saying you don't know?"
            ),
        ],
        "ru": [
            (
                "Ты говоришь «не знаю» — это не невежество, это отказ смотреть. "
                "Сузь туман до одной сферы жизни. Что ты притворяешься, будто ещё неясно?"
            ),
            (
                "«Не знаю» — дешёвое утешение. Ты знаешь достаточно, чтобы чувствовать боль. "
                "Какой один выбор на этой неделе ты не назвал вслух?"
            ),
            (
                "Незнание — твоё алиби. Сними его: что тебе пришлось бы сделать завтра, "
                "если бы ты признал, что уже знаешь, от чего бежишь?"
            ),
            (
                "Бездна не пуста — ты отстранился. Назови один конкретный провал за последний месяц, "
                "который не хочешь называть своим именем. Что это?"
            ),
            (
                "Без тумана. Ты всё равно действуешь — значит, что-то знаешь. "
                "Какая правда о твоей ситуации заставила бы тебя меняться, если перестать от неё прятаться?"
            ),
            (
                "Слабость прячется за размытостью. Сузь: один человек, одна привычка, один страх — "
                "что из этого, и что ты защищаешь словами «не знаю»?"
            ),
        ],
    },
    "sartre": {
        "en": [
            (
                "Not knowing is still a position — you choose to leave the situation undefined. "
                "What commitment are you refusing to make by hiding in vagueness?"
            ),
            (
                '"I don\'t know" buys you one more day without responsibility. '
                "Name the fork in the road you're staring at but won't call a decision."
            ),
            (
                "Freedom doesn't wait for certainty. Which real option have you already mapped "
                "and dismissed because owning it would make you accountable?"
            ),
            (
                "You are not a thing the world pushes around — you assign weight to facts. "
                "What meaning are you refusing to assign to what already happened to you?"
            ),
            (
                "Bad faith loves the mask of uncertainty. What single fact about your life, if spoken clearly, "
                "would strip away your excuse?"
            ),
            (
                "Silence is a choice with consequences. What are you accepting — in work, love, or self-respect — "
                "by pretending the answer isn't there yet?"
            ),
        ],
        "ru": [
            (
                "«Не знаю» — тоже позиция: ты оставляешь ситуацию неопределённой. "
                "За каким обязательством ты прячешься за этой туманностью?"
            ),
            (
                "«Не знаю» покупает тебе ещё один день без ответственности. "
                "Назови развилку, на которую смотришь, но не хочешь назвать решением."
            ),
            (
                "Свобода не ждёт ясности. Какой реальный вариант ты уже прикинул "
                "и отбросил, потому что признать его значит нести ответственность?"
            ),
            (
                "Ты не вещь, которую толкает мир — ты придаёшь фактам вес. "
                "Какой смысл ты отказываешься приписать тому, что с тобой уже случилось?"
            ),
            (
                "Самообман любит маску неуверенности. Какой один факт о твоей жизни, сказанный чётко, "
                "сорвал бы с тебя оправдание?"
            ),
            (
                "Молчание — выбор с последствиями. Что ты принимаешь — в работе, в любви, в уважении к себе — "
                "притворяясь, что ответа ещё нет?"
            ),
        ],
    },
    "camus": {
        "en": [
            (
                "The absurd doesn't give you a pass to dissolve into fog. "
                "What specific habit are you using so you never have to answer clearly?"
            ),
            (
                "You don't know — yet you repeat the same week. "
                "Which loop are you calling 'mystery' instead of naming the choice inside it?"
            ),
            (
                "Sisyphus doesn't confuse the stone with the weather. What is the stone in your life — "
                "the burden you won't describe honestly — and what would honesty cost you?"
            ),
            (
                "Silence isn't neutral here; it's a stance. What are you agreeing to carry "
                "by refusing to say what you already sense?"
            ),
            (
                "Revolt begins with naming what is. Narrow it: one hour yesterday where you felt the absurd — "
                "what exactly did you do right after, and why that?"
            ),
            (
                "Clarity hurts less than endless maybe. What small, concrete next step are you avoiding "
                "because pretending you don't know feels safer?"
            ),
        ],
        "ru": [
            (
                "Абсурд не даёт права раствориться в тумане. "
                "Какую конкретную привычку ты используешь, чтобы никогда не ответить чётко?"
            ),
            (
                "Ты «не знаешь» — но повторяешь одну и ту же неделю. "
                "Какой цикл ты называешь «тайной», вместо того чтобы назвать выбор внутри него?"
            ),
            (
                "Сизиф не путает камень с погодой. Что за камень в твоей жизни — ноша, которую ты не хочешь "
                "описать честно — и чего стоит эта честность?"
            ),
            (
                "Молчание здесь не нейтрально — это позиция. С чем ты соглашаешься нести, "
                "отказываясь сказать то, что уже чувствуешь?"
            ),
            (
                "Бунт начинается с того, чтобы назвать то, что есть. Сузь: один час вчера, когда ты ощутил абсурд — "
                "что ты сделал сразу после и почему именно это?"
            ),
            (
                "Ясность больнее бесконечного «может». Какой маленький конкретный шаг ты избегаешь, "
                "потому что притворяться, что не знаешь, кажется безопаснее?"
            ),
        ],
    },
}

CONFUSION_RESPONSES: dict[str, dict[str, list[str]]] = {
    "nietzsche": {
        "en": [
            (
                "Let's simplify. Cut the noise: in one short sentence, what part of *your* situation "
                "felt impossible to follow?"
            ),
            (
                "Plain speech — no riddles. What decision are you hiding behind 'I don't get it'?"
            ),
            (
                "Two options only: fear of being wrong, or fear of moving at all. Which is louder right now?"
            ),
            (
                "Enough abstraction. Name one concrete moment this week when everything sounded like gibberish — "
                "what was happening?"
            ),
        ],
        "ru": [
            (
                "Давай упростим. Срежь шум: одним коротким предложением — какая часть *твоей* ситуации "
                "казалась невозможной понять?"
            ),
            (
                "Простыми словами, без загадок. За каким решением ты прячешься за «не понимаю»?"
            ),
            (
                "Только два варианта: боязнь ошибиться или боязнь сдвинуться с места. Что сильнее сейчас?"
            ),
            (
                "Хватит абстракций. Назови один конкретный момент на этой неделе, когда всё казалось кашей — "
                "что происходило?"
            ),
        ],
    },
    "sartre": {
        "en": [
            "Let's simplify. What is hardest for you to decide right now?",
            "Let me ask differently: what decision are you avoiding?",
            "Simpler: pick one — fear of mistake or fear of change?",
            (
                "Step back from the wording. Which fact about your life are you not yet translating "
                "into a clear choice?"
            ),
        ],
        "ru": [
            "Давай упростим. Что тебе сейчас сложнее всего решить?",
            "Хорошо, по-другому: какое решение ты откладываешь?",
            "Скажу проще: выбери одно — боишься ошибиться или менять ситуацию?",
            (
                "Отойди от формулировок. Какой факт о твоей жизни ты ещё не перевёл "
                "в ясный выбор?"
            ),
        ],
    },
    "camus": {
        "en": [
            (
                "Let's simplify. What felt unclear — the feeling itself, or what you should do about it?"
            ),
            (
                "Softer angle: what have you been circling without naming out loud?"
            ),
            (
                "Two gentle paths — a small wrong step, or staying frozen. Which feels closer today?"
            ),
            (
                "No philosophy lecture. What's one thing you could describe clearly right now if you slowed down?"
            ),
        ],
        "ru": [
            (
                "Давай упростим. Что было неясно — само чувство или что с этим делать?"
            ),
            (
                "Мягче: о чём ты ходишь кругами, не называя вслух?"
            ),
            (
                "Два спокойных пути — маленький неверный шаг или застыть. Что ближе сегодня?"
            ),
            (
                "Без лекции. Что одно ты мог бы описать ясно прямо сейчас, если замедлиться?"
            ),
        ],
    },
}


def pick_confusion_response(philosopher_name: str, lang: str, state: dict) -> str:
    key = philosopher_name.lower()
    row = CONFUSION_RESPONSES.get(key) or CONFUSION_RESPONSES["camus"]
    lg = lang if lang in ("en", "ru") else "en"
    variants = row.get(lg) or row["en"]
    last = state.get("_last_confusion_template")
    pool = [v for v in variants if v != last] or list(variants)
    chosen = random.choice(pool)
    state["_last_confusion_template"] = chosen
    return chosen


def pick_uncertainty_response(philosopher_name: str, lang: str, state: dict) -> str:
    key = philosopher_name.lower()
    row = UNCERTAINTY_RESPONSES.get(key) or UNCERTAINTY_RESPONSES["nietzsche"]
    lg = lang if lang in ("en", "ru") else "en"
    variants = row.get(lg) or row["en"]
    last = state.get("_last_uncertainty_template")
    pool = [v for v in variants if v != last] or list(variants)
    chosen = random.choice(pool)
    state["_last_uncertainty_template"] = chosen
    return chosen


def philosopher_intro(philosopher_name: str, lang: str) -> Optional[str]:
    key = philosopher_name.lower()
    row = PHILOSOPHER_INFO.get(key)
    if not row:
        return None
    lg = lang if lang in ("en", "ru") else "en"
    return row.get(lg) or row.get("en")


def t(key: str, lang: str = "en", **kwargs: str) -> str:
    entry = TEXTS.get(key, {})
    text = entry.get(lang) or entry.get("en", key)
    if kwargs:
        text = text.format(**kwargs)
    return text
