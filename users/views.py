from datetime import datetime, timedelta

from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from rest_framework import views
from rest_framework import viewsets
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .serializers import UserRegistrationSerializer, UserPublicSerializer, UserUpdateSerializer
from users.models import CustomUser
from booking.models import Booking, BookingStatus


class RegisterView(views.APIView):
    serializer_class = UserRegistrationSerializer

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            data = UserPublicSerializer(user).data
            return Response(data, status=201)
        return Response(serializer.errors, status=400)


class ConfirmEmailView(views.APIView):
    def get(self, request):
        uid = request.GET.get('uid')
        token = request.GET.get('token')

        try:
            user_id = int(urlsafe_base64_decode(uid).decode())
            user = CustomUser.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Http404("Пользователь не найден")

        confirm = default_token_generator.check_token(user, token)
        if confirm:
            user.is_active = True
            user.save()
            return Response({"detail": "Email подтвержден"}, status=200)

        return Response({"detail": "Неверная или устаревшая ссылка подтверждения"}, status=400)


class UserViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        user = request.user

        if request.method == 'GET':
            data = UserPublicSerializer(user).data
            bookings = Booking.objects.filter(user=user)
            data['total_bookings'] = bookings.count()
            data['completed_bookings'] = bookings.filter(status=BookingStatus.COMPLETED).count()
            return Response(data, status=200)

        elif request.method == 'PATCH':
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(UserPublicSerializer(user).data)

    @action(detail=False, methods=['get'], url_path='me/stats')
    def stats(self, request):
        user = request.user
        data = {}

        period = request.query_params.get('period')
        from_date_str = request.query_params.get('from')
        to_date_str = request.query_params.get('to')

        valid_periods = ['week', 'month', 'year']
        if period and period not in valid_periods:
            return Response({"error": "Неверное значение параметра 'period'"}, status=400)

        total_completed = Booking.objects.filter(user=user, status=BookingStatus.COMPLETED)

        from_date = to_date = None
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return Response({"error": "Неверный формат даты"}, status=400)

        qs = Booking.objects.filter(user=user, status=BookingStatus.COMPLETED)

        if from_date and to_date:
            data["completed_between"] = qs.filter(date__gte=from_date, date__lte=to_date).count()

        now = datetime.now().date()
        period_counts = {
            "week": qs.filter(date__gte=now - timedelta(days=7)).count(),
            "month": qs.filter(date__gte=now - timedelta(days=30)).count(),
            "year": qs.filter(date__gte=now - timedelta(days=365)).count()
        }

        if period:
            data[period] = period_counts[period]
        else:
            data.update(period_counts)

        data["total_completed"] = total_completed.count()
        data["unique_places_visited"] = qs.values("place").distinct().count()

        return Response(data, status=200)


