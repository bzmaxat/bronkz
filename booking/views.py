from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import datetime, timedelta

from .models import Place, Booking, BookingStatus
from .serializers import PlaceSerializer, BookingSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'], url_path='available-times')
    def available_times(self, request, pk=None):
        """
        Возвращает доступные тайм-слоты для конкретного объекта на указанную дату.
        Пример: /api/places/1/available-times/?date=2025-06-01
        """
        place = self.get_object()
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "Параметр 'date' обязателен в формате YYYY-MM-DD"}, status=400)

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Неверный формат даты"}, status=400)

        duration = timedelta(minutes=place.slot_duration)
        slots = []
        current = datetime.combine(date, place.open_time)
        end = datetime.combine(date, place.close_time)

        while current + duration <= end:
            start_time = current.time()
            end_time = (current + duration).time()

            overlapping = Booking.objects.filter(
                place=place,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).count()

            available = overlapping < place.capacity
            slots.append({
                'start_time': start_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'availabe': available,
                'current_bookings': overlapping,
                'max_capacity': place.capacity
            })

            current += duration

        return Response(slots)

    @action(detail=False, methods=['get'], url_path='available')
    def available(self, request):
        date_str = request.query_params.get('date')
        time_str = request.query_params.get('time')

        if not date_str:
            return Response({"error": "Параметр 'date' обязателен в формате YYYY-MM-DD"}, status=400)

        if not time_str:
            return Response({"error": "Параметр 'time' обязателен в формате HH-MM"}, status=400)

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Неверный формат даты"}, status=400)

        try:
            time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return Response({"error": "Неверный формат времени"}, status=400)
        available_places = []

        for place in Place.objects.filter(open_time__lte=time, close_time__gt=time):
            bookings = Booking.objects.filter(
                place=place,
                date=date,
                start_time__lte=time,
                end_time__gt=time,
                status__in=Booking.get_active_statuses()
            )

            if bookings.count() < place.capacity:
                available_places.append(place)

        if not available_places:
            return Response([], status=200)

        return Response(PlaceSerializer(available_places, many=True).data)


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.user != request.user:
             return Response({"detail": "Нет доступа"}, status=403)

        if booking.status == BookingStatus.CANCELLED:
            return Response({"detail": "Уже отменена"}, status=400)

        if booking.status == BookingStatus.COMPLETED:
            return Response({"detail": "Бронь уже завершена"}, status=400)

        booking.status = BookingStatus.CANCELLED
        booking.save()
        return Response({"detail": "Бронь отменена"}, status=200)

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        bookings = self.get_queryset()

        data = {}
        for value, label in BookingStatus.choices:
            booking_by_status = bookings.filter(status=value)
            serializer = BookingSerializer(booking_by_status, many=True)
            data[value] = serializer.data
        return Response(data)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        booking = self.get_object()

        if not request.user.is_staff:
            return Response({"detail": "Нет прав"}, status=403)

        if booking.status != BookingStatus.PENDING:
            return Response({"detail": "Бронь не может быть подтверждена в текущем статусе"}, status=400)

        booking.status = BookingStatus.CONFIRMED
        booking.save()

        return Response({"detail": "Бронь подтверждена"}, status=200)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        booking = self.get_object()

        if not request.user.is_staff:
            return Response({"detail": "Нет прав"}, status=403)

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            return Response({"detail": "Бронь не может быть подтверждена в текущем статусе"}, status=400)

        booking.status = BookingStatus.COMPLETED
        booking.save()

        return Response({"detail": "Бронь завершена"}, status=200)




