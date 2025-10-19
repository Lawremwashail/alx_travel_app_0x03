from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet, PaymentViewSet, VerifyPaymentViewSet

router = DefaultRouter()
router.register(r'listings', ListingViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'verify-payment', VerifyPaymentViewSet, basename='verify-payment')

urlpatterns = [
    path('', include(router.urls)),
]

