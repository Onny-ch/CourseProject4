from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"autofocus": True})
    )


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Email", widget=forms.EmailInput())

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "country",
            "avatar",
            "password1",
            "password2",
        )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "country", "avatar")
