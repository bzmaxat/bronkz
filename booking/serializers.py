from rest_framework import serializers
from datetime import datetime, timedelta

from .models import Booking, Place, BookingStatus
from .utils import get_time_slots


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('user',)

    def validate(self, data):
        place = data['place']
        start = data['start_time']
        end = data['end_time']
        date = data['date']

        if start < place.open_time or end > place.close_time:
            raise serializers.ValidationError("Время бронирования вне рабочего времени объекта.")

        if start >= end:
            raise serializers.ValidationError("Время начала должно быть раньше времени окончания")

        duration = datetime.combine(date, end) - datetime.combine(date, start)
        if duration != timedelta(minutes=place.slot_duration):
            raise serializers.ValidationError("Продолжительность бронирования должна быть равна продолжительности слота")

        slots = get_time_slots(place, date)
        if (start, end) not in slots:
            raise serializers.ValidationError("Выбранное время не соответствует доступным слотам.")

        overlapping = Booking.objects.filter(
            place=place,
            date=date,
            start_time__lt=end,
            end_time__gt=start,
        )

        if self.instance:
            overlapping = overlapping.exclude(id=self.instance.id).filter(status__in=Booking.get_active_statuses())

        if overlapping.count() >= place.capacity:
            raise serializers.ValidationError("Максимальное количество бронирований на это время уже достигнуто.")

        return data


class PlaceSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Place
        fields = '__all__'


class PlaceManagerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['open_time', 'close_time', 'slot_duration', 'capacity']
