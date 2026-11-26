"""
Капибара-помощник: POST /api/assistant/chat/

Тело запроса: {"message": "...", "lang": "ru", "history": [{"role": "user"|"assistant", "content": "..."}]}
Ответ:        {"reply": "...", "links": [{"label": "...", "url": "/courses"}], "source": "ai"|"rules"}

Если задан ключ ИИ (переменная окружения AI_API_KEY), отвечает ИИ
(любой сервис с OpenAI-совместимым API, по умолчанию Google Gemini).
Если ключа нет или ИИ не ответил — работает «мозг» без ИИ (assistant_brain.py).
Ключ хранится только в переменной окружения, в коде его нет.
"""
import json
import os
import urllib.request
from datetime import date, timedelta

from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .assistant_brain import LANGS, rule_answer, system_prompt
from .models import GRADE_POINTS, Assignment, Course, Enrollment, Submission, Waitlist
from .permissions import is_admin, is_teacher

AI_API_URL = os.environ.get(
    "AI_API_URL", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
)
AI_MODEL = os.environ.get("AI_MODEL", "gemini-flash-latest")

MAX_MESSAGE = 500   # символов в одном сообщении
MAX_HISTORY = 6     # сколько прошлых сообщений отправляем ИИ


def build_context(user):
    """Собирает данные пользователя, на которые опирается капибара."""
    today = date.today()
    ctx = {
        "name": user.first_name or user.username,
        "role": "admin" if is_admin(user) else user.role,
        "today": today.isoformat(),
        "courses": [],
        "deadlines": [],
        "standing": [],
        "waitlist": [],
        "gpa": None,
        "total_credits": 0,
        "graded_credits": 0,
    }
    soon = today + timedelta(days=14)

    if is_teacher(user) or is_admin(user):
        courses = Course.objects.filter(teacher=user) if is_teacher(user) else Course.objects.all()[:20]
        for c in courses:
            ctx["courses"].append({"code": c.code, "title": c.title, "credits": c.credits,
                                   "students": c.enrollments.count()})
        assignments = (Assignment.objects.filter(course__in=courses, due_date__gte=today, due_date__lte=soon)
                       .select_related("course").order_by("due_date"))
        for a in assignments:
            ctx["deadlines"].append({"code": a.course.code, "title": a.title, "due": a.due_date.isoformat(),
                                     "days_left": (a.due_date - today).days})
        return ctx

    # студент
    from .views import course_standing  # тот же расчёт, что и в /courses/my-standing/

    enrollments = Enrollment.objects.filter(student=user).select_related("course", "course__teacher")
    total_points = 0
    for e in enrollments:
        c = e.course
        ctx["courses"].append({"code": c.code, "title": c.title, "credits": c.credits, "grade": e.grade})
        ctx["total_credits"] += c.credits
        points = GRADE_POINTS.get(e.grade)
        if points is not None:
            total_points += points * c.credits
            ctx["graded_credits"] += c.credits
        s = course_standing(c, user)
        ctx["standing"].append({"code": c.code, "avg": s["current_midterm_avg"],
                                "need70": s["final_needed_for_70"], "need90": s["final_needed_for_90"]})
    if ctx["graded_credits"]:
        ctx["gpa"] = round(total_points / ctx["graded_credits"], 2)

    submitted = set(Submission.objects.filter(student=user).values_list("assignment_id", flat=True))
    assignments = (Assignment.objects
                   .filter(course__enrollments__student=user, due_date__gte=today, due_date__lte=soon)
                   .select_related("course").order_by("due_date"))
    for a in assignments:
        if a.id in submitted:
            continue
        ctx["deadlines"].append({"code": a.course.code, "title": a.title, "due": a.due_date.isoformat(),
                                 "days_left": (a.due_date - today).days})

    for w in Waitlist.objects.filter(student=user).select_related("course"):
        ctx["waitlist"].append({"code": w.course.code, "position": w.position})
    return ctx


def ask_ai(ctx, lang, history, message):
    """Спросить ИИ. Возвращает текст или None, если ключа нет или произошла ошибка."""
    api_key = os.environ.get("AI_API_KEY", "")
    if not api_key:
        return None
    messages = [{"role": "system", "content": system_prompt(ctx, lang)}]
    for item in history[-MAX_HISTORY:]:
        role = item.get("role")
        content = str(item.get("content", ""))[:MAX_MESSAGE * 2]
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    body = json.dumps({"model": AI_MODEL, "messages": messages, "max_tokens": 500,
                       "temperature": 0.5}).encode("utf-8")
    request = urllib.request.Request(AI_API_URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "capyclass/1.0",
    })
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return text.strip() or None
    except Exception as exc:
        # Видно в терминале runserver; пользователь получит ответ без ИИ
        print(f"[assistant] AI request failed: {exc}")
        return None


# POST /api/assistant/chat/
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def assistant_chat(request):
    message = str(request.data.get("message", "")).strip()[:MAX_MESSAGE]
    lang = request.data.get("lang", "ru")
    if lang not in LANGS:
        lang = "ru"
    history = request.data.get("history") or []
    if not isinstance(history, list):
        history = []
    if not message:
        return Response({"message": ["This field is required."]}, status=400)

    ctx = build_context(request.user)
    rules_text, links, _intent = rule_answer(message, ctx, lang)

    ai_text = ask_ai(ctx, lang, [h for h in history if isinstance(h, dict)], message)
    if ai_text:
        return Response({"reply": ai_text, "links": links, "source": "ai"})
    return Response({"reply": rules_text, "links": links, "source": "rules"})
