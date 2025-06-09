from django.urls import path, include
from .views import RegisterView, ConfirmEmailView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('confirm-email/', ConfirmEmailView.as_view(), name='confirm-email')
]
