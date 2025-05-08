from django import forms
from ..models import User

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '@' in username:
            raise forms.ValidationError("Username cannot contain '@'.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken, please choose another one!")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not '@' in email:
            raise forms.ValidationError("Email must include '@'.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already taken, please choose another one or login!")
        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
            
        return cleaned_data

class LoginForm(forms.Form):
    user_username_mail = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)

    def clean(self):
        cleaned_data = super().clean()
        
        return cleaned_data

class AddUsernameForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '@' in username:
            raise forms.ValidationError("Username cannot contain '@'.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken, please choose another one!")
        return username

    def clean(self):
        cleaned_data = super().clean()
        
        return cleaned_data