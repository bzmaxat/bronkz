import pytest
from datetime import datetime, timedelta, time

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from booking.models import Booking, BookingStatus, Place
from booking.tasks import auto_complete_bookings


class BookingTasksTest(TestCase):
    def test_auto_complete_expired_bookings(self):
        now = timezone.now().replace(microsecond=0, second=0)

        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='1234')

        place = Place.objects.create(
            name="Test Place",
            open_time=time(hour=8, minute=0),
            close_time=time(hour=22, minute=0)
        )

        past_booking = Booking.objects.create(
            user=user,
            place=place,
            date=now.date(),
            start_time=(now - timedelta(hours=2)).time(),
            end_time=(now - timedelta(hours=1)).time(),
            status=BookingStatus.CONFIRMED
        )

        future_booking = Booking.objects.create(
            user=user,
            place=place,
            date=now.date(),
            start_time=(now + timedelta(hours=1)).time(),
            end_time=(now + timedelta(hours=2)).time(),
            status=BookingStatus.PENDING
        )

        auto_complete_bookings()

        past_booking.refresh_from_db()
        future_booking.refresh_from_db()

        self.assertEqual(past_booking.status, BookingStatus.COMPLETED)
        self.assertEqual(future_booking.status, BookingStatus.PENDING)
