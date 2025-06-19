from datetime import datetime
from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from .models import Booking, BookingStatus


@shared_task
def auto_complete_bookings():
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    bookings = Booking.objects.filter(
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
    ).filter(
        Q(date__lt=today) |
        Q(date=today, end_time__lte=current_time)
    )
    print(f"[Celery] Завершено {bookings.count()} бронирований автоматически.")
    bookings.update(status=BookingStatus.COMPLETED)

