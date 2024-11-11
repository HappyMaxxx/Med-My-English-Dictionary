from django.db import models

class Word(models.Model):
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    example = models.TextField(max_length=1000, blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.word
    
    class Meta:
        ordering = ['-time_create', 'word']
        indexes = [
            models.Index(fields=['-time_create'])
        ]