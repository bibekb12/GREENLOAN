from django.db import models
from greenloan import settings
from loans.models import Repayment

User = settings.AUTH_USER_MODEL
# Create your models here.
class EsewaPayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="esewa_payment")
    application = models.ForeignKey("loans.Application", on_delete=models.CASCADE, related_name="esewa_payments", null=True, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    product_code = models.CharField(max_length=50)
    transaction_uuid = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=(("PENDING","Pending"),("SUCCESS","Success"),("FAILURE","Failure"),), default="PENDING",)
    ref_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_uuid} - {self.status}"
    
class Payment(models.Model):
    PAYMENT_METHODS = (
        ("esewa", "eSewa"),
        ("qrpayment", "QR Payment"),
        ("bank", "Bank Transfer"),
        ("cash", "Cash"),
        ("card", "Card"),
    )

    repayment = models.ForeignKey(
        Repayment,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.repayment.id} - {self.amount}"

    