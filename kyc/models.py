from django.db import models


class KYCVerification(models.Model):
    citizenship = models.ImageField(upload_to='citizenship/')
    selfie = models.ImageField(upload_to='selfies/')

    verified = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"KYC #{self.id}"