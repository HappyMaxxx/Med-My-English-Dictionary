from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import date

class Word(models.Model):
    TYPE_CHOICES = [
        ('noun', 'Noun'),
        ('verb', 'Verb'),
        ('adjective', 'Adjective'),
        ('adverb', 'Adverb'),
        ('pronoun', 'Pronoun'),
        ('phrasal verb', 'Phrasal verb'),
        ('other', 'Other')
    ]

    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    example = models.TextField(blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_favourite = models.BooleanField(default=False)
    word_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')

    def __str__(self):
        return self.word
    
    class Meta:
        ordering = ['-time_create', 'word']
        indexes = [
            models.Index(fields=['-time_create'])
        ]


class WordGroup(models.Model):
    name = models.CharField(max_length=100)
    words = models.ManyToManyField(Word, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_main = models.BooleanField(verbose_name='main', default=False)
    uses_users = models.ManyToManyField(User, blank=True, related_name='uses_of_group')

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'])
        ]