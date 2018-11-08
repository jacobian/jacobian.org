from django.db import models
from django_postgres_unlimited_varchar import UnlimitedCharField

class Presentation(models.Model):
    title = UnlimitedCharField()


