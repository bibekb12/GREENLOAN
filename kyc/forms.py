from django import forms


class LiveKYCForm(forms.Form):

    live_capture = forms.CharField(
        widget=forms.HiddenInput()
    )