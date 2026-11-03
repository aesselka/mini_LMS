from django.db import models

class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название курса")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.title