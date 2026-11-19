from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from courses.models import Assignment, Course, Enrollment, Lesson, Submission

User = get_user_model()
PASSWORD = "password123"

# test data updated with weights and scores
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
# Курсы с весами (code, title, credits, teacher_username, midterm_weight, final_weight)
COURSES = [
    ("CS101", "Databases", 5, "marat", "0.60", "0.40"),
    ("CS102", "Web Programming", 5, "marat", "0.50", "0.50"),
    ("MATH101", "Discrete Math", 4, "gulnar", "0.60", "0.40"),
    ("ENG101", "Academic English", 3, "john", "0.70", "0.30"),
]
# Записи студентов с баллами за Midterm и Final (от 0 до 100) и буквенной оценкой
ENROLLMENTS = [
    ("aruzhan", "CS101", 85.50, 90.00, "А"),
    ("aruzhan", "MATH101", 78.00, 82.50, "B"),
    ("daniyar", "CS101", 70.00, 75.00, "B"),
    ("daniyar", "ENG101", 92.00, 95.00, "A"),
    ("aliya", "CS102", 0.00, 0.00, None),
    ("timur", "CS101", 60.00, 65.00, "C"),
    ("timur", "MATH101", 0.00, 0.00, None),
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
# graded works for my-standing demo (aruzhan CS101 avg = 80)
SUBMISSIONS = [
    ("aruzhan", "Draw an ERD", 85),
    ("aruzhan", "Write 5 SQL queries", 75),
    ("aruzhan", "Logic homework", 60),
    ("timur", "Draw an ERD", 55),
]


class Command(BaseCommand):
    help = "fill db with test data including course weights and student scores"

    def handle(self, *args, **options):
        for role, people in [("teacher", TEACHERS), ("student", STUDENTS)]:
            for username, first, last in people:
                if not User.objects.filter(username=username).exists():
                    User.objects.create_user(
                        username=username, password=PASSWORD, role=role,
                        first_name=first, last_name=last
                    )

        for code, title, credits, teacher, m_weight, f_weight in COURSES:
            Course.objects.get_or_create(
                code=code,
                defaults={
                    "title": title,
                    "credits": credits,
                    "teacher": User.objects.get(username=teacher),
                    "midterm_weight": m_weight,
                    "final_weight": f_weight,
                },
            )

        for student, code, m_score, f_score, grade in ENROLLMENTS:
            Enrollment.objects.get_or_create(
                student=User.objects.get(username=student),
                course=Course.objects.get(code=code),
                defaults={
                    "midterm_score": m_score,
                    "final_score": f_score,
                    "grade": grade,
                },
            )

        # small limit for demo: CS102 has 1 student, so it is full
        Course.objects.filter(code="CS102").update(max_students=1)

        for code, order, title in LESSONS:
            Lesson.objects.get_or_create(
                course=Course.objects.get(code=code),
                order=order,
                defaults={"title": title}
            )

        for code, title, due_date in ASSIGNMENTS:
            Assignment.objects.get_or_create(
                course=Course.objects.get(code=code),
                title=title,
                defaults={"due_date": due_date}
            )
        self.stdout.write(self.style.SUCCESS("Done! Test data with weights and scores loaded. Password for all users: " + PASSWORD))

