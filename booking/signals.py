from django.db.models.signals import post_save
from django.dispatch import receiver
from booking.models import Booking, Place
from logs.models import ActivityLog


@receiver(post_save, sender=Booking)
def log_booking_change(sender, instance, created, **kwargs):

    if created:
        ActivityLog.objects.create(
            user=instance.user,
            action='Создал бронь',
            content_object=instance
        )
