from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_booking_confirmation_email(user_email, booking_id):
    subject = "Booking Confirmation"
    message = f"Your booking with ID {booking_id} has been successfully created!"
    send_mail(
        subject,
        message,
        "noreply@alxtravelapp.com",
        [user_email],
        fail_silently=False,
    )

