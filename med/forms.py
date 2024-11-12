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
    
    def clean_example(self):
        example = self.cleaned_data.get('example')
        if len(example) > 1000:
            raise forms.ValidationError('Example is too long, max 1000 characters.')
        
        return example