from django.db import models
from med.models import WordGroup

class ReadingText(models.Model):
    ENG_LEVEL_CHOICES = [
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
        ('C2', 'C2')
    ]
    
    title = models.CharField(max_length=100)
    time_to_read = models.IntegerField()
    word_count = models.IntegerField()
    eng_level = models.CharField(max_length=2, choices=ENG_LEVEL_CHOICES, default='A1')
    content = models.TextField(blank=True)
    words_with_translations = models.JSONField(default=dict, blank=True, null=True)
    auth = models.CharField(max_length=200, blank=True)
    is_auth_a = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['eng_level', 'word_count', 'title']
        indexes = [
            models.Index(fields=['eng_level', 'title'])
        ]


class CommunityGroup(models.Model):
    group = models.OneToOneField(WordGroup, on_delete=models.CASCADE)
    state = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('added', 'Added')], default='public')

    def __str__(self):
        return self.group.name
    
    class Meta:
        ordering = ['group__name']
        indexes = [
            models.Index(fields=['group'])
        ]