from django import forms
from django.contrib.auth.models import User
from tafl.models import *

class LoginForm(forms.Form):
    username = forms.CharField(max_length=20)
    password = forms.CharField(max_length=200, 
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
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("username taken")

        return username

class MessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['text']

class GameForm(forms.Form):
    optradio = forms.CharField(max_length=20)
    ruleset = forms.CharField(max_length=20)
    is_priv = forms.BooleanField(required=False)
    priv_pw = forms.CharField(max_length=200, required=False)
    #priv_pw all cleartext bc it's just limited who can join a game,
    #  not locking anything important
    
    def clean(self):
        cleaned_data = super(GameForm, self).clean()
        isp = cleaned_data.get('is_priv')
        ppw = cleaned_data.get('priv_pw')
        if isp and ppw=="":
            raise forms.ValidationError("must provide password for private game")
        return cleaned_data

class SearchForm(forms.Form):
    search = forms.CharField(max_length=20)
