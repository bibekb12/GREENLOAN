from django import forms
from .models import KYCVerification


class KYCVerificationForm(forms.ModelForm):
    class Meta:
        model = KYCVerification
        fields = ['citizenship', 'selfie']

        widgets = {
            'citizenship': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'selfie': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }