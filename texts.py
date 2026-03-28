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
    "ask_philosophy_approach": {
        "en": "How do you want to approach this?",
        "ru": "Как ты хочешь на это посмотреть?",
    },
    "choose_philosopher_in_category": {
        "en": "Who should speak?",
        "ru": "Кто должен заговорить?",
    },
    "pick_philosopher": {
        "en": "Pick a philosopher from the buttons below.",
        "ru": "Выбери философа из кнопок ниже.",
    },
    "philosopher_chosen": {
        "en": "You chose {name}.",
        "ru": "Ты выбрал {name}.",
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
    "kierkegaard": {
        "en": (
            "Søren Kierkegaard (1813–1855, Denmark)\n"
            "Existential thinker of anxiety, faith, and the leap beyond mere talk."
        ),
        "ru": (
            "Сёрён Кьеркегор (1813–1855, Дания)\n"
            "Мыслитель тревоги, веры и прыжка — не пустых слов."
        ),
    },
    "marcus": {
        "en": (
            "Marcus Aurelius (121–180, Rome)\n"
            "Stoic emperor: judgment, duty, and shrinking the drama."
        ),
        "ru": (
            "Марк Аврелий (121–180, Рим)\n"
            "Стоический император: суждение, долг и меньше драмы."
        ),
    },
    "epictetus": {
        "en": (
            "Epictetus (~50–135, Greece)\n"
            "Stoic teacher: control what is yours; stop demanding the world obey."
        ),
        "ru": (
            "Эпиктет (~50–135, Греция)\n"
            "Стоический учитель: владей своим; не требуй от мира покорности."
        ),
    },
    "seneca": {
        "en": (
            "Seneca (~4 BCE–65 CE, Rome)\n"
            "Stoic senator: time, anger, and practicing under pressure."
        ),
        "ru": (
            "Сенека (~4 до н.э.–65 н.э., Рим)\n"
            "Стоический сенатор: время, гнев и практика под давлением."
        ),
    },
    "buddha": {
        "en": (
            "The Buddha (~5th c. BCE, India)\n"
            "Maps craving, suffering, and seeing clearly — without easy comfort."
        ),
        "ru": (
            "Будда (~V в. до н.э., Индия)\n"
            "Показывает жажду, страдание и ясность — без дешёвого утешения."
        ),
    },
    "william_james": {
        "en": (
            "William James (1842–1910, USA)\n"
            "Pragmatist: truth in experience, choices that cash out in life."
        ),
        "ru": (
            "Уильям Джеймс (1842–1910, США)\n"
            "Прагматист: истина в опыте, выборы, которые меняют жизнь."
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

_STOIC_UNCERTAINTY_EN = [
    (
        "Not knowing is a story about what you refuse to judge. "
        "What part of this situation are you pretending is outside your power to name?"
    ),
    (
        '"I don\'t know" often means "I don\'t want the cost of choosing." '
        "Which small duty are you dodging by staying vague?"
    ),
    (
        "The world is indifferent; your opinion is yours to own. "
        "What interpretation of events are you renting from panic instead of selecting on purpose?"
    ),
    (
        "Confusion is sometimes appetite for more data you do not need. "
        "What action today would make the next step obvious even if fear stays?"
    ),
    (
        "You cannot steer another person's will — only your response. "
        "What are you demanding that violates that line, and what would you do if you stopped?"
    ),
    (
        "Silence can be discipline or cowardice. Which is it here — "
        "and what would change if you spoke one plain sentence about what you actually want?"
    ),
]
_STOIC_UNCERTAINTY_RU = [
    (
        "«Не знаю» — часто история о том, что ты не хочешь судить. "
        "Какую часть ситуации ты притворяешься, что не в твоей власти назвать?"
    ),
    (
        "«Не знаю» часто значит «не хочу цены выбора». "
        "Какой маленький долг ты избегаешь, оставаясь в тумане?"
    ),
    (
        "Мир равнодушен; твоё мнение — твоё. "
        "Какую интерпретацию событий ты арендуешь у паники вместо того чтобы выбрать её сам?"
    ),
    (
        "Путаница иногда — жажда лишних данных. "
        "Какое действие сегодня сделало бы следующий шаг ясным, даже если страх останется?"
    ),
    (
        "Чужую волю не повернуть — только свой ответ. "
        "Чего ты требуешь, что бьётся об эту границу, и что сделаешь, если перестанешь?"
    ),
    (
        "Молчание может быть дисциплиной или трусостью. Что здесь — "
        "и что изменится, если ты произнесёшь одно простое предложение о том, чего хочешь на самом деле?"
    ),
]
for _slug in ("marcus", "epictetus", "seneca"):
    UNCERTAINTY_RESPONSES[_slug] = {
        "en": list(_STOIC_UNCERTAINTY_EN),
        "ru": list(_STOIC_UNCERTAINTY_RU),
    }

UNCERTAINTY_RESPONSES["kierkegaard"] = {
    "en": [
        (
            "Anxiety feeds on the unnamed. You are not waiting for information — you are postponing commitment. "
            "What leap have you been circling without calling it a choice?"
        ),
        (
            '"I don\'t know" can be the aesthetic dodge of infinite reflection. '
            "Cut it: what would you lose if you stopped researching and acted tomorrow?"
        ),
        (
            "The absurd here is not the world — it is your double life between possibility and refusal. "
            "Which self are you performing so you never have to be one person?"
        ),
        (
            "Faith — for you — is not comfort; it is venturing where proof ends. "
            "What risk are you branding as confusion so you never have to own it?"
        ),
        (
            "Despair is also a stance. Name the version of yourself you are protecting by staying suspended."
        ),
        (
            "Silence before God or fate is still a decision. What are you granting veto power "
            "by pretending the answer has not arrived?"
        ),
    ],
    "ru": [
        (
            "Тревога питается неназванным. Ты ждёшь не информации — ты откладываешь обязательство. "
            "О каком прыжке ты ходишь кругами, не называя его выбором?"
        ),
        (
            "«Не знаю» может быть эстетическим уходом в бесконечное размышление. "
            "Режь: что ты потеряешь, если завтра перестанешь «изучать» и сделаешь шаг?"
        ),
        (
            "Абсурд здесь не в мире — в твоей двойной жизни между возможностью и отказом. "
            "Какую роль ты играешь, чтобы не быть одним человеком?"
        ),
        (
            "Вера — для тебя — не утешение, а шаг туда, где кончаются доказательства. "
            "Какой риск ты называешь сомнением, чтобы не признать его своим?"
        ),
        (
            "Отчаяние — тоже позиция. Назови версию себя, которую защищаешь, зависая в подвешенном состоянии."
        ),
        (
            "Молчание перед судьбой — всё равно решение. Кому ты даёшь право вето, "
            "притворяясь, что ответ ещё не пришёл?"
        ),
    ],
}
UNCERTAINTY_RESPONSES["buddha"] = {
    "en": [
        (
            "Not knowing, repeated, is often clinging to a story that hurts. "
            "What craving is this confusion buying you — comfort, identity, avoidance?"
        ),
        (
            '"I don\'t know" can be a shield against seeing cause and effect. '
            "What habit restarted the same suffering this week?"
        ),
        (
            "The mind loves fog when clear sight imposes restraint. "
            "What would you have to stop doing if you admitted you already see the chain?"
        ),
        (
            "Suffering plus resistance becomes drama. Where are you adding the second arrow "
            "by refusing to name what is actually happening?"
        ),
        (
            "Clarity is not cruelty. One breath, one fact: what is the simplest true sentence "
            "you are refusing to say about your situation?"
        ),
        (
            "Liberation starts with honest attention. What are you turning away from "
            "the moment you say you cannot know?"
        ),
    ],
    "ru": [
        (
            "Повторяемое «не знаю» часто — цепляние за историю, которая ранит. "
            "Какую жажду кормит эта путаница — покой, образ себя, избегание?"
        ),
        (
            "«Не знаю» может быть щитом от причинности. "
            "Какая привычка снова запустила то же страдание на этой неделе?"
        ),
        (
            "Уму нравится туман, когда ясность требует сдержанности. "
            "Что ты перестал бы делать, если признал, что уже видишь цепочку?"
        ),
        (
            "Страдание плюс сопротивление — драма. Где ты добавляешь вторую стрелу, "
            "отказываясь назвать, что происходит на самом деле?"
        ),
        (
            "Ясность — не жестокость. Одно дыхание, один факт: какое простое правдивое предложение "
            "ты не хочешь сказать о своей ситуации?"
        ),
        (
            "Освобождение начинается с честного внимания. От чего ты отворачиваешься "
            "в тот момент, когда говоришь, что не можешь знать?"
        ),
    ],
}
UNCERTAINTY_RESPONSES["william_james"] = {
    "en": [
        (
            "Ideas are cheap until they cash out in conduct. "
            "What difference would it make tomorrow if you believed one sharp answer instead of 'I don't know'?"
        ),
        (
            '"I don\'t know" is sometimes a way to avoid betting. '
            "What hypothesis about your life are you refusing to test in action?"
        ),
        (
            "Not deciding is experimenting with paralysis. Run the thought experiment: "
            "if you acted as if you knew for one week, what would you do first?"
        ),
        (
            "Truth happens in the living. Which trail of consequences are you ignoring "
            "while you wait for a feeling of certainty?"
        ),
        (
            "Stream of thought: notice the edits. What detail did your story drop "
            "so the problem could stay abstract?"
        ),
        (
            "Pragmatic cut: what works badly in your current story, and what working belief "
            "would force you to change behavior today?"
        ),
    ],
    "ru": [
        (
            "Идеи дешевы, пока не обналичиваются в поступках. "
            "Какая разница завтра, если ты поверишь одному острому ответу вместо «не знаю»?"
        ),
        (
            "«Не знаю» иногда — способ не делать ставку. "
            "Какую гипотезу о своей жизни ты не хочешь проверить действием?"
        ),
        (
            "Не решать — значит экспериментировать с оцепенением. Мысленный эксперимент: "
            "если бы ты действовал так, будто знаешь, одну неделю — что сделал бы первым?"
        ),
        (
            "Истина случается в живом. Какую цепочку последствий ты игнорируешь, "
            "ждая чувства уверенности?"
        ),
        (
            "Поток мысли: заметь правки. Какую деталь твоя история выбросила, "
            "чтобы проблема осталась абстрактной?"
        ),
        (
            "Прагматичный срез: что плохо работает в твоей текущей истории и какое «рабочее» убеждение "
            "заставило бы тебя сегодня сменить поведение?"
        ),
    ],
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

_STOIC_CONFUSION_EN = [
    "Let's simplify. What part feels unclear — the facts, or what you should do next?",
    "Plain words: what are you afraid would happen if you chose one small next step?",
    "Two buckets — what you control and what you don't. Which bucket is the mess in?",
    "No Stoic lecture. One sentence: what happened, without the story you added?",
]
_STOIC_CONFUSION_RU = [
    "Давай проще. Что неясно — факты или что делать дальше?",
    "Простыми словами: чего ты боишься, если выберешь один маленький следующий шаг?",
    "Две корзины — твоё и не твоё. В какой корзине каша?",
    "Без лекции. Одно предложение: что случилось, без истории, которую ты добавил?",
]
for _slug in ("marcus", "epictetus", "seneca"):
    CONFUSION_RESPONSES[_slug] = {
        "en": list(_STOIC_CONFUSION_EN),
        "ru": list(_STOIC_CONFUSION_RU),
    }

CONFUSION_RESPONSES["kierkegaard"] = {
    "en": [
        "Let's simplify. Are you confused about the situation, or about what you're willing to become?",
        "Different angle: what decision feels like it would cost you your self-image?",
        "One thread only: what are you repeating so the question stays mystical?",
        "Plain speech: what would honesty force you to do this week?",
    ],
    "ru": [
        "Давай проще. Ты не понимаешь ситуацию или не понимаешь, кем готов стать?",
        "Под другим углом: какое решение кажется, что отнимет образ себя?",
        "Одна нить: что ты повторяешь, чтобы вопрос оставался «мистическим»?",
        "Простыми словами: что заставила бы тебя сделать честность на этой неделе?",
    ],
}
CONFUSION_RESPONSES["buddha"] = {
    "en": [
        "Let's simplify. What sensation or thought keeps looping when you say you don't understand?",
        "Softer: what are you holding onto that makes the story hard to parse?",
        "One breath: name one fact, then one reaction — where is the extra suffering?",
        "No doctrine. What would change if you watched the urge instead of obeying it?",
    ],
    "ru": [
        "Давай проще. Какое ощущение или мысль крутится, когда ты говоришь «не понимаю»?",
        "Мягче: за что ты держишься, из-за чего историю трудно разобрать?",
        "Одно дыхание: один факт, потом одна реакция — где лишнее страдание?",
        "Без учения. Что изменится, если смотреть на импульс, а не подчиняться ему?",
    ],
}
CONFUSION_RESPONSES["william_james"] = {
    "en": [
        "Let's simplify. What outcome are you trying to avoid naming?",
        "Pragmatic cut: what would you try for a week if confusion were expensive?",
        "Different question: what evidence do you already have but won't weigh?",
        "Plain: what habit explains the muddle better than any abstract puzzle?",
    ],
    "ru": [
        "Давай проще. Какой исход ты избегаешь назвать?",
        "Прагматично: что бы ты пробовал неделю, если путаница стоила бы дорого?",
        "Другой вопрос: какие свидетельства у тебя уже есть, но ты их не взвешиваешь?",
        "Просто: какая привычка лучше объясняет кашу, чем любая абстрактная загадка?",
    ],
}


_DISPLAY_TO_SLUG: dict[str, str] = {
    "nietzsche": "nietzsche",
    "ницше": "nietzsche",
    "camus": "camus",
    "камю": "camus",
    "sartre": "sartre",
    "сартр": "sartre",
    "kierkegaard": "kierkegaard",
    "кьеркегор": "kierkegaard",
    "marcus aurelius": "marcus",
    "марк аврелий": "marcus",
    "epictetus": "epictetus",
    "эпиктет": "epictetus",
    "seneca": "seneca",
    "сенека": "seneca",
    "the buddha": "buddha",
    "buddha": "buddha",
    "будда": "buddha",
    "william james": "william_james",
    "уильям джеймс": "william_james",
}


def _philosopher_slug(display_name: str) -> str:
    n = display_name.lower().strip()
    if n in PHILOSOPHER_INFO:
        return n
    return _DISPLAY_TO_SLUG.get(n, display_name.lower().replace(" ", "_"))


def pick_confusion_response(philosopher_name: str, lang: str, state: dict) -> str:
    key = _philosopher_slug(philosopher_name)
    row = CONFUSION_RESPONSES.get(key) or CONFUSION_RESPONSES["camus"]
    lg = lang if lang in ("en", "ru") else "en"
    variants = row.get(lg) or row["en"]
    last = state.get("_last_confusion_template")
    pool = [v for v in variants if v != last] or list(variants)
    chosen = random.choice(pool)
    state["_last_confusion_template"] = chosen
    return chosen


def pick_uncertainty_response(philosopher_name: str, lang: str, state: dict) -> str:
    key = _philosopher_slug(philosopher_name)
    row = UNCERTAINTY_RESPONSES.get(key) or UNCERTAINTY_RESPONSES["nietzsche"]
    lg = lang if lang in ("en", "ru") else "en"
    variants = row.get(lg) or row["en"]
    last = state.get("_last_uncertainty_template")
    pool = [v for v in variants if v != last] or list(variants)
    chosen = random.choice(pool)
    state["_last_uncertainty_template"] = chosen
    return chosen


def philosopher_intro(philosopher_name: str, lang: str) -> Optional[str]:
    key = _philosopher_slug(philosopher_name)
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
