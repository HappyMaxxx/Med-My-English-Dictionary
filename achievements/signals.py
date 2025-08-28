from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db.models import Q, Count
from django.utils.timezone import now, timedelta
from typing import List, Tuple
from .models import UserAchievement, Achievement
from friendship.models import Friendship
from dictionary.models import Word, WordGroup
from practice.models import CommunityGroup
from med.models import UserProfile
from datetime import datetime

import logging

logger = logging.getLogger(__name__)
SITE_LAUNCH_DATE = datetime(2025, 8, 21)

class AchievementProcessor:
    """Handles achievement processing logic for different types."""
    
    THRESHOLDS = {
        '1': [10, 50, 100],  # Words
        '2': [1, 5, 10],     # Word groups
        '3': [5, 20, 50],    # Friends
        '4': [(5, 1), (50, 10), (100, 20)],  # Reading
        '6': [10, 50, 100],  # Words with examples
    }

    @staticmethod
    def process_achievements(user, ach_type: str, thresholds: List):
        """Process achievements for a given type and user."""
        try:
            achievements = Achievement.objects.filter(ach_type=ach_type).order_by('level')
            user_profile = UserProfile.objects.get(user=user)
            current_achievements = UserAchievement.objects.filter(
                user=user,
                achievement__ach_type=ach_type
            )
            current_levels = {ua.achievement.level for ua in current_achievements}

            if ach_type in ['1', '3', '6']:
                item_count = AchievementProcessor._get_item_count(user, ach_type)
                for i, ach in enumerate(achievements):
                    if item_count >= thresholds[i] and ach.level not in current_levels:
                        AchievementProcessor._update_achievement(user, achievements, current_levels, ach.level)

            elif ach_type == '2':
                item_count = AchievementProcessor._get_item_count(user, ach_type)
                for i, ach in enumerate(achievements):
                    if ach.level == 2:
                        groups_with_min_words = WordGroup.objects.filter(
                            user=user, is_main=False
                        ).annotate(
                            word_count=Count('words')
                        ).filter(word_count__gte=5).count()
                        if groups_with_min_words >= 5 and ach.level not in current_levels:
                            AchievementProcessor._update_achievement(user, achievements, current_levels, ach.level)
                    elif item_count >= thresholds[i] and ach.level not in current_levels:
                        AchievementProcessor._update_achievement(user, achievements, current_levels, ach.level)

            elif ach_type == '4':
                text_read, words_added = user_profile.text_read, user_profile.words_added_from_text
                for i, ach in enumerate(achievements):
                    if text_read >= thresholds[i][0] and words_added >= thresholds[i][1] and ach.level not in current_levels:
                        AchievementProcessor._update_achievement(user, achievements, current_levels, ach.level)

        except Exception as e:
            logger.error(f"Error processing achievement type {ach_type} for user {user.id}: {str(e)}")

    @staticmethod
    def _get_item_count(user, ach_type: str) -> int:
        """Get count of items for achievement type."""
        if ach_type == '1':
            return Word.objects.filter(user=user).count()
        elif ach_type == '2':
            return WordGroup.objects.filter(user=user, is_main=False).count()
        elif ach_type == '3':
            return Friendship.objects.filter(
                Q(sender=user, status='accepted') | Q(receiver=user, status='accepted')
            ).count()
        elif ach_type == '6':
            return Word.objects.filter(user=user).exclude(example='').count()
        return 0

    @staticmethod
    def _update_achievement(user, achievements, current_levels: set, target_level: int):
        """Update or create achievement for user."""
        ach = next((a for a in achievements if a.level == target_level), None)
        if ach and not any(existing_level > ach.level for existing_level in current_levels):
            UserAchievement.objects.filter(
                user=user,
                achievement__ach_type=ach.ach_type,
                achievement__level__lt=ach.level
            ).delete()
            UserAchievement.objects.create(user=user, achievement=ach)
            current_levels.add(ach.level)

    @staticmethod
    def process_special_achievements(user):
        """Process special achievements (type 7)."""
        try:
            user_special_achievements = UserAchievement.objects.filter(
                user=user, 
                achievement__ach_type='7'
            ).values_list('achievement__name', flat=True)
            
            all_achievements = Achievement.objects.filter(ach_type='7')
            current_time = now().replace(tzinfo=None)

            # Early Bird
            if 'Early Bird' not in user_special_achievements and current_time <= SITE_LAUNCH_DATE + timedelta(days=30):
                early_bird = all_achievements.filter(name='Early Bird').first()
                if early_bird:
                    UserAchievement.objects.create(user=user, achievement=early_bird)

            # Marathoner
            if 'Marathoner' not in user_special_achievements:
                last_30_days = now().date() - timedelta(days=30)
                login_count = user.logins.filter(date__gte=last_30_days).aggregate(
                    count=Count('date', distinct=True)
                )['count']
                if login_count == 30:
                    marathoner = all_achievements.filter(name='Marathoner').first()
                    if marathoner:
                        UserAchievement.objects.create(user=user, achievement=marathoner)

            # Perfectionist
            if 'Perfectionist' not in user_special_achievements:
                edited_words = UserProfile.objects.filter(user=user).values_list(
                    'edited_words', flat=True
                ).first()
                if edited_words and edited_words >= 20:
                    perfectionist = all_achievements.filter(name='Perfectionist').first()
                    if perfectionist:
                        UserAchievement.objects.create(user=user, achievement=perfectionist)

            # Gotta Catch 'Em All
            if "Gotta Catch 'Em All!" not in user_special_achievements:
                user_ach_count = UserAchievement.objects.filter(
                    user=user
                ).exclude(achievement__ach_type='7').count()
                total_ach_count = Achievement.objects.exclude(ach_type='7').count()
                if total_ach_count == user_ach_count:
                    gcea = all_achievements.filter(name="Gotta Catch 'Em All!").first()
                    if gcea:
                        UserAchievement.objects.create(user=user, achievement=gcea)

        except Exception as e:
            logger.error(f"Error processing special achievements for user {user.id}: {str(e)}")

    @staticmethod
    def process_interaction_achievements(user):
        """Process interaction achievements (type 5)."""
        try:
            user_interaction_achievements = UserAchievement.objects.filter(
                user=user, 
                achievement__ach_type='5'
            ).values_list('achievement__name', flat=True)

            # Friendly Learner
            if not user_interaction_achievements:
                user_groups = WordGroup.objects.filter(uses_users=user).count()
                if user_groups >= 5:
                    UserAchievement.objects.create(
                        user=user, 
                        achievement=Achievement.objects.get(ach_type='5', level=1)
                    )

            # Social Butterfly
            friendly_learner = Achievement.objects.get(ach_type='5', level=1)
            if friendly_learner.name in user_interaction_achievements:
                shared_groups = CommunityGroup.objects.filter(
                    state='added', 
                    group__user=user
                ).count()
                if shared_groups >= 10:
                    social_butterfly = Achievement.objects.get(ach_type='5', level=2)
                    UserAchievement.objects.create(user=user, achievement=social_butterfly)
                    UserAchievement.objects.filter(user=user, achievement=friendly_learner).delete()

        except Exception as e:
            logger.error(f"Error processing interaction achievements for user {user.id}: {str(e)}")

# Signal receivers
@receiver(post_save, sender=Word)
def update_word_achievements(sender, instance, **kwargs):
    processor = AchievementProcessor()
    processor.process_achievements(instance.user, '1', processor.THRESHOLDS['1'])
    processor.process_achievements(instance.user, '6', processor.THRESHOLDS['6'])
    processor.process_special_achievements(instance.user)
    processor.process_interaction_achievements(instance.user)

@receiver(post_save, sender=WordGroup)
@receiver(m2m_changed, sender=WordGroup.words.through)
def update_group_achievements(sender, instance, action=None, **kwargs):
    if action in [None, 'post_add', 'post_remove', 'post_clear']:
        processor = AchievementProcessor()
        processor.process_achievements(instance.user, '2', processor.THRESHOLDS['2'])
        processor.process_special_achievements(instance.user)
        processor.process_interaction_achievements(instance.user)

@receiver(post_save, sender=Friendship)
def update_friendship_achievements(sender, instance, **kwargs):
    processor = AchievementProcessor()
    processor.process_achievements(instance.sender, '3', processor.THRESHOLDS['3'])
    processor.process_achievements(instance.receiver, '3', processor.THRESHOLDS['3'])

@receiver(post_save, sender=UserProfile)
def update_reading_achievements(sender, instance, **kwargs):
    processor = AchievementProcessor()
    processor.process_achievements(instance.user, '4', processor.THRESHOLDS['4'])
    processor.process_special_achievements(instance.user)
    processor.process_interaction_achievements(instance.user)