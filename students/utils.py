
from functools import wraps
import random
import traceback
from django.core.cache import cache
from django.conf import settings
from datetime import datetime
from django.core.mail import send_mail
import logging

from rest_framework import response, status
logger = logging.getLogger(__name__)
 
 
def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return str(random.randint(10**(length-1), (10**length)-1))
 
def store_otp(email, otp, ttl=300):
    """Store OTP in Redis cache with TTL (default 5 min)."""
    cache.set(f"otp:{email}", otp, timeout=ttl)
 
def get_stored_otp(email):
    """Retrieve OTP from Redis."""
    return cache.get(f"otp:{email}")
 
def verify_otp(email, otp):
    """Verify OTP and delete if valid."""
    stored_otp = get_stored_otp(email)
    if stored_otp and stored_otp == otp:
        cache.delete(f"otp:{email}")
        return True
    return False


def send_password_reset(email , reset_link):
    subject = 'Password Reset Request'
    message = f'Click the link below to reset your password:\n{reset_link}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)


def try_except_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log to console/file with full traceback
            logger.error(
                "Unhandled exception in %s: %s",
                func.__name__,
                str(e),
                exc_info=True,
            )
 
            # Optional: also print to terminal if you're running runserver
            traceback.print_exc()
 
            # Return a safe JSON response
            return response(
                {
                    "error": "An internal server error occurred.",
                    "exception": e.__class__.__name__
                    # "details": str(e),  # remove in production if you don’t want to leak info
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return wrapper


import ast
 
 
def flatten_errors(errors):
 
    if isinstance(errors, dict):
 
        field, value = next(iter(errors.items()))
 
        if isinstance(value, list) and value:
 
            message = value[0]
 
            # If the first element is itself a nested dict/list
            # (e.g. per-item errors inside a list field like "items"),
            # recurse instead of stringifying it.
            if isinstance(message, (dict, list)):
                return flatten_errors(message)
 
            if hasattr(message, "string"):
                message = message.string
 
            message = str(message)
 
            if message == "This field is required.":
                return f"{field} field is required."
 
            if message == "This field may not be null.":
                return f"{field} field cannot be null."
 
            if field == "non_field_errors":
                return message
 
            return message
 
        return flatten_errors(value)
 
    if isinstance(errors, list):
 
        if not errors:
            return ""
 
        return flatten_errors(errors[0])
 
    if isinstance(errors, str):
 
        if errors.startswith("{") and errors.endswith("}"):
 
            try:
                parsed = ast.literal_eval(errors)
                return flatten_errors(parsed)
            except Exception:
                pass
 
        return errors
 
    return str(errors)
 
 