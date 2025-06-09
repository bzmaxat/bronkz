from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from rest_framework import views
from rest_framework.response import Response

from .serializers import UserRegistrationSerializer, UserPublicSerializer
from users.models import CustomUser


class RegisterView(views.APIView):
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
