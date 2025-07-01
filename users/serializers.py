from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from .models import CustomUser
from .tasks import send_activation_email


class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = f"http://localhost:8000/api/users/confirm-email/?uid={uid}&token={token}"
        print(link)

        send_activation_email.delay(
            user.email,
            subject='Подтверждение регистрации',
            message=f'Перейдите по ссылке для подтверждения: {link}'
        )

        return user

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value):
            raise serializers.ValidationError("Имя пользователя уже занято.")
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value):
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role')


class UserUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=50, required=False)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)

        new_email = validated_data.get('email')
        if new_email and new_email != instance.email:
            instance.email = new_email
            instance.is_active = False
            instance.save()

            uid = urlsafe_base64_encode(force_bytes(instance.pk))
            token = default_token_generator.make_token(instance)
            link = f"http://localhost:8000/api/users/confirm-email/?uid={uid}&token={token}"
            print(link)

            send_activation_email.delay(
                instance.email,
                subject='Подтверждение email',
                message=f'Перейдите по ссылке для подтверждения: {link}'
            )
        else:
            instance.save()
        return instance

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Имя пользователя уже занято.")
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']
        read_only_fields = ('role',)
