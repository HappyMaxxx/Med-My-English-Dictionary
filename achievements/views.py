from datetime import datetime
from typing import List, Tuple, Dict
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q, Count, Case, When
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import User
from med.models import UserProfile
from .models import UserAchievement, Achievement
from friendship.models import Friendship
from dictionary.models import Word, WordGroup
from practice.models import CommunityGroup

import logging

logger = logging.getLogger(__name__)
SITE_LAUNCH_DATE = datetime(2025, 8, 21)

def achievement_view(request):
    """
    Handle achievement page view and order updates.
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        order = request.POST.get('word_stat_order')
        if order:
            user_profile.achievement_order = order
            user_profile.changed_order = True
            user_profile.save(update_fields=["achievement_order", "changed_order"])

    # Group achievements by type
    achievements_by_type = {}
    for ach in Achievement.objects.all():
        ach_type = dict(Achievement.ACH_TYPE_CHOICES).get(ach.ach_type, ach.ach_type)
        achievements_by_type.setdefault(ach_type, []).append(ach)

    # Get user's achievements
    user_achievements = UserAchievement.objects.filter(user=request.user)
    user_achievement_names = user_achievements.values_list('achievement__name', flat=True)

    # Get highest level for each achievement type
    highest_levels = {}
    for ach_type_value, ach_type_name in Achievement.ACH_TYPE_CHOICES[:6]:
        ach = Achievement.objects.filter(
            ach_type=ach_type_value,
            userachievement__user=request.user
        ).order_by('-level').first()
        if ach:
            highest_levels[ach_type_name] = ach.level

    # Mask unreached achievements
    for ach_type, ach_list in achievements_by_type.items():
        for ach in ach_list:
            if ach_type == 'Special':
                if ach.name not in user_achievement_names:
                    ach.name = "?"
                    ach.description = "???"
                continue

            if ach.level > highest_levels.get(ach_type, 0):
                ach.name = "?"
                ach.description = ach.requirements if ach.level == highest_levels.get(ach_type, 0) + 1 else "???"

    # Handle achievement ordering
    if user_profile.changed_order:
        order_ids = [int(i) for i in user_profile.achievement_order.strip('[]').replace('"', '').split(",") if i]
        profile_achievements = UserAchievement.objects.filter(
            user=request.user,
            id__in=order_ids
        ).order_by(Case(*[When(id=id, then=pos) for pos, id in enumerate(order_ids)]))
    else:
        profile_achievements = user_achievements[:5]

    profile_achievements_list = [ach.achievement for ach in profile_achievements]
    all_user_achievements = [ach.achievement for ach in user_achievements]

    # Get highest level achievements per type
    highest_level_achievements = []
    seen_types = set()
    for ach in all_user_achievements:
        if ach.ach_type not in seen_types or not any(a.ach_type == ach.ach_type and a.level > ach.level for a in highest_level_achievements):
            highest_level_achievements.append(ach)
            seen_types.add(ach.ach_type)

    # Add special achievements
    special_achievements = Achievement.objects.filter(ach_type='7')
    highest_level_achievements.extend(ach for ach in special_achievements if ach not in highest_level_achievements)

    return render(request, 'achievements/achievements.html', {
        'profile_achievements': profile_achievements,
        'profile_achievements_list': profile_achievements_list,
        'highest_level_achievements': highest_level_achievements,
        'achievements_by_type': achievements_by_type,
        'achievement_types': [ach[1] for ach in Achievement.ACH_TYPE_CHOICES],
        'user_achievement_names': user_achievement_names,
        'highest_levels': highest_levels,
    })

def add_achievement(request, ach_id: int):
    """
    Add an achievement to user's ordered list.
    """
    user_profile = get_object_or_404(UserProfile, user=request.user)
    achievement = get_object_or_404(Achievement, id=ach_id)
    user_achievement = get_object_or_404(UserAchievement, user=request.user, achievement=achievement)

    achievement_order = user_profile.achievement_order.strip('[]').split(",") if user_profile.achievement_order else []
    achievement_order = [str(user_achievement.id)] + achievement_order[:4]
    
    user_profile.achievement_order = ",".join(achievement_order)
    user_profile.changed_order = True
    user_profile.save(update_fields=['achievement_order', 'changed_order'])
    
    return redirect('achievement')