from django import forms
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import *


class AddWordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ['word', 'translation', 'example']
        labels = {
            'word': 'Word',
            'translation': 'Translation',
            'example': 'Example'
        }
        widgets = {
            'example': forms.Textarea(attrs={'rows': 3})
        }
        required = {
            'example': False
        }

    def clean_example(self):
        example = self.cleaned_data.get('example')
        if len(example) > 1000:
            raise forms.ValidationError('Example is too long, max 1000 characters.')
        
        return example
    

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput())
    email = forms.EmailField(label='Email', widget=forms.EmailInput())
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput())
    password = forms.CharField(label='Password', widget=forms.PasswordInput())


class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ['word', 'translation', 'example']
        labels = {
            'word': 'Word',
            'translation': 'Translation',
            'example': 'Example'
        }
        widgets = {
            'example': forms.Textarea(attrs={'rows': 3})
        }