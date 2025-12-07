from django import forms
from django.contrib.auth.forms import AuthenticationForm

from accounts.models import User

class EmailAuthenticationForm(AuthenticationForm):
    email = forms.EmailField(
        label="EEmail",
        widget=forms.EmailInput(attrs={'autofocus':True,'class':'form-control'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.fields['password'].widget.attrs.update({'class':'form-control'})

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email_iexact = email)
                if user.check_password(password) and user.is_active:
                    self.user_cache = user
                else:
                    raise forms.ValidationError("User doent exits or invalid credential.",code="invalid login")
            except User.DoesNotExist:
                raise forms.ValidationError("invalid email password", code ="invalid login")

        return self.cleaned_data

class SimpleUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}), label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}), label="Confirm password")

    class Meta:
        model = User
        fields = ('first_name','last_name','email','phone')
        widgets = {
            'first_name': forms.TextInput(attrs={'class':'form-control'}),
            'last_name': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Password don't match")
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.full_name = f"{user.first_name}{user.last_name}"
        if commit:
            user.save()
        return user