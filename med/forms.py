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
        if not re.match("^[a-zA-Z ]+$", word) or re.match("^[ ]+$", word):
            raise forms.ValidationError("Word can contain only Latin characters.")
        
        return example
    

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'id': 'id_username'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput())
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username


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


class TextForm(forms.ModelForm):
    class Meta:
        model = ReadingText
        fields = ['title', 'eng_level', 'content', 'words_with_translations', 'auth', 'is_auth_a']
        labels = {
            'title': 'Title',
            'eng_level': 'English level',
            'content': 'Text',
            'words_with_translations': 'Words with translations',
            'auth': 'Author',
            'is_auth_a': 'Author is a link'
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'eng_level': forms.Select(attrs={'class': 'form-select'}),
            'words_with_translations': forms.Textarea(),
            'is_auth_a': forms.CheckboxInput()
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eng_level'].initial = 'A1' 

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

class WordsShowForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['words_num_in_prof', 'what_type_show', 'access_dictionary']
        labels = {
            'words_num_in_prof': 'Number of words in profile',
            'what_type_show': 'What type of words to show',
            'access_dictionary': 'Who can see your dictionary'
        }
        widgets = {
            'words_num_in_prof': forms.Select(attrs={'class': 'form-select'}),
            'what_type_show': forms.Select(attrs={'class': 'form-select'}),
            'access_dictionary': forms.Select(attrs={'class': 'form-select'})
        }

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