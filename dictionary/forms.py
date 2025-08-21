import re

from django import forms
from .models import Word, WordGroup

class AddWordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ['word', 'translation', 'example', 'word_type']
        labels = {
            'word': 'Word',
            'translation': 'Translation',
            'example': 'Example',
            'word_type': 'Word type'
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
        if not re.match("^[a-zA-Z ']+$", word) or re.match("^[ ]+$", word):
            raise forms.ValidationError("Word can contain only Latin characters.")
        
        return example
    

class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ['word', 'translation', 'example', 'word_type']
        labels = {
            'word': 'Word',
            'translation': 'Translation',
            'example': 'Example',
            'word_type': 'Word type'
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