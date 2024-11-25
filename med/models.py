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
    is_favourite = models.BooleanField(default=False)

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
    class Types(models.TextChoices):
        favourite = 'fav', 'Favourite'
        learning = 'learn', 'Learning'

    class NumberWords(models.IntegerChoices):
        five = 5, '5'
        three = 3, '3'
        one = 1, '1'
        zero = 0, '0'

    class WordsType(models.TextChoices):
        everybody = 'every', 'Everybody'
        friends = 'friends', 'Friends'
        only_me = 'only', 'Only me'


    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    words_num_in_prof = models.IntegerField(choices=NumberWords.choices, default=NumberWords.five)
    what_type_show = models.CharField(max_length=10, choices=Types.choices, default=Types.learning)
    access_dictionary = models.CharField(max_length=10, choices=WordsType.choices, default=WordsType.everybody)

    def __str__(self):
        return self.user.username
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/med/img/base/default_avatar.png'
    
    def save(self, *args, **kwargs):
        if not self._state.adding: 
            old_instance = UserProfile.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.avatar != self.avatar:
                if self.avatar:
                    extension = self.avatar.name.split('.')[-1]
                    new_name = f"{self.user.username}_{now().strftime('%Y%m%d%H%M%S')}_{self.user.id}.{extension}"
                    self.avatar.name = new_name

        super().save(*args, **kwargs)


class Friendship(models.Model):
    sender = models.ForeignKey(User, related_name="friendship_requests_sent", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="friendship_requests_received", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')