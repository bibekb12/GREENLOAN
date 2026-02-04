from decimal import Decimal
from django import forms
from loans.models import Application, Document
from core.models import SitePage


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            "loan_type",
            "amount",
            "duration_months",
            "purpose",
            "monthly_income",
            "address",
            "citizenship_number",
        ]
        widgets = {
            "purpose": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "address": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "loan_type": forms.Select(attrs={"class": "form-control"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "duration_months": forms.NumberInput(attrs={"class": "form-control"}),
            "monthly_income": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        """
        The loan amount must not exceed 50% of the declared monthly salary.
        If it does, we fail validation instead of creating an application
        that will immediately be declined.
        """
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        monthly_income = cleaned_data.get("monthly_income")
        site = SitePage.objects.first()

        if amount is not None and monthly_income is not None:
            # Use Decimal for safe comparison
            allow_percent = Decimal(site.allowed_income_percent)/Decimal("100")
            max_allowed = monthly_income * allow_percent 
            if amount > max_allowed:
                raise forms.ValidationError(
                    f"Requested loan amount cannot exceed {site.allowed_income_percent}% of your monthly salary."
                )

        return cleaned_data


class DocumentUploadForm(forms.ModelForm):
    # Single required file per upload – applicant must choose a file
    # every time they submit this form.
    file = forms.FileField(
        required=True, widget=forms.FileInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Document
        fields = ["document_type"]
        widgets = {
            "document_type": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_file(self):
        """
        Enforce that one document file is compulsory for each submission.
        """
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            raise forms.ValidationError("Please upload a document file.")
        return uploaded_file
