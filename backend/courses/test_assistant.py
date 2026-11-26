from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from .assistant_brain import detect_intent, rule_answer
from .models import Assignment, Course, Enrollment, Submission

User = get_user_model()


class AssistantBrainTest(SimpleTestCase):
    def test_intents_in_three_languages(self):
        self.assertEqual(detect_intent("Какой у меня GPA?"), "grades")
        self.assertEqual(detect_intent("show my deadlines"), "deadlines")
        self.assertEqual(detect_intent("менің курстарым"), "courses")
        self.assertEqual(detect_intent("привет, какие дедлайны?"), "deadlines")
        self.assertEqual(detect_intent("сколько нужно на финале"), "final")
        self.assertEqual(detect_intent("абракадабра"), "fallback")

    def test_gpa_answer(self):
        ctx = {"role": "student", "gpa": 3.5, "graded_credits": 6, "total_credits": 9,
               "courses": [{"code": "CS101", "title": "DB", "credits": 3, "grade": "A"}]}
        text, links, intent = rule_answer("мой GPA", ctx, "ru")
        self.assertEqual(intent, "grades")
        self.assertIn("3.50", text)
        self.assertIn("CS101: A", text)
        self.assertEqual(links[0]["url"], "/my-courses")

    def test_final_impossible(self):
        ctx = {"role": "student", "standing": [{"code": "CS101", "avg": 40.0, "need70": 115, "need90": None}]}
        text, _, _ = rule_answer("final", ctx, "en")
        self.assertIn("not reachable", text)


@mock.patch.dict("os.environ", {"AI_API_KEY": ""})
class AssistantApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        teacher = User.objects.create_user("marat", password="x", role="teacher")
        self.student = User.objects.create_user("aruzhan", password="x", role="student")
        self.course = Course.objects.create(code="CS101", title="Databases", teacher=teacher)
        Enrollment.objects.create(student=self.student, course=self.course, grade="B+")
        self.soon = Assignment.objects.create(course=self.course, title="Lab 1",
                                              due_date=date.today() + timedelta(days=2))
        done = Assignment.objects.create(course=self.course, title="Lab 0",
                                         due_date=date.today() + timedelta(days=1))
        Submission.objects.create(assignment=done, student=self.student, answer="ok")

    def ask(self, message, lang="ru"):
        return self.client.post("/api/assistant/chat/", {"message": message, "lang": lang}, format="json")

    def test_login_required(self):
        self.assertEqual(self.ask("hi").status_code, 401)

    def test_deadlines_skip_submitted(self):
        self.client.force_authenticate(self.student)
        data = self.ask("дедлайны").json()
        self.assertEqual(data["source"], "rules")
        self.assertIn("Lab 1", data["reply"])
        self.assertNotIn("Lab 0", data["reply"])

    def test_gpa_from_database(self):
        self.client.force_authenticate(self.student)
        data = self.ask("my gpa", "en").json()
        self.assertIn("3.33", data["reply"])

    def test_empty_message(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.ask("  ").status_code, 400)
