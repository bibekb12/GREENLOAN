from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleAdminCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}), label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Confirm password",
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")
        labels = {
            "first_name": "Admin first name",
            "last_name": "Admin last name",
            "email": "Admin email",
            "phone": "Admin phone no",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords don't match")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("Email is required")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        user.full_name = f"{user.first_name} {user.last_name}"
        if commit:
            user.save()
        return user
