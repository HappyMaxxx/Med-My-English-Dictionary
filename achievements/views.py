from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import When, Case

from django.utils.timezone import now, timedelta

from django.db.models import Q, Count

from med.models import UserProfile
from .models import UserAchievement, Achievement
from friendship.models import Friendship
from dictionary.models import Word, WordGroup

from practice.models import CommunityGroup

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from med.tasks import send_activation_email, update_top

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processed_signals = {}
process_words_signals = {}
SITE_LAUNCH_DATE = datetime(2025, 8, 21)

def process_achievements(user, achievement_type, thresholds):
    if achievement_type == '6':
        processed_signals.clear()

    if user.pk in processed_signals:
        return

    processed_signals[user.pk] = True

    try:
        achievements = Achievement.objects.filter(ach_type=achievement_type)
        user_profile = UserProfile.objects.get(user=user)

        current_user_achievements = UserAchievement.objects.filter(
            user=user,
            achievement__ach_type=achievement_type
        )
        current_levels = {ua.achievement.level for ua in current_user_achievements}

        if achievement_type == '1':
            item_count = Word.objects.filter(user=user).count()
        elif achievement_type == '2':
            item_count = WordGroup.objects.filter(user=user, is_main=False).count()
        elif achievement_type == '3':
            item_count = Friendship.objects.filter(
                Q(sender=user, status='accepted') | Q(receiver=user, status='accepted')
            ).count()
        elif achievement_type == '4':
            item_count = (user_profile.text_read, user_profile.words_added_from_text)
        elif achievement_type == '6':
            item_count = Word.objects.filter(user=user).exclude(example='').count()
        else:
            item_count = 0

        for i, ach in enumerate(achievements):
            threshold = thresholds[i] if i < len(thresholds) else thresholds[-1]

            if achievement_type in ['1', '2', '3', '6']:
                if achievement_type == '2' and current_levels == {2}:
                    groups_with_more_5_words = WordGroup.objects.filter(
                        user=user, is_main=False
                    ).annotate(
                        word_count=Count('words')
                    ).filter(word_count__gte=5).count()

                    if groups_with_more_5_words >= 5 and ach.level not in current_levels:
                        if any(existing_level > ach.level for existing_level in current_levels):
                            continue

                        UserAchievement.objects.filter(
                            user=user,
                            achievement__ach_type=achievement_type,
                            achievement__level__lt=ach.level
                        ).delete()
                        UserAchievement.objects.create(user=user, achievement=ach)
                        current_levels.add(ach.level)

                    continue

                if item_count >= threshold and ach.level not in current_levels:
                    if any(existing_level > ach.level for existing_level in current_levels):
                        continue

                    UserAchievement.objects.filter(
                        user=user,
                        achievement__ach_type=achievement_type,
                        achievement__level__lt=ach.level
                    ).delete()
                    UserAchievement.objects.create(user=user, achievement=ach)
                    current_levels.add(ach.level)

            elif achievement_type == '4':
                if (
                    item_count[0] >= threshold[0]
                    and item_count[1] >= threshold[1]
                    and ach.level not in current_levels
                ):
                    if any(existing_level > ach.level for existing_level in current_levels):
                        continue

                    UserAchievement.objects.filter(
                        user=user,
                        achievement__level__lt=ach.level
                    ).delete()
                    UserAchievement.objects.create(user=user, achievement=ach)
                    current_levels.add(ach.level)
    finally:
        processed_signals.pop(user.pk, None)

def process_words_achivments(user, thresholds):
    if user.pk in process_words_signals:
        return
    
    process_words_signals[user.pk] = True
    
    achievement_type = ['1', '6']

    for ach_type in achievement_type:
        process_achievements(user, ach_type, thresholds)

def process_special_achivments(user):
    user_special_achivments = UserAchievement.objects.filter(user=user, achievement__ach_type='7').values_list('achievement__name', flat=True)
    
    all_achievements = Achievement.objects.filter(ach_type='7')

    current_time = now().replace(tzinfo=None)
    if 'Early Bird' not in user_special_achivments and current_time <= SITE_LAUNCH_DATE + timedelta(days=30):
        early_bird_achievement = all_achievements.get(name='Early Bird')
        if early_bird_achievement:
            UserAchievement.objects.create(user=user, achievement=early_bird_achievement)

    # Marathoner
    if 'Marathoner' not in user_special_achivments:
        last_30_days = now().date() - timedelta(days=30)
        user_logins = user.logins.filter(date__gte=last_30_days).aggregate(count=Count('date', distinct=True))['count']
        if user_logins == 30:
            marathoner_achievement = all_achievements.get(name='Marathoner')
            if marathoner_achievement:
                UserAchievement.objects.create(user=user, achievement=marathoner_achievement)

    # Perfectionist
    if 'Perfectionist' not in user_special_achivments:
        edited_words = UserProfile.objects.filter(user=user).values_list('edited_words', flat=True).first()
        if edited_words and edited_words >= 20:
            perfectionist_achievement = all_achievements.get(name='Perfectionist')
            if perfectionist_achievement:
                UserAchievement.objects.create(user=user, achievement=perfectionist_achievement)

    # Gotta Catch 'Em All
    if "Gotta Catch 'Em All!" not in user_special_achivments:
        user_ach_count = UserAchievement.objects.filter(user=user).exclude(achievement__ach_type='7').count()
        ach_count = Achievement.objects.exclude(ach_type='7').count()
        if ach_count == user_ach_count:
            gcea_acievement = all_achievements.get(name="Gotta Catch 'Em All!")
            if gcea_acievement:
                UserAchievement.objects.create(user=user, achievement=gcea_acievement)

def process_interaction_achivments(user):
    user_interaction_achivments = UserAchievement.objects.filter(user=user, achievement__ach_type='5').values_list('achievement__name', flat=True)
    # Friendly learner
    if not user_interaction_achivments:
        user_groups = WordGroup.objects.filter(uses_users=user).count()
        if user_groups >= 5:
            UserAchievement.objects.create(user=user, achievement=Achievement.objects.get(ach_type='5', level=1))

    # Social Butterfly
    fl_ach = Achievement.objects.get(ach_type='5', level=1)
    if fl_ach.name in user_interaction_achivments:
        shered_groups = CommunityGroup.objects.filter(state='added', group__user=user).count()
        if shered_groups >= 10:
            UserAchievement.objects.create(user=user, achievement=Achievement.objects.get(ach_type='5', level=2))
            UserAchievement.objects.filter(user=user, achievement=fl_ach).delete()

@receiver(post_save, sender=Word)
def update_achievements_words(sender, instance, **kwargs):
    thresholds = [10, 50, 100]
    process_words_achivments(instance.user, thresholds)
    process_special_achivments(instance.user)
    process_interaction_achivments(instance.user)

@receiver(post_save, sender=WordGroup)
def update_achievements_on_group_words_change(sender, instance, **kwargs):
    thresholds = [1, 5, 10]
    process_achievements(instance.user, achievement_type='2', thresholds=thresholds)
    process_special_achivments(instance.user)
    process_interaction_achivments(instance.user)

@receiver(m2m_changed, sender=WordGroup.words.through)
def update_achievements_on_group_words_change(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        thresholds = [1, 5, 10]
        process_achievements(instance.user, achievement_type='2', thresholds=thresholds)
        process_special_achivments(instance.user)
        process_interaction_achivments(instance.user)   

@receiver(post_save, sender=Friendship)
def update_achievements_friends(sender, instance, **kwargs):
    thresholds = [5, 20, 50]
    
    process_achievements(instance.sender, achievement_type='3', thresholds=thresholds)
    process_achievements(instance.receiver, achievement_type='3', thresholds=thresholds)

@receiver(post_save, sender=UserProfile)
def update_achievements_reading(sender, instance, **kwargs):
    thresholds = [(5, 1), (50, 10), (100, 20)]
    process_achievements(instance.user, achievement_type='4', thresholds=thresholds)
    process_special_achivments(instance.user)
    process_interaction_achivments(instance.user)

def achievement_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        order = request.POST.get('word_stat_order')
        if order:
            user_profile.achicment_order = order
            user_profile.chenged_order = True
            user_profile.save(update_fields=["achicment_order", "chenged_order"]) 

    achivments = {}
    for ach in Achievement.objects.all():
        achivments[ach.ach_type] = achivments.get(ach.ach_type, []) + [ach]

    for ach_type in list(achivments.keys()):
        achivments[Achievement.ACH_TYPE_CHOICES[int(ach_type) - 1][1]] = achivments.pop(ach_type)

    user_achivments = UserAchievement.objects.filter(user=request.user).values_list('achievement__name', flat=True)

    biggest_level_each_type = {}

    for ach_type in Achievement.ACH_TYPE_CHOICES[:6]:
        ach = Achievement.objects.filter(
            ach_type=ach_type[0],
            userachievement__user=request.user
        ).order_by('-level').first()
        
        if ach:
            biggest_level_each_type[ach_type[1]] = ach.level
    
    for ach_type, ach_list in achivments.items():
        for ach in ach_list:
            if ach_type == 'Special':
                if ach.name not in user_achivments:
                    ach.name = "?"
                    ach.description = f"???"
                continue

            if ach.level > biggest_level_each_type.get(ach_type, 0):
                ach.name = "?"
                if ach.level == biggest_level_each_type.get(ach_type, 0) + 1:
                    ach.description = ach.requirements
                else:
                    ach.description = "???"

    if user_profile.chenged_order:
        achievements_order = user_profile.achicment_order.strip('[]').replace('"', '').split(",")

        order = [int(i) for i in achievements_order]

        profile_achievements = UserAchievement.objects.filter(
            user=request.user,
            id__in=achievements_order
        ).order_by(Case(*[When(id=id, then=pos) for pos, id in enumerate(order)]))
    else:
        profile_achievements = UserAchievement.objects.filter(user=request.user)[:5]

    prof_ach = [ach.achievement for ach in profile_achievements]

    user_ach_ach = [ach.achievement for ach in UserAchievement.objects.filter(user=request.user)]

    prof_ach_biggest_level = []
    for ach in user_ach_ach:
        ach_type = ach.ach_type

        if ach_type not in prof_ach_biggest_level or ach.level > prof_ach_biggest_level[ach_type].level:
            prof_ach_biggest_level.append(ach)

    special_ach = Achievement.objects.filter(ach_type='7')

    for ach in special_ach:
        if ach not in prof_ach_biggest_level:
            prof_ach_biggest_level.append(ach)

    return render(request, 'med/achievements.html', {
        'profile_achievements': profile_achievements,
        'prof_ach': prof_ach,
        'prof_ach_biggest_level': prof_ach_biggest_level,
        'achivments': achivments,
        'types': [ach[1] for ach in Achievement.ACH_TYPE_CHOICES],
        'user_achivments': user_achivments,
        'biggest_level_each_type': biggest_level_each_type,
    })

def add_achievement(request, ach_id):
    user_profile = UserProfile.objects.only('achicment_order', 'chenged_order').get(user=request.user)
    
    ach = get_object_or_404(Achievement, id=ach_id)
    
    user_achievement = get_object_or_404(UserAchievement, user=request.user, achievement=ach)

    achicment_order = user_profile.achicment_order.strip('[]').split(",") if user_profile.achicment_order else []

    achicment_order = [str(user_achievement.id)] + achicment_order
    achicment_order = achicment_order[:5]

    user_profile.achicment_order = ",".join(achicment_order)
    user_profile.chenged_order = True
    user_profile.save(update_fields=['achicment_order', 'chenged_order'])

    return redirect('achievement')