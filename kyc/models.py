from django.db import models
from django.conf import settings

class KYCVerification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_verification_attempts', null=True, blank=True)
    citizenship_image = models.ImageField(upload_to='kyc/citizenship/')
    selfie_image = models.ImageField(upload_to='kyc/selfie/')

    verified = models.BooleanField(default=False)
    confidence = models.FloatField(default=0)

    blink_detected = models.BooleanField(default=False)
    left_turn_detected = models.BooleanField(default=False)
    right_turn_detected = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KYC #{self.id}"