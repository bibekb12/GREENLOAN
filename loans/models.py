from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords

from accounts.models import User


class LoanTypes(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Interest rate in percentage"
    )
    amount_limit = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Maximum loan amount"
    )
    required_documents = models.JSONField(
        default=list, help_text="List of required document types"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Loan Type"
        verbose_name_plural = "Loan Types"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - Interest rate({self.interest_rate})" 

    def clean(self):
        """Validate required documents"""
        if not isinstance(self.required_documents, list):
            raise ValidationError("Required documents must be a list")

        valid_docs = [choice[0] for choice in Document.DOCUMENT_TYPES]
        for doc in self.required_documents:
            if doc not in valid_docs:
                raise ValidationError(f"Invalid document type: {doc}")
    
    history = HistoricalRecords()


class Application(models.Model):
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("info_requested", "Info Requested"),
        ("info_provided", "Info Provided"),
        ("documents_verified", "Documents Verified"),
        ("salary_verified", "Salary Verified"),
        ("proposal_approved", "Proposal Approved"),
        ("final_review", "Final Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    loan_type = models.ForeignKey(LoanTypes, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField()
    purpose = models.TextField()
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2)
    address = models.TextField()
    citizenship_number = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="submitted"
    )
    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_applications",
    )
    status_history = models.JSONField(default=list)
    comments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application {self.id} - {self.applicant.username}"

    def clean(self):
        """Validate application data"""
        if self.amount > self.loan_type.amount_limit:
            raise ValidationError(
                f"Loan amount exceeds limit of {self.loan_type.amount_limit}"
            )

        if self.amount <= 0:
            raise ValidationError("Loan amount must be positive")

    def add_status_history(self, status, user, note=""):
        """Add entry to status history"""
        from django.utils import timezone

        self.status_history.append(
            {
                "status": status,
                "user": user.get_username(),
                "user_id": user.id,
                "timestamp": timezone.now().isoformat(),
                "note": note,
            }
        )
        self.save(update_fields=["status_history"])
    
    history = HistoricalRecords()


class Document(models.Model):
    DOCUMENT_TYPES = [
        ("citizenship_front", "Citizenship Certificate (Front)"),
        ("citizenship_back", "Citizenship Certificate (Back)"),
        ("salary_slip", "Salary Slips"),
        ("bank_statement", "Bank Statements"),
        ("business_registration", "Business Registration"),
        ("property_document", "Property Documents"),
        ("admission_letter", "Admission Letter"),
        ("id_proof", "ID Proof"),
    ]

    VERIFICATION_STATUS = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(
        max_length=50, choices=DOCUMENT_TYPES, default="citizenship_front"
    )
    file = models.FileField(upload_to="documents/")
    verification_status = models.CharField(
        max_length=10, choices=VERIFICATION_STATUS, default="pending"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_additional = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        unique_together = ("application","document_type","verification_status")

class ApprovedLoans(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    principle = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tenure_months = models.IntegerField()
    approved_by = models.ForeignKey(User, on_delete= models.PROTECT)
    approved_at = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ("active", "Active"),
        ("closed","Closed"),
        ("defaulted","Defaulted"),
    ])

    def __str__(self):
        return f"Loan #{self.id}- {self.user.full_name}"
    
    history = HistoricalRecords()
    
class Repayment(models.Model):
    loan = models.ForeignKey(ApprovedLoans, on_delete=models.CASCADE, related_name="repayments")
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("paid", "Paid"),
            ("late", "Late"),
        ],
        default="pending",
    )

    def is_late(self):
        return self.paid_date and self.paid_date > self.due_date
    
    history = HistoricalRecords()

class CreditScore(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.IntegerField(default=300)  # start from 300
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.score}"
    
    history = HistoricalRecords()
    

