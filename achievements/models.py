from django.db import models
from django.contrib.auth.models import User

class Achievement(models.Model):
    ACH_TYPE_CHOICES = [
        ('1', 'Words'),
        ('2', 'Groups'),
        ('3', 'Friends'),
        ('4', 'Reading'),
        ('5', 'Interaction'),
        ('6', 'Content Quality'),
        ('7', 'Special')
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    level = models.PositiveIntegerField()
    icon = models.ImageField(upload_to='achievements/', blank=True)
    ach_type = models.CharField(max_length=20, choices=ACH_TYPE_CHOICES)

    def get_icon_url(self):
        if self.icon:
            return f'/media/achievements/{self.icon.name.split("/")[-1]}'
        return self.name

    def __str__(self):
        return f"{self.name} (Level {self.level})"
    

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    time_get = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
    
    class Meta:
        ordering = ['-time_get']
        indexes = [
            models.Index(fields=['-time_get'])
        ]