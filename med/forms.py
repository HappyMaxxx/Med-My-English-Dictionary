import re
from django import forms
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
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
        
        word = self.cleaned_data.get('word')
        if not re.match("^[a-zA-Z]+$", word):
            raise forms.ValidationError("Word can contain only Latin characters.")
        
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


class GroupForm(forms.ModelForm):
    class Meta:
        model = WordGroup
        fields = ['name']
        labels = {
            'name': 'Group name',
        }

class EditProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput())
    first_name = forms.CharField(label='First Name', required=False, widget=forms.TextInput())
    last_name = forms.CharField(label='Last Name', required=False, widget=forms.TextInput())

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']

class ChengePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(label='Old password', widget=forms.PasswordInput())
    new_password1 = forms.CharField(label='New password', widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='New password confirmation', widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
        labels = {
            'old_password': 'Old password',
            'new_password1': 'New password',
            'new_password2': 'New password confirmation'
        }