from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from med.models import UserProfile, UserStreak
from dictionary.models import Word

@receiver(post_save, sender=User)
def create_user_profile_streak(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        UserStreak.objects.create(user=instance)

@receiver(post_save, sender=Word)
def update_user_streak(sender, instance, created, **kwargs):
    if not created:
        return

    streak, _ = UserStreak.objects.get_or_create(user=instance.user)
    streak.update_streak(activity_date=instance.time_create.date())