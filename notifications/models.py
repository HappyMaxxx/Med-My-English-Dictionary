from django.db import models
from dictionary.models import WordGroup
from django.contrib.auth.models import User

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_set')
    message = models.TextField()
    time_create = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=[
        ('1', 'Base'),
        ('2', 'Group_r'),
        ('3', 'Friend_r'),
    ], default='1')
    group = models.ForeignKey(WordGroup, on_delete=models.CASCADE, blank=True, null=True)
    friendship_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.message}"
    
    class Meta:
        ordering = ['-time_create']
        indexes = [
            models.Index(fields=['-time_create'])
        ]