from django.shortcuts import render
import os
import requests
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
from .tasks import send_booking_confirmation_email

class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing listings.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def perform_create(self, serializer):
        booking = serializer.save()
        user_email = booking.user.email if hasattr(booking, "user") else "test@example.com"
        send_booking_confirmation_email.delay(user_email, booking.id)


# Payment Integration (Chapa API)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for initiating payments via the Chapa API.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        """
        Initiate payment through Chapa API when a booking is made.
        """
        booking_id = request.data.get('booking')
        amount = request.data.get('amount')

        if not booking_id or not amount:
            return Response(
                {"error": "Both 'booking' and 'amount' fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        # Unique transaction reference
        tx_ref = f"TX-{booking_id}-{os.urandom(4).hex()}"

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "amount": str(amount),
            "currency": "ETB",
            "email": f"{booking.guest_name.lower().replace(' ', '')}@example.com",
            "first_name": booking.guest_name,
            "tx_ref": tx_ref,
            "callback_url": "http://localhost:8000/api/verify-payment/",
        }

        # Make API call to Chapa
        response = requests.post(
            "https://api.chapa.co/v1/transaction/initialize",
            headers=headers,
            json=data
        )
        resp_data = response.json()

        if response.status_code == 200 and resp_data.get("status") == "success":
            # Save payment record
            Payment.objects.create(
                booking=booking,
                transaction_id=tx_ref,
                amount=amount,
                status='Pending'
            )
            return Response(resp_data, status=status.HTTP_201_CREATED)
        else:
            return Response(resp_data, status=status.HTTP_400_BAD_REQUEST)


class VerifyPaymentViewSet(viewsets.ViewSet):
    """
    ViewSet for verifying payment status with Chapa.
    """
    def retrieve(self, request, pk=None):
        """
        Verify a payment using its transaction ID.
        """
        try:
            payment = Payment.objects.get(transaction_id=pk)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
        verify_url = f"https://api.chapa.co/v1/transaction/verify/{payment.transaction_id}"

        response = requests.get(verify_url, headers=headers)
        resp_data = response.json()

        if response.status_code == 200 and resp_data.get("status") == "success":
            payment.status = "Completed"
        else:
            payment.status = "Failed"

        payment.save()
        return Response(PaymentSerializer(payment).data)

