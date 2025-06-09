from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings


class PlaceCategory(models.TextChoices):
    GYM = 'gym', 'Тренажерный зал'
    SPORTS_ARENA = 'arena', 'Аренда спортивных площадок'
    EQUIPMENT_RENTAL = 'equipment', 'Аренда снаряжения'
    POOL = 'poll', 'Бассейн'
    SAUNA = 'sauna', 'Сайна'
    OTHER = 'other', 'Другое'


class Place(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='places/', null=True, blank=True)
    open_time = models.TimeField()
    close_time = models.TimeField()
    slot_duration = models.PositiveIntegerField(help_text='Slot duration in minutes', default=60)
    capacity = models.PositiveIntegerField(default=1)

    category = models.CharField(
        max_length=20,
        choices=PlaceCategory.choices,
        default=PlaceCategory.OTHER
    )

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Ожидает подтверждения'
    CONFIRMED = 'confirmed', 'Подтверждено'
    COMPLETED = 'completed', 'Завершено'
    CANCELLED = 'cancelled', 'Отменено'


class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )

    @classmethod
    def get_active_statuses(cls):
        return [BookingStatus.PENDING, BookingStatus.CONFIRMED]

    @classmethod
    def get_closed_statuses(cls):
        return [BookingStatus.CANCELLED, BookingStatus.COMPLETED]

    class Meta:
        ordering = ['-date', 'start_time']

    def __str__(self):
        return f"{self.user.username} - {self.place.name} | {self.date} | ({self.start_time}-{self.end_time})"

    def clean(self):
        if self.status in Booking.get_closed_statuses():
            return

        if self.start_time < self.place.open_time or self.end_time > self.place.close_time:
            raise ValidationError("Время бронирования вне рабочего времени объекта.")

        if self.start_time >= self.end_time:
            raise ValidationError("Время начала должно быть раньше окончания.")

        overlapping = Booking.objects.filter(
            place=self.place,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        count = overlapping.count()

        if count >= self.place.capacity:
            raise ValidationError("В это время уже забронировано максимальное количество человек.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
