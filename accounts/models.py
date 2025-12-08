from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

"""Preparing for the abstract class for the project"""
class User(AbstractUser):

    #email as username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [] 

    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('loan_officer', 'Loan Officer'),
        ('senior_officer', 'Senior Officer'),
    ]

    APPLICANT_OCCUPATION_CHOICES = [
        ('individual', 'Individual Borrower'),
        ('business_owner', 'Business Owner'),
        ('student', 'Student'),
        ('self_employed', 'Self employed'),
        ('farmer', 'Farmer'),
    ]

    GENDER_CHOICES = [
         ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    username = None
    first_name = models.CharField(_("applicant first name"), max_length=50)
    last_name = models.CharField(_("applicant last name"), max_length=50)
    full_name = models.CharField(_("applicant full name"), max_length=150)
    role = models.CharField(_("applicant role"), max_length=50, choices= ROLE_CHOICES, default='customer')
    email = models.EmailField(_("applicant email"), unique=True)
    phone = models.CharField(_("applicant phone no"), max_length=15, blank=False)
    is_active = models.BooleanField(_("applicant active status"), default=True)


    #for kyc purpose
    date_of_birth = models.DateField(_("applicant date of birth"), auto_now=False, auto_now_add=False, null=True, blank=True)
    gender = models.CharField(_("gender of the applicant"), max_length=50, choices=GENDER_CHOICES, blank=True)
    nationality = models.CharField(_("applicant nation"), max_length=50, default='Nepali')
    permanent_address = models.TextField(_("applicant permanent address"), blank=True)
    temporary_address = models.TextField(_("applicant temporary address"), blank=True)
    occupation = models.CharField(_("applicant occupation"), max_length=50, choices=APPLICANT_OCCUPATION_CHOICES, blank=True)
    employer_name = models.CharField(_("applicant employer if any"), max_length=100, blank=True)
    monthly_income = models.DecimalField(_("applicant income"), max_digits=15, decimal_places=2, null=True, blank=True)
    citizenship_number = models.CharField(_("applicant citizenship number"), max_length=50, blank=True)
    national_id_number = models.CharField(_("applicant national id number"), max_length=50, blank=True)
    pan_number = models.CharField(_("applicant pan number"), max_length=50, blank=True)

    # KYC Status
    kyc_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ], default='pending')
    
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    kyc_verified_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='kyc_verifications'
    )

    #documents
    citizenship_front_url = models.URLField(blank=True)
    citizenship_back_url = models.URLField(blank=True)
    passport_photo_url = models.URLField(blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
