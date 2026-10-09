from celery import shared_task
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.apps import apps
from .models import Product

@shared_task
def send_otp_email(email, otp):
    subject = "Your SuperAdmin Login OTP"
    message = f"Your OTP is {otp}. It will expire in 5 minutes."
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [email])


@shared_task
def create_scheduled_product():
 
    product = Product.objects.create(
        name="Scheduled Product",
        description="This product was created by Celery Beat.",
        is_active=True,
    )
 
    return f"Product created successfully: {product.id}"