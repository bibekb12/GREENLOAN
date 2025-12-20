from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "class": "form-control"}),
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class SimpleUserCreationForm(forms.ModelForm):
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


class UserProfileForm(forms.ModelForm):  # <-- inherit from forms.ModelForm
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "nationality",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "nationality": forms.TextInput(attrs={"class": "form-control"}),
        }


class KYCUpdateForm(forms.ModelForm):
    citizenship_front = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )
    citizenship_back = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )
    passport_photo = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
    )

    class Meta:
        model = User
        fields = [
            "date_of_birth",
            "gender",
            "nationality",
            "permanent_address",
            "temporary_address",
            "occupation",
            "employer_name",
            "monthly_income",
            "citizenship_number",
            "pan_number",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "nationality": forms.TextInput(attrs={"class": "form-control"}),
            "permanent_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "temporary_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "occupation": forms.TextInput(attrs={"class": "form-control"}),
            "employer_name": forms.TextInput(attrs={"class": "form-control"}),
            "monthly_income": forms.NumberInput(attrs={"class": "form-control"}),
            "citizenship_number": forms.TextInput(attrs={"class": "form-control"}),
            "pan_number": forms.TextInput(attrs={"class": "form-control"}),
        }
