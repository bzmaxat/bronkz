from django.db import models
from django.contrib.auth.models import AbstractUser


class UserRole(models.TextChoices):
    CLIENT = 'client', 'Клиент'
    MANAGER = 'manager', 'Менеджер зала'


class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CLIENT
    )
