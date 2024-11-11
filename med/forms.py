from django import forms
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