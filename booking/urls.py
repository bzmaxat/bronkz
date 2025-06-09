from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaceViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'places', PlaceViewSet, basename='place')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]
