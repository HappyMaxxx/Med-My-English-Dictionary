from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import date, timedelta
import os

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
        EVERYBODY = 'every', 'Everybody'
        FRIENDS = 'friends', 'Friends'
        ONLY_ME = 'only', 'Only me'

    class WordsMore(models.TextChoices):
        EVERYBODY = 'every', 'Everybody'
        FRIENDS = 'friends', 'Friends'
        ONLY_ME = 'only', 'Only me'
        NOBODY = 'nobody', 'Nobody'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    words_num_in_prof = models.IntegerField(choices=NumberWords.choices, default=NumberWords.five)
    what_type_show = models.CharField(max_length=10, choices=Types.choices, default=Types.learning)
    access_dictionary = models.CharField(max_length=10, choices=WordsType.choices, default=WordsType.EVERYBODY)
    show_word_stats = models.CharField(max_length=10, choices=WordsMore.choices, default=WordsMore.EVERYBODY)
    show_pie_chart = models.BooleanField(default=True)
    show_bar_chart = models.BooleanField(default=True)
    show_line_chart = models.BooleanField(default=True)
    charts_order = models.CharField(max_length=30, default='Pie Chart,Bar Chart,Time Line')
    text_read = models.IntegerField(default=0)
    words_added_from_text = models.IntegerField(default=0)
    sent_groups = models.IntegerField(default=0)
    edited_words = models.IntegerField(default=0)

    chenged_order = models.BooleanField(default=False)
    achicment_order = models.CharField(max_length=30, blank=True)

    hide_warning_message = models.BooleanField(default=False)

    is_premium = models.BooleanField(default=False)
    premium_until = models.DateField(null=True, blank=True)

    grouper = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_avatar_url(self):
        if self.avatar:
            filename = self.avatar.name.split("/")[-1]
            media_path = f"avatars/{filename}" 
            file_path = os.path.join(settings.MEDIA_ROOT, media_path) 
            
            if os.path.exists(file_path):
                return f"{settings.MEDIA_URL}{media_path}"
        return '/static/med/img/base/default_avatar.png'
    
    def save(self, *args, **kwargs):
        if not self._state.adding: 
            old_instance = UserProfile.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.avatar != self.avatar:
                if self.avatar:
                    extension = self.avatar.name.split('.')[-1]
                    new_name = f"{self.user.username}_{now().strftime('%Y%m%d%H%M')}_{self.user.id}.{extension}"
                    self.avatar.name = new_name

        super().save(*args, **kwargs)

    @staticmethod
    def format_date_range(start_date, end_date):
        if start_date and end_date:
            if start_date == end_date:
                return start_date.strftime("%b %d, %Y")
            return start_date.strftime("%b %d, %Y") + " - " + end_date.strftime("%b %d, %Y")
        return 0


class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="streak")
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    streak_start_date = models.DateField(null=True, blank=True)
    streak_end_date = models.DateField(null=True, blank=True)

    longest_streak_start_date = models.DateField(null=True, blank=True)
    longest_streak_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} streak"

    def update_streak(self, activity_date=None):
        today = activity_date or date.today()

        if self.last_activity_date == today:
            return

        if self.last_activity_date == today - timedelta(days=1):
            self.current_streak += 1
            self.streak_end_date = today
        else:
            self.current_streak = 1
            self.streak_start_date = today
            self.streak_end_date = today

        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
            self.longest_streak_start_date = self.streak_start_date
            self.longest_streak_end_date = self.streak_end_date

        self.last_activity_date = today
        self.save()
    
    def get_today_status(self):
        today = date.today()

        if self.last_activity_date == today:
            return 1
        elif self.last_activity_date == today - timedelta(days=1):
            return 0
        return None

    def get_streak_data(self):
        return (
            self.current_streak,
            self.longest_streak,
            self.streak_start_date,
            self.streak_end_date,
            self.longest_streak_start_date,
            self.longest_streak_end_date,
            self.get_today_status(),
        )


class UserLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logins')
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Category(models.Model):
    name = models.CharField(max_length=20, unique=True, choices=[
        ('words', 'Words'),
        ('streak', 'Streak'),
        ('logins', 'Logins')
    ])
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Top(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="tops")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.PositiveIntegerField()
    points = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.place}"
    
    class Meta:
        ordering = ['category', 'place']
        indexes = [
            models.Index(fields=['category', 'place']),
        ]