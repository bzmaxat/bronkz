from datetime import datetime
from celery import shared_task
from django.db.models import Q
from .models import Booking, BookingStatus


@shared_task
def auto_complete_bookings():
    today = datetime.today().date()
    bookings = Booking.objects.filter(
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
    ).filter(
        Q(date__lt=today) |
        Q(date=today, end_time__lte=datetime.now().time())
    )
    print(f"[Celery] Завершено {bookings.count()} бронирований автоматически.")
    bookings.update(status=BookingStatus.COMPLETED)

