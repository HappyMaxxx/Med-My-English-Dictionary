from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import date
from dictionary.models import Word, WordGroup


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
            return f'/media/avatars/{self.avatar.name.split("/")[-1]}'
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
    def calculate_streak(user):
        words = Word.objects.filter(user=user).order_by('time_create')
        if not words.exists():
            return 0, 0, None, None, None, None, None

        longest_streak = 0
        current_streak = 0
        streak_start_date = None
        streak_end_date = None
        longest_streak_start_date = None
        longest_streak_end_date = None
        ff = None

        unique_dates = set()
        previous_date = None

        for word in words:
            word_date = word.time_create.date()
            if word_date not in unique_dates:
                unique_dates.add(word_date)
                if previous_date and (word_date - previous_date).days == 1:
                    current_streak += 1
                    streak_end_date = word_date
                else:
                    if current_streak > longest_streak:
                        longest_streak = current_streak
                        longest_streak_start_date = streak_start_date
                        longest_streak_end_date = streak_end_date
                    current_streak = 1
                    streak_start_date = word_date
                    streak_end_date = word_date
                previous_date = word_date

        if current_streak > longest_streak:
            longest_streak = current_streak
            longest_streak_start_date = streak_start_date
            longest_streak_end_date = streak_end_date

        last_word_date = words[len(words) - 1].time_create.date()
        today = date.today()
        if (today - last_word_date).days == 1:
            streak_end_date = last_word_date
            ff = 0
        elif last_word_date != today:
            current_streak = 0
            streak_end_date = None
            streak_start_date = None
        
        if words[len(words)-1].time_create.date() == today:
            ff = 1

        return current_streak, longest_streak, streak_start_date, streak_end_date, longest_streak_start_date, longest_streak_end_date, ff

    @staticmethod
    def format_date_range(start_date, end_date):
        if start_date and end_date:
            if start_date == end_date:
                return start_date.strftime("%b %d, %Y")
            return start_date.strftime("%b %d, %Y") + " - " + end_date.strftime("%b %d, %Y")
        return 0


class UserLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logins')
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    

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


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    time_create = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=[
        ('1', 'Base'),
        ('2', 'Group_r'),
    ], default='1')
    group = models.ForeignKey(WordGroup, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.message}"
    
    class Meta:
        ordering = ['-time_create']
        indexes = [
            models.Index(fields=['-time_create'])
        ]


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