# Веса по умолчанию — Decimal("0.60") / Decimal("0.40") вместо float 0.6 / 0.4.
# float 0.6 превращается в 0.59999999..., и full_clean() в Course.save()
# отклонял курс: «Ensure that there are no more than 2 decimal places».

import decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0007_course_prerequisites_waitlist"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="midterm_weight",
            field=models.DecimalField(
                decimal_places=2,
                default=decimal.Decimal("0.60"),
                max_digits=3,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)],
                verbose_name="Вес Midterm",
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="final_weight",
            field=models.DecimalField(
                decimal_places=2,
                default=decimal.Decimal("0.40"),
                max_digits=3,
                validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)],
                verbose_name="Вес Final",
            ),
        ),
    ]
