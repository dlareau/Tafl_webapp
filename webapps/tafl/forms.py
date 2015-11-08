from django import forms
from django.contrib.auth.models import User

class LoginForm(forms.Form):
    username = forms.CharField(max_length=20)
    password1 = forms.CharField(max_length=200, 
                                label='Password', 
                                widget=forms.PasswordInput())

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=20)
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(max_length=200, 
                                label='Password', 
                                widget=forms.PasswordInput())
    password2 = forms.CharField(max_length=200,
                                label='Confirm Password',
                                widget=forms.PasswordInput())

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()

        pw1 = cleaned_data.get('password1')
        pw2 = cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("passwords don't match")

        return cleaned_data

    def clean_username(self):
        username = cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("username taken")

        return username
