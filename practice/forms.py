from django import forms
from .models import ReadingText

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
    
    eng_level = forms.ChoiceField(
        choices=[(choice[0], choice[1]) for choice in ReadingText.ENG_LEVEL_CHOICES],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )