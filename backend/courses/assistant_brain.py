"""
«Мозг» капибары-помощника без ИИ: понимает вопрос по ключевым словам
и отвечает по данным пользователя (курсы, GPA, дедлайны...).

Здесь нет Django — только обычный Python, поэтому логику легко тестировать.
Контекст (ctx) собирается во views (assistant.py) из базы данных.
"""

LANGS = ("en", "ru", "kz")

# Порядок важен: первое совпадение побеждает.
# «привет, какие дедлайны?» -> deadlines, а не greet.
INTENTS = [
    ("password", ["парол", "password", "құпиясөз", "құпия сөз"]),
    ("final", ["финал", "final", "экзамен", "exam", "емтихан", "стипенд", "scholarship", "сколько нужно", "how much do i need"]),
    ("deadlines", ["дедлайн", "deadline", "задани", "assignment", "тапсырма", "срок", "мерзім", "сдать", "due", "homework", "домашк"]),
    ("grades", ["gpa", "оценк", "балл", "grade", "score", "баға", "транскрипт", "transcript", "успеваем"]),
    ("waitlist", ["очеред", "waitlist", "кезек", "мест нет", "no seats"]),
    ("enroll", ["записат", "запись", "enroll", "тіркел", "жазыл", "join"]),
    ("achievements", ["достижен", "achievement", "жетістік", "бейдж", "badge"]),
    ("search", ["поиск", "найти", "search", "ctrl", "іздеу", "find"]),
    ("settings", ["тема", "язык", "theme", "language", "тіл", "аватар", "avatar", "настройк", "settings", "баптау", "темн", "dark"]),
    ("courses", ["курс", "course", "предмет", "subject", "пән"]),
    ("who", ["кто ты", "who are you", "сен кімсің", "капибар", "capybara", "что ты умеешь", "what can you do", "не істей аласың"]),
    ("thanks", ["спасибо", "thank", "рахмет", "благодар"]),
    ("greet", ["привет", "здравств", "салем", "сәлем", "hello", "hi ", "hey", "добрый"]),
]

LINKS = {
    "en": {"/courses": "Course catalog", "/my-courses": "My courses", "/achievements": "Achievements",
           "/profile": "Profile", "/settings": "Settings", "/teacher": "Teacher cabinet",
           "/forgot-password": "Reset password"},
    "ru": {"/courses": "Каталог курсов", "/my-courses": "Мои курсы", "/achievements": "Достижения",
           "/profile": "Профиль", "/settings": "Настройки", "/teacher": "Кабинет преподавателя",
           "/forgot-password": "Сброс пароля"},
    "kz": {"/courses": "Курстар каталогы", "/my-courses": "Менің курстарым", "/achievements": "Жетістіктер",
           "/profile": "Профиль", "/settings": "Баптаулар", "/teacher": "Оқытушы кабинеті",
           "/forgot-password": "Құпиясөзді қалпына келтіру"},
}

T = {
    "en": {
        "greet": "Hi, {name}! 🤎 I'm Capy, your calm study buddy. Ask me about your courses, GPA, deadlines or how something works here.",
        "who": "I'm Capy, the capybara of CapyClass 🤎 I can tell you about your courses, grades and GPA, upcoming deadlines, how many final points you need, and help you find pages.",
        "thanks": "Always happy to help! Stay calm like a capybara 🧘",
        "fallback": "Hmm, I'm not sure I understood 🤔 Try asking: «my courses», «my GPA», «deadlines», «how much do I need on the final», «how to enroll».",
        "courses_none": "You are not enrolled in any course yet. Open the catalog and pick one — I believe in you! 🌱",
        "courses_head": "Your courses ({n}, {credits} credits):",
        "courses_line": "• {code} — {title} ({credits} cr.){grade}",
        "grade_part": ", grade {grade}",
        "teach_none": "You don't teach any course yet. Create one in the teacher cabinet.",
        "teach_head": "You teach {n} course(s):",
        "teach_line": "• {code} — {title}: {students} student(s)",
        "gpa": "Your GPA is {gpa} 🎓 (graded credits: {graded} of {credits}).",
        "gpa_none": "You don't have grades yet, so there is no GPA. It will appear after the first final grade.",
        "grades_head": "Grades:",
        "grade_line": "• {code}: {grade}",
        "gpa_good": "Great result — keep it up! 🏆",
        "gpa_low": "It's okay, a capybara never panics. Focus on one course at a time 💪",
        "teacher_grades": "You set grades in the teacher cabinet: open a course and choose a grade for each student.",
        "deadlines_none": "No deadlines in the next 2 weeks 🎉 Perfect time to rest… or to get ahead.",
        "deadlines_head": "Upcoming deadlines:",
        "deadline_line": "• {code} «{title}» — {due} ({left})",
        "today": "today!",
        "tomorrow": "tomorrow",
        "in_days": "in {d} days",
        "final_none": "I need at least one graded assignment to calculate what you need on the final.",
        "final_head": "What you need on the final (total = 60% midterm + 40% final):",
        "final_line": "• {code}: current average {avg}% → for 70: {n70}, for 90: {n90}",
        "impossible": "not reachable",
        "enroll": "Open the course catalog, choose a course and press «Enroll». If the course is full, you can join the waitlist — you'll get the seat automatically when it frees up.",
        "waitlist_none": "You are not in any waitlist. If a course is full, press «Join waitlist» on its page.",
        "waitlist_head": "Your waitlists:",
        "waitlist_line": "• {code}: position {pos}",
        "password": "Forgot your password? Log out, press «Forgot password?» on the login page and enter your email — you'll get a reset link. To change the theme or avatar, open Settings.",
        "achievements": "Achievements are on the «Achievements» page 🏆 You get them for enrolling, submitting work, grades, GPA… and for petting me 10 times 🤎",
        "search": "Press Ctrl+K (⌘K on Mac) anywhere to open quick search: courses, pages and actions.",
        "settings": "In Settings you can change the avatar, theme (light/dark), language and turn me (the walking capybara) on or off.",
    },
    "ru": {
        "greet": "Привет, {name}! 🤎 Я Капи, твоя спокойная помощница по учёбе. Спроси меня про курсы, GPA, дедлайны или как здесь что работает.",
        "who": "Я Капи — капибара CapyClass 🤎 Могу рассказать про твои курсы, оценки и GPA, ближайшие дедлайны, сколько нужно набрать на финале, и помочь найти нужную страницу.",
        "thanks": "Всегда рада помочь! Будь спокойной, как капибара 🧘",
        "fallback": "Хм, кажется, я не поняла 🤔 Попробуй спросить: «мои курсы», «мой GPA», «дедлайны», «сколько нужно на финале», «как записаться».",
        "courses_none": "Ты пока не записан(а) ни на один курс. Открой каталог и выбери — я в тебя верю! 🌱",
        "courses_head": "Твои курсы ({n}, кредитов: {credits}):",
        "courses_line": "• {code} — {title} ({credits} кр.){grade}",
        "grade_part": ", оценка {grade}",
        "teach_none": "Ты пока не ведёшь ни одного курса. Создай курс в кабинете преподавателя.",
        "teach_head": "Ты ведёшь курсов: {n}",
        "teach_line": "• {code} — {title}: студентов {students}",
        "gpa": "Твой GPA: {gpa} 🎓 (оценено кредитов: {graded} из {credits}).",
        "gpa_none": "Оценок пока нет, поэтому GPA ещё не посчитан. Он появится после первой итоговой оценки.",
        "grades_head": "Оценки:",
        "grade_line": "• {code}: {grade}",
        "gpa_good": "Отличный результат, так держать! 🏆",
        "gpa_low": "Ничего, капибара никогда не паникует. Займись одним курсом за раз 💪",
        "teacher_grades": "Оценки ставятся в кабинете преподавателя: открой курс и выбери оценку каждому студенту.",
        "deadlines_none": "В ближайшие 2 недели дедлайнов нет 🎉 Можно отдохнуть… или сделать задания заранее.",
        "deadlines_head": "Ближайшие дедлайны:",
        "deadline_line": "• {code} «{title}» — {due} ({left})",
        "today": "сегодня!",
        "tomorrow": "завтра",
        "in_days": "через {d} дн.",
        "final_none": "Чтобы посчитать, сколько нужно на финале, нужна хотя бы одна оценённая работа.",
        "final_head": "Сколько нужно на финале (итог = 60% рубежка + 40% финал):",
        "final_line": "• {code}: средний балл сейчас {avg}% → на 70: {n70}, на 90: {n90}",
        "impossible": "уже не получится",
        "enroll": "Открой каталог курсов, выбери курс и нажми «Записаться». Если мест нет, встань в очередь — место дадут автоматически, когда оно освободится.",
        "waitlist_none": "Ты не стоишь ни в одной очереди. Если на курсе нет мест, нажми «Встать в очередь» на его странице.",
        "waitlist_head": "Твои очереди:",
        "waitlist_line": "• {code}: место {pos}",
        "password": "Забыл(а) пароль? Выйди из аккаунта, на странице входа нажми «Забыли пароль?» и введи email — придёт ссылка для сброса. Тему и аватар можно поменять в Настройках.",
        "achievements": "Достижения — на странице «Достижения» 🏆 Их дают за запись на курсы, сданные работы, оценки, GPA… и за то, что погладишь меня 10 раз 🤎",
        "search": "Нажми Ctrl+K (⌘K на Mac) на любой странице — откроется быстрый поиск по курсам, страницам и действиям.",
        "settings": "В Настройках можно поменять аватар, тему (светлая/тёмная), язык и включить или выключить меня — гуляющую капибару.",
    },
    "kz": {
        "greet": "Сәлем, {name}! 🤎 Мен Капи — сабақтағы сабырлы көмекшің. Курстар, GPA, дедлайндар немесе сайт туралы сұра.",
        "who": "Мен Капи — CapyClass капибарасымын 🤎 Курстарың, бағаларың мен GPA, жақын дедлайндар, финалда қанша керек екенін айтып, қажет бетті табуға көмектесемін.",
        "thanks": "Әрқашан көмектесуге қуаныштымын! Капибара сияқты сабырлы бол 🧘",
        "fallback": "Хм, түсінбей қалдым 🤔 Былай сұрап көр: «менің курстарым», «менің GPA», «дедлайндар», «финалда қанша керек», «қалай жазылуға болады».",
        "courses_none": "Сен әзірге ешбір курсқа жазылмағансың. Каталогты ашып, курс таңда — саған сенемін! 🌱",
        "courses_head": "Сенің курстарың ({n}, кредит: {credits}):",
        "courses_line": "• {code} — {title} ({credits} кр.){grade}",
        "grade_part": ", баға {grade}",
        "teach_none": "Сен әзірге ешбір курс жүргізбейсің. Оқытушы кабинетінде курс құр.",
        "teach_head": "Сен жүргізетін курстар: {n}",
        "teach_line": "• {code} — {title}: студенттер {students}",
        "gpa": "Сенің GPA: {gpa} 🎓 (бағаланған кредит: {graded} / {credits}).",
        "gpa_none": "Әзірге баға жоқ, сондықтан GPA есептелмеген. Ол алғашқы қорытынды бағадан кейін шығады.",
        "grades_head": "Бағалар:",
        "grade_line": "• {code}: {grade}",
        "gpa_good": "Керемет нәтиже, осылай жалғастыр! 🏆",
        "gpa_low": "Ештеңе етпейді, капибара ешқашан абыржымайды. Бір уақытта бір курсқа көңіл бөл 💪",
        "teacher_grades": "Бағалар оқытушы кабинетінде қойылады: курсты ашып, әр студентке баға таңда.",
        "deadlines_none": "Алдағы 2 аптада дедлайн жоқ 🎉 Демалуға… немесе тапсырмаларды алдын ала орындауға болады.",
        "deadlines_head": "Жақын дедлайндар:",
        "deadline_line": "• {code} «{title}» — {due} ({left})",
        "today": "бүгін!",
        "tomorrow": "ертең",
        "in_days": "{d} күннен кейін",
        "final_none": "Финалда қанша керек екенін есептеу үшін кемінде бір бағаланған жұмыс керек.",
        "final_head": "Финалда қанша керек (қорытынды = 60% аралық + 40% финал):",
        "final_line": "• {code}: қазіргі орташа {avg}% → 70 үшін: {n70}, 90 үшін: {n90}",
        "impossible": "енді мүмкін емес",
        "enroll": "Курстар каталогын ашып, курсты таңда да «Жазылу» бас. Орын болмаса, кезекке тұр — орын босағанда автоматты түрде беріледі.",
        "waitlist_none": "Сен ешбір кезекте тұрған жоқсың. Курста орын болмаса, оның бетінде «Кезекке тұру» бас.",
        "waitlist_head": "Сенің кезектерің:",
        "waitlist_line": "• {code}: {pos}-орын",
        "password": "Құпиясөзді ұмыттың ба? Аккаунттан шығып, кіру бетінде «Құпиясөзді ұмыттыңыз ба?» бас та email енгіз — қалпына келтіру сілтемесі келеді. Тақырып пен аватарды Баптауларда өзгертуге болады.",
        "achievements": "Жетістіктер «Жетістіктер» бетінде 🏆 Олар курсқа жазылу, жұмыс тапсыру, бағалар, GPA… және мені 10 рет сипағаның үшін беріледі 🤎",
        "search": "Кез келген бетте Ctrl+K (Mac-та ⌘K) бас — курстар, беттер мен әрекеттер бойынша жылдам іздеу ашылады.",
        "settings": "Баптауларда аватарды, тақырыпты (ашық/қараңғы), тілді өзгертіп, мені — жүретін капибараны — қосып не өшіре аласың.",
    },
}


def detect_intent(message):
    text = " " + (message or "").lower().strip() + " "
    for intent, words in INTENTS:
        if any(word in text for word in words):
            return intent
    return "fallback"


def _days_left(days, t):
    if days <= 0:
        return t["today"]
    if days == 1:
        return t["tomorrow"]
    return t["in_days"].format(d=days)


def _fmt(value):
    # 85.0 -> "85", 85.5 -> "85.5"
    if value is None:
        return "—"
    return f"{value:g}"


def _link_list(lang, *routes):
    labels = LINKS[lang]
    return [{"label": labels[r], "url": r} for r in routes]


def rule_answer(message, ctx, lang="ru"):
    """Возвращает (текст, ссылки, intent) — ответ без ИИ."""
    if lang not in LANGS:
        lang = "ru"
    t = T[lang]
    intent = detect_intent(message)
    is_teacher = ctx.get("role") in ("teacher", "admin")
    lines = []
    links = []

    if intent == "greet":
        lines.append(t["greet"].format(name=ctx.get("name") or "🙂"))
    elif intent == "who":
        lines.append(t["who"])
    elif intent == "thanks":
        lines.append(t["thanks"])

    elif intent == "courses":
        courses = ctx.get("courses", [])
        if is_teacher:
            if not courses:
                lines.append(t["teach_none"])
            else:
                lines.append(t["teach_head"].format(n=len(courses)))
                for c in courses:
                    lines.append(t["teach_line"].format(code=c["code"], title=c["title"], students=c.get("students", 0)))
            links = _link_list(lang, "/teacher")
        elif not courses:
            lines.append(t["courses_none"])
            links = _link_list(lang, "/courses")
        else:
            total = sum(c["credits"] for c in courses)
            lines.append(t["courses_head"].format(n=len(courses), credits=total))
            for c in courses:
                grade = t["grade_part"].format(grade=c["grade"]) if c.get("grade") else ""
                lines.append(t["courses_line"].format(code=c["code"], title=c["title"], credits=c["credits"], grade=grade))
            links = _link_list(lang, "/my-courses", "/courses")

    elif intent == "grades":
        if is_teacher:
            lines.append(t["teacher_grades"])
            links = _link_list(lang, "/teacher")
        else:
            gpa = ctx.get("gpa")
            if gpa is None:
                lines.append(t["gpa_none"])
            else:
                lines.append(t["gpa"].format(gpa=f"{gpa:.2f}", graded=ctx.get("graded_credits", 0),
                                             credits=ctx.get("total_credits", 0)))
                graded = [c for c in ctx.get("courses", []) if c.get("grade")]
                if graded:
                    lines.append(t["grades_head"])
                    for c in graded:
                        lines.append(t["grade_line"].format(code=c["code"], grade=c["grade"]))
                lines.append(t["gpa_good"] if gpa >= 3.0 else t["gpa_low"])
            links = _link_list(lang, "/my-courses", "/achievements")

    elif intent == "deadlines":
        deadlines = ctx.get("deadlines", [])
        if not deadlines:
            lines.append(t["deadlines_none"])
        else:
            lines.append(t["deadlines_head"])
            for d in deadlines[:6]:
                lines.append(t["deadline_line"].format(code=d["code"], title=d["title"], due=d["due"],
                                                       left=_days_left(d["days_left"], t)))
        links = _link_list(lang, "/teacher" if is_teacher else "/my-courses")

    elif intent == "final":
        standing = [s for s in ctx.get("standing", []) if s.get("avg") is not None]
        if is_teacher or not standing:
            lines.append(t["final_none"])
        else:
            lines.append(t["final_head"])
            for s in standing:
                n70 = _fmt(s["need70"]) if s.get("need70") is not None else t["impossible"]
                n90 = _fmt(s["need90"]) if s.get("need90") is not None else t["impossible"]
                lines.append(t["final_line"].format(code=s["code"], avg=_fmt(s["avg"]), n70=n70, n90=n90))
        links = _link_list(lang, "/my-courses")

    elif intent == "enroll":
        lines.append(t["enroll"])
        links = _link_list(lang, "/courses")

    elif intent == "waitlist":
        waitlist = ctx.get("waitlist", [])
        if not waitlist:
            lines.append(t["waitlist_none"])
        else:
            lines.append(t["waitlist_head"])
            for w in waitlist:
                lines.append(t["waitlist_line"].format(code=w["code"], pos=w["position"]))
        links = _link_list(lang, "/courses")

    elif intent == "password":
        lines.append(t["password"])
        links = _link_list(lang, "/settings")
    elif intent == "achievements":
        lines.append(t["achievements"])
        links = _link_list(lang, "/achievements")
    elif intent == "search":
        lines.append(t["search"])
    elif intent == "settings":
        lines.append(t["settings"])
        links = _link_list(lang, "/settings")
    else:
        lines.append(t["fallback"])

    return "\n".join(lines), links, intent


LANG_NAMES = {"en": "English", "ru": "Russian", "kz": "Kazakh"}


def system_prompt(ctx, lang):
    """Инструкция для ИИ: кто такая Капи и какие данные о пользователе есть."""
    import json
    return (
        "You are Capy, a calm, kind and slightly funny capybara assistant inside CapyClass, a university LMS "
        "(learning management system). Answer in " + LANG_NAMES.get(lang, "Russian") + ". "
        "Keep answers short: 1-6 sentences or a short list. Use at most one emoji. "
        "Plain text only, no markdown tables or headings. "
        "Use ONLY the user data below for facts about their courses, grades, GPA and deadlines; "
        "if something is not in the data, say you don't know. Never invent grades or dates. "
        "Total score = 60% midterm (assignments average) + 40% final. GPA scale: A=4.0 ... F=0. "
        "Site pages: /courses (catalog, enroll, waitlist), /my-courses, /achievements, /profile, "
        "/settings (avatar, theme, language, walking capybara on/off), /teacher (teachers: courses, grades). "
        "Quick search: Ctrl+K. Forgot password: log out, then «Forgot password?» on the login page. "
        "You may help with general study questions (explain a topic, make a study plan), "
        "but do not write full homework solutions for the user to submit as their own.\n\n"
        "User data (JSON):\n" + json.dumps(ctx, ensure_ascii=False, default=str)
    )
