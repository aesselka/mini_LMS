from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from courses.models import Assignment, Course, Enrollment, Lesson

User = get_user_model()
PASSWORD = "password123"

# test data from task 9
TEACHERS = [
    ("marat", "Marat", "Akhmetov"),
    ("gulnar", "Gulnar", "Iskakova"),
    ("john", "John", "Smith"),
]
STUDENTS = [
    ("aruzhan", "Aruzhan", "Sadykova"),
    ("daniyar", "Daniyar", "Omarov"),
    ("aliya", "Aliya", "Nurlanova"),
    ("timur", "Timur", "Bekov"),
]
COURSES = [
    ("CS101", "Databases", 5, "marat"),
    ("CS102", "Web Programming", 5, "marat"),
    ("MATH101", "Discrete Math", 4, "gulnar"),
    ("ENG101", "Academic English", 3, "john"),
]
ENROLLMENTS = [
    ("aruzhan", "CS101", "A"),
    ("aruzhan", "MATH101", "B"),
    ("daniyar", "CS101", "B"),
    ("daniyar", "ENG101", "A"),
    ("aliya", "CS102", None),
    ("timur", "CS101", "C"),
    ("timur", "MATH101", None),
]
LESSONS = [
    ("CS101", 1, "Introduction to databases"),
    ("CS101", 2, "SQL basics: SELECT, INSERT"),
    ("CS101", 3, "Keys and relationships"),
    ("CS102", 1, "HTML and CSS"),
    ("MATH101", 1, "Sets and logic"),
]
ASSIGNMENTS = [
    ("CS101", "Draw an ERD", "2026-12-01"),
    ("CS101", "Write 5 SQL queries", "2026-12-10"),
    ("MATH101", "Logic homework", "2026-12-05"),
]


class Command(BaseCommand):
    help = "fill db with test data"

    def handle(self, *args, **options):
        for role, people in [("teacher", TEACHERS), ("student", STUDENTS)]:
            for username, first, last in people:
                if not User.objects.filter(username=username).exists():
                    User.objects.create_user(username, password=PASSWORD, role=role,
                                             first_name=first, last_name=last)

        for code, title, credits, teacher in COURSES:
            Course.objects.get_or_create(code=code, defaults={
                "title": title, "credits": credits,
                "teacher": User.objects.get(username=teacher),
            })

        for student, code, grade in ENROLLMENTS:
            Enrollment.objects.get_or_create(
                student=User.objects.get(username=student),
                course=Course.objects.get(code=code),
                defaults={"grade": grade},
            )

        for code, order, title in LESSONS:
            Lesson.objects.get_or_create(course=Course.objects.get(code=code), order=order,
                                         defaults={"title": title})

        for code, title, due_date in ASSIGNMENTS:
            Assignment.objects.get_or_create(course=Course.objects.get(code=code), title=title,
                                             defaults={"due_date": due_date})

        self.stdout.write("done, password for all users: " + PASSWORD)
