from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from courses.models import Course, Enrollment

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

        self.stdout.write("done, password for all users: " + PASSWORD)
