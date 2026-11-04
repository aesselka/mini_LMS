from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Course, Enrollment

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
