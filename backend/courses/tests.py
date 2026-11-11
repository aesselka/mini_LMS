from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Assignment, Course, Enrollment, Lesson, Submission

User = get_user_model()


class CoursesApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user("admin1", password="x", role="admin")
        self.marat = User.objects.create_user("marat", password="x", role="teacher",
                                              first_name="Marat", last_name="Akhmetov")
        self.gulnar = User.objects.create_user("gulnar", password="x", role="teacher",
                                               first_name="Gulnar", last_name="Iskakova")
        self.student = User.objects.create_user("aruzhan", password="x", role="student")
        self.other_student = User.objects.create_user("timur", password="x", role="student")

        self.db = Course.objects.create(code="CS101", title="Databases", teacher=self.marat)
        self.math = Course.objects.create(code="MATH101", title="Discrete Math", teacher=self.gulnar)

    def codes(self, url):
        return [c["code"] for c in self.client.get(url).json()]

    # courses list and search

    def test_list_courses(self):
        self.assertEqual(self.codes("/api/courses/"), ["CS101", "MATH101"])

    def test_search_by_title(self):
        self.assertEqual(self.codes("/api/courses/?search=data"), ["CS101"])

    def test_search_by_code(self):
        self.assertEqual(self.codes("/api/courses/?search=math"), ["MATH101"])

    def test_search_by_teacher(self):
        self.assertEqual(self.codes("/api/courses/?search=akhmetov"), ["CS101"])

    # who can create courses

    def test_student_cannot_create_course(self):
        self.client.force_authenticate(self.student)
        r = self.client.post("/api/courses/", {"code": "X1", "title": "X"})
        self.assertEqual(r.status_code, 403)

    def test_teacher_creates_course(self):
        self.client.force_authenticate(self.gulnar)
        r = self.client.post("/api/courses/", {"code": "MATH201", "title": "Algebra"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Course.objects.get(code="MATH201").teacher, self.gulnar)

    def test_teacher_cannot_edit_other_course(self):
        self.client.force_authenticate(self.gulnar)
        r = self.client.patch(f"/api/courses/{self.db.id}/", {"title": "new"})
        self.assertEqual(r.status_code, 403)

    def test_admin_creates_course(self):
        self.client.force_authenticate(self.admin)
        r = self.client.post("/api/courses/", {"code": "ENG101", "title": "English",
                                               "teacher_id": self.gulnar.id})
        self.assertEqual(r.status_code, 201)

    # enrollments

    def test_student_enrolls(self):
        self.client.force_authenticate(self.student)
        r = self.client.post("/api/enrollments/", {"course": self.db.id})
        self.assertEqual(r.status_code, 201)

    def test_duplicate_enrollment_api(self):
        self.client.force_authenticate(self.student)
        self.client.post("/api/enrollments/", {"course": self.db.id})
        r = self.client.post("/api/enrollments/", {"course": self.db.id})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Enrollment.objects.count(), 1)

    def test_duplicate_enrollment_db(self):
        Enrollment.objects.create(student=self.student, course=self.db)
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=self.student, course=self.db)

    def test_guest_cannot_enroll(self):
        r = self.client.post("/api/enrollments/", {"course": self.db.id})
        self.assertIn(r.status_code, (401, 403))

    def test_teacher_cannot_enroll(self):
        self.client.force_authenticate(self.marat)
        r = self.client.post("/api/enrollments/", {"course": self.math.id})
        self.assertEqual(r.status_code, 400)

    def test_student_sees_only_own_enrollments(self):
        Enrollment.objects.create(student=self.student, course=self.db)
        Enrollment.objects.create(student=self.other_student, course=self.math)
        self.client.force_authenticate(self.student)
        self.assertEqual(len(self.client.get("/api/enrollments/").json()), 1)

    def test_student_unenrolls(self):
        e = Enrollment.objects.create(student=self.student, course=self.db)
        self.client.force_authenticate(self.student)
        r = self.client.delete(f"/api/enrollments/{e.id}/")
        self.assertEqual(r.status_code, 204)


class GradesLessonsStatsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user("admin1", password="x", role="admin")
        self.marat = User.objects.create_user("marat", password="x", role="teacher")
        self.gulnar = User.objects.create_user("gulnar", password="x", role="teacher")
        self.student = User.objects.create_user("aruzhan", password="x", role="student")
        self.other_student = User.objects.create_user("timur", password="x", role="student")

        self.db = Course.objects.create(code="CS101", title="Databases", teacher=self.marat)
        self.math = Course.objects.create(code="MATH101", title="Discrete Math", teacher=self.gulnar)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.db)

    # grades

    def test_teacher_sets_grade(self):
        self.client.force_authenticate(self.marat)
        r = self.client.patch(f"/api/enrollments/{self.enrollment.id}/grade/", {"grade": "a"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["grade"], "A")

    def test_wrong_grade(self):
        self.client.force_authenticate(self.marat)
        r = self.client.patch(f"/api/enrollments/{self.enrollment.id}/grade/", {"grade": "Z"})
        self.assertEqual(r.status_code, 400)

    def test_student_cannot_set_grade(self):
        self.client.force_authenticate(self.student)
        r = self.client.patch(f"/api/enrollments/{self.enrollment.id}/grade/", {"grade": "A"})
        self.assertEqual(r.status_code, 403)

    def test_other_teacher_cannot_set_grade(self):
        self.client.force_authenticate(self.gulnar)
        r = self.client.patch(f"/api/enrollments/{self.enrollment.id}/grade/", {"grade": "A"})
        self.assertEqual(r.status_code, 404)  # he doesn't even see this enrollment

    # my courses

    def test_my_courses(self):
        self.enrollment.grade = "B"
        self.enrollment.save()
        self.client.force_authenticate(self.student)
        data = self.client.get("/api/my-courses/").json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "CS101")
        self.assertEqual(data[0]["grade"], "B")

    # lessons and assignments

    def test_teacher_adds_lesson(self):
        self.client.force_authenticate(self.marat)
        r = self.client.post("/api/lessons/", {"course": self.db.id, "title": "Intro"})
        self.assertEqual(r.status_code, 201)

    def test_teacher_cannot_add_lesson_to_other_course(self):
        self.client.force_authenticate(self.marat)
        r = self.client.post("/api/lessons/", {"course": self.math.id, "title": "Intro"})
        self.assertEqual(r.status_code, 400)

    def test_student_cannot_add_lesson(self):
        self.client.force_authenticate(self.student)
        r = self.client.post("/api/lessons/", {"course": self.db.id, "title": "Intro"})
        self.assertEqual(r.status_code, 403)

    def test_student_sees_lessons_only_of_enrolled_courses(self):
        Lesson.objects.create(course=self.db, title="L1")
        Lesson.objects.create(course=self.math, title="L2")
        self.client.force_authenticate(self.student)
        data = self.client.get("/api/lessons/").json()
        self.assertEqual([l["title"] for l in data], ["L1"])

    def test_teacher_adds_assignment(self):
        self.client.force_authenticate(self.marat)
        r = self.client.post("/api/assignments/", {"course": self.db.id, "title": "ERD",
                                                   "due_date": "2026-12-01"})
        self.assertEqual(r.status_code, 201)

    # submissions

    def test_student_submits_once(self):
        a = Assignment.objects.create(course=self.db, title="ERD")
        self.client.force_authenticate(self.student)
        r = self.client.post("/api/submissions/", {"assignment": a.id, "answer": "my erd"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/submissions/", {"assignment": a.id, "answer": "again"})
        self.assertEqual(r.status_code, 400)

    def test_not_enrolled_student_cannot_submit(self):
        a = Assignment.objects.create(course=self.db, title="ERD")
        self.client.force_authenticate(self.other_student)
        r = self.client.post("/api/submissions/", {"assignment": a.id, "answer": "x"})
        self.assertEqual(r.status_code, 400)

    def test_teacher_sets_score(self):
        a = Assignment.objects.create(course=self.db, title="ERD", max_score=100)
        s = Submission.objects.create(assignment=a, student=self.student, answer="x")
        self.client.force_authenticate(self.marat)
        r = self.client.patch(f"/api/submissions/{s.id}/score/", {"score": 90})
        self.assertEqual(r.json()["score"], 90)
        r = self.client.patch(f"/api/submissions/{s.id}/score/", {"score": 150})
        self.assertEqual(r.status_code, 400)

    # stats

    def test_stats_for_admin(self):
        self.enrollment.grade = "A"
        self.enrollment.save()
        Enrollment.objects.create(student=self.other_student, course=self.db, grade="C")
        self.client.force_authenticate(self.admin)
        data = self.client.get("/api/stats/").json()
        self.assertEqual(data["total_courses"], 2)
        self.assertEqual(data["total_enrollments"], 2)
        self.assertEqual(data["popular_courses"][0]["code"], "CS101")
        self.assertEqual(data["popular_courses"][0]["average_grade"], 3.0)  # (4 + 2) / 2

    def test_stats_closed_for_student(self):
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get("/api/stats/").status_code, 403)
