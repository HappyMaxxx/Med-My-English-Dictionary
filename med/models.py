from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Word(models.Model):
    word = models.CharField(max_length=100)
    translation = models.CharField(max_length=100)
    example = models.TextField(blank=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'])
        ]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.user.username
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/med/img/base/default_avatar.png'
    
    def save(self, *args, **kwargs):
        if self.avatar and not self._state.adding:  
            extension = self.avatar.name.split('.')[-1]
            new_name = f"{self.user.username}_{now().strftime('%Y%m%d%H%M%S')}_{self.user.id}.{extension}"

            self.avatar.name = new_name
        
        super().save(*args, **kwargs)