from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def send_thankyou_message(sender, instance, created, **kwargs):
    if created:
        send_mail(
            subject="Thank You for Connected with GreenLoan",
            message=f"Hi {instance.full_name },\n\nThank you for creating an account with us!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=True,
        )

def create_default_admin(sender, **kwargs):
    if not User.objects.filter(email='admin@gmail.com').exists():
        User.objects.create_user(
            email='admin@gmail.com',
            password='admin',
            full_name='admin sir',
            first_name='admin',
            last_name='sir',
            phone='9999999999',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
