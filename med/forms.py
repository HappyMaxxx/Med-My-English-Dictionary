from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import *
    

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound and not self.is_valid():
            self.data = self.data.copy() 
            self.data['password1'] = ''  
            self.data['password2'] = '' 


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Username', widget=forms.TextInput())
    password = forms.CharField(label='Password', widget=forms.PasswordInput())
    

class EditProfileForm(forms.ModelForm):
    # email = forms.EmailField(label='Email', widget=forms.EmailInput())
    first_name = forms.CharField(label='First Name', required=False, widget=forms.TextInput())
    last_name = forms.CharField(label='Last Name', required=False, widget=forms.TextInput())

    class Meta:
        model = User
        # fields = ['email', 'first_name', 'last_name']
        fields = ['first_name', 'last_name']

class WordsShowForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['words_num_in_prof', 'what_type_show', 'access_dictionary', 'show_word_stats']
        labels = {
            'words_num_in_prof': 'Number of words in profile',
            'what_type_show': 'What type of words to show',
            'access_dictionary': 'Who can see your dictionary',
            'show_word_stats': 'Who can see your word statistics'
        }
        widgets = {
            'words_num_in_prof': forms.Select(attrs={'class': 'form-select'}),
            'what_type_show': forms.Select(attrs={'class': 'form-select'}),
            'access_dictionary': forms.Select(attrs={'class': 'form-select'}),
            'show_word_stats': forms.Select(attrs={'class': 'form-select'})
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