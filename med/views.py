from datetime import datetime
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from med.forms import (ChengePasswordForm, RegisterUserForm, LoginUserForm, EditProfileForm, 
                       AvatarUpdateForm, WordsShowForm)
from django.views.generic import ListView, CreateView
from django.contrib.auth.views import LoginView
from django.views import View
from django.views.decorators.cache import cache_page
from django.db.models import When, Case

from django.utils.timezone import now, timedelta
from django.db.models.functions import TruncDay

from django.contrib.auth.decorators import login_required

from django.db import transaction
from django.db.models import Q, Count

from django.http import JsonResponse
import json

from django.core.paginator import Paginator

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from med.models import (User, UserProfile, UserAchievement, Achievement, Category, Top,
                        Friendship, Notification)
from dictionary.models import Word, WordGroup

from practice.models import ReadingText, CommunityGroup

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings

from med.tasks import send_activation_email, update_top

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

processed_signals = {}
process_wrods_signals = {}

@cache_page(60 * 15)
def index(request):
    if request.user.is_authenticated:
        return redirect('profile', user_name=request.user.username)
    return render(request, 'med/index.html')

@cache_page(60 * 15)
def about(request):
    return render(request, 'med/about.html')

def add_to_main_group(request, word):
    group_name = f"All {request.user.username}'s "
    group, created = WordGroup.objects.get_or_create(
        name=group_name,
        is_main=True,
        user=request.user
    )

    group.save()

    if isinstance(word, str):
        word = Word.objects.get(word=word, user=request.user)

    group.words.add(word)


class ConfirmDeleteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        word_ids = request.GET.getlist('word_ids')
        group_id = request.GET.get('group_id')
        text_id = request.GET.get('text_id')

        context = {}
        if text_id:
            text = get_object_or_404(ReadingText, id=text_id)
            context.update({
                'is_text': True,
                'text': 'Are you sure you want to delete this text?',
                'text_id': text_id,
                'text_title': text.title
            })

        elif group_id:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            words = group.words.filter(id__in=word_ids) if word_ids else []
            context.update({
                'is_group': True,
                'group_name': group.name,
                'group_id': group_id,
                'words': words,
                'text': self._get_delete_message(words, group.name)
            })

            if word_ids:
                context['word_ids'] = word_ids

        elif word_ids:
            words = Word.objects.filter(id__in=word_ids, user=request.user)
            if not words:
                return redirect('words')
            context.update({
                'is_group': False,
                'words': words,
                'word_ids': word_ids,
                'text': self._get_delete_message(words)
            })
        return render(request, 'med/confirm_delete.html', context)

    def post(self, request, *args, **kwargs):
        word_ids = request.POST.getlist('word_ids')
        group_id = request.POST.get('group_id')
        text_id = request.POST.get('text_id')

        if text_id:
            get_object_or_404(ReadingText, id=text_id).delete()
            return redirect('practice_reading')
        elif group_id:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            if word_ids:
                words = group.words.filter(id__in=word_ids)
                for word in words:
                    group.words.remove(word)

                return redirect('group_words', group_id=group_id)
            else:
                group.delete()
                return redirect('groups')
        elif word_ids:
            Word.objects.filter(id__in=word_ids, user=request.user).delete()
            return redirect('words', user_name=request.user.username)
        
        return redirect('profile', user_name=request.user.username)

    @staticmethod
    def _get_delete_message(words, group_name=None):
        if group_name:
            return ("Are you sure you want to delete this group?"
                    if len(words) == 0 else
                    f"Are you sure you want to delete these words from group {group_name}?"
                    if len(words) > 1 else
                    f"Are you sure you want to delete this word from group {group_name}?")
        return ("Are you sure you want to delete these words?"
                if len(words) > 1 else
                "Are you sure you want to delete this word?")


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        create_notification(
            receiver=request.user,
            message="Your account has been activated successfully!"
        )
        return redirect('login')
    else:
        create_notification(
            receiver=request.user,
            message="Activation link is invalid!"
        )
        return redirect('register')


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'med/register.html'
    success_url = '/login'
    extra_context = {'title': 'Register'}

    @transaction.atomic
    def form_valid(self, form):
        user = form.save(commit=False)
        if User.objects.filter(email=user.email).exists():
            form.add_error('email', "User with this email already exists")
            return self.form_invalid(form)
        
        # user.is_active = False 
        user.save()

        # send_activation_email.delay(user.id)

        # return render(self.request, 'med/activation_email_sent.html')
        login(self.request, user)
        return redirect('profile', user_name=user.username)

class LoginUser(LoginView):
    form_class =  LoginUserForm
    template_name = 'med/login.html'
    extra_context = {'title': 'Log in'}

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'user_name': self.request.user.username})


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, user_name, **kwargs):
        def get_user_data(user):
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            is_favorite = user_profile.what_type_show == 'fav'

            recent_words = Word.objects.filter(
                user=user, 
                is_favourite=is_favorite
            )[:user_profile.words_num_in_prof] if is_favorite else Word.objects.filter(user=user)[:user_profile.words_num_in_prof]

            words = Word.objects.filter(user=user)
            word_count = words.count()
            group_count = max((WordGroup.objects.filter(user=user).count() +
                            WordGroup.objects.filter(uses_users=self.request.user).count()) - 1, 0)

            friends = User.objects.filter(
                Q(friendship_requests_sent__receiver=user, friendship_requests_sent__status='accepted') |
                Q(friendship_requests_received__sender=user, friendship_requests_received__status='accepted')
            ).distinct()

            word_stats = words.values('word_type').annotate(count=Count('id'))
            word_type_data = json.dumps([
                {
                    'name': word_type['word_type'].capitalize(),
                    'y': word_type['count']
                }
                for word_type in word_stats
            ])

            n_days = 7
            today = now().date()
            start_date = today - timedelta(days=n_days)

            daily_word_count = Word.objects.filter(
                user=user,
                time_create__gte=start_date
            ).annotate(
                day=TruncDay('time_create')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            daily_data = {
                entry['day'].date().isoformat(): entry['count']
                for entry in daily_word_count
            }
            daily_chart_data = json.dumps({
                'categories': [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(n_days + 1)],
                'data': [daily_data.get((start_date + timedelta(days=i)).strftime('%Y-%m-%d'), 0) for i in range(n_days + 1)],
            })

            if user_profile.chenged_order:
                achievements_order = user_profile.achicment_order.strip('[]').replace('"', '').split(",")

                order = [int(i) for i in achievements_order]

                achievements = UserAchievement.objects.filter(
                    user=request.user,
                    id__in=achievements_order
                ).order_by(Case(*[When(id=id, then=pos) for pos, id in enumerate(order)]))
            else:
                achievements = UserAchievement.objects.filter(user=request.user)[:5]
            
            
            # process_special_achivments(user)
            # process_interaction_achivments(user)

            streak_data = UserProfile.calculate_streak(user)

            current_streak, max_streak, current_start, current_end, longest_start, longest_end, ff = streak_data

            current_streak_range = UserProfile.format_date_range(current_start, current_end)
            longest_streak_range = UserProfile.format_date_range(longest_start, longest_end)

            user_in_top = Top.objects.filter(user=user, place__in=[1, 2, 3]) or None

            return {
                'user_profile': user_profile,
                'recent_words': recent_words,
                'word_count': word_count,
                'group_count': group_count,
                'friends': friends,
                'friend_count': friends.count(),
                'is_favorite': is_favorite,
                'word_type_data': word_type_data,
                'daily_chart_data': daily_chart_data,
                'order': user_profile.charts_order.split(','),
                'achievements': achievements,
                'current_streak': current_streak,
                'current_streak_range': current_streak_range,
                'longest_streak': max_streak,
                'longest_streak_range': longest_streak_range,
                'ff': ff,
                'user_in_top': user_in_top,
            }

        profile_user = get_object_or_404(User, username=user_name)
        is_my_profile = profile_user == request.user

        profile_data = get_user_data(profile_user)

        is_requests_in = True if Friendship.objects.filter(receiver=request.user, sender=profile_user, status='pending').values_list('sender', flat=True) else False
        is_requests_out = True if Friendship.objects.filter(sender=request.user, receiver=profile_user, status='pending').values_list('receiver', flat=True) else False

        if not is_my_profile:
            profile_data['is_friends'] = request.user in profile_data['friends']
        else:
            profile_data['friend_requests'] = Friendship.objects.filter(receiver=request.user, status='pending')

        friendships = Friendship.objects.filter(
            Q(sender=profile_user, status='accepted') |
            Q(receiver=profile_user, status='accepted')
        )

        if not is_my_profile and profile_data['is_friends']:
            friendship = friendships.filter(sender=profile_user, receiver=request.user).first() or friendships.filter(sender=request.user, receiver=profile_user).first()
            profile_user.friendship_id = friendship.id if friendship else None

        return render(request, 'med/profile.html', {
            **profile_data,
            'user': profile_user,
            'logged_user': request.user,
            'is_my_profile': is_my_profile,
            'is_profile': True,
            'is_requests_in': is_requests_in,
            'is_requests_out': is_requests_out,
        })
    

class EditProfileView(LoginRequiredMixin, View):
    def get_user_profile(self, user):
        return UserProfile.objects.get_or_create(user=user)[0]

    def get_forms(self, request, user_profile):
        return {
            'profile_form': EditProfileForm(instance=request.user),
            'words_show_form': WordsShowForm(instance=user_profile),
            'avatar_form': AvatarUpdateForm(instance=user_profile),
            'password_form': ChengePasswordForm(user=request.user),
        }

    def render_profile_page(self, request, user_profile, **kwargs):
        forms = self.get_forms(request, user_profile)
        forms.update(kwargs)
        forms['user_profile'] = user_profile 
        forms['order'] = user_profile.charts_order.split(',')
        return render(request, 'med/edit_profile.html', forms)

    def handle_delete_avatar(self, user_profile):
        if user_profile.avatar:
            try:
                os.remove(user_profile.avatar.path.replace('/media/', '/media/avatars/'))
            except FileNotFoundError:
                pass
            user_profile.avatar = None
            user_profile.save()

    def handle_cropped_avatar(self, request, user_profile):
        avatar_file = request.FILES.get('cropped_avatar')
        if avatar_file:
            try:
                new_name = f"{request.user.username}_{now().strftime('%Y%m%d%H%M')}_{request.user.id}.png"

                if user_profile.avatar:
                    try:
                        os.remove(user_profile.avatar.path.replace('/media/', '/media/avatars/'))
                    except FileNotFoundError:
                        pass

                user_profile.avatar.save(new_name, avatar_file)
                return True
            except Exception as e:
                return False
        return False

    def get(self, request, *args, **kwargs):
        user_profile = self.get_user_profile(request.user)
        return self.render_profile_page(request, user_profile)

    def post(self, request, *args, **kwargs):
        user_profile = self.get_user_profile(request.user)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if 'delete_avatar' in request.POST:
            self.handle_delete_avatar(user_profile)
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Avatar deleted'})
            return redirect('profile', user_name=request.user.username)

        if 'update_profile' in request.POST:
            profile_form = EditProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Profile updated'})
                return redirect('profile', user_name=request.user.username)
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': profile_form.errors})
            return self.render_profile_page(request, user_profile, profile_form=profile_form)

        if 'update_words_show' in request.POST:
            words_show_form = WordsShowForm(request.POST, instance=user_profile)
            charts_order = request.POST.get('word_stat_order')
            if charts_order:
                user_profile.charts_order = charts_order
                user_profile.save()

            pie_visible = request.POST.get('pie-visible') == 'true'
            bar_visible = request.POST.get('bar-visible') == 'true'
            line_visible = request.POST.get('time-visible') == 'true'

            if pie_visible != user_profile.show_pie_chart:
                user_profile.show_pie_chart = pie_visible
            if bar_visible != user_profile.show_bar_chart:
                user_profile.show_bar_chart = bar_visible
            if line_visible != user_profile.show_line_chart:
                user_profile.show_line_chart = line_visible

            if words_show_form.is_valid():
                words_show_form.save()
                user_profile.save()
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Words settings updated'})
                return redirect('profile', user_name=request.user.username)
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': words_show_form.errors})
            return self.render_profile_page(request, user_profile, words_show_form=words_show_form)

        if 'cropped_avatar' in request.FILES:
            success = self.handle_cropped_avatar(request, user_profile)
            if is_ajax:
                return JsonResponse({
                    'status': 'success' if success else 'error',
                    'message': 'Avatar updated' if success else 'Failed to update avatar',
                    'redirect_url': reverse('profile', kwargs={'user_name': request.user.username})
                })
            return redirect('profile', user_name=request.user.username)

        if 'change_password' in request.POST:
            password_form = ChengePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': 'Password updated'})
                return redirect('profile', user_name=request.user.username)
            if is_ajax:
                return JsonResponse({'status': 'error', 'errors': password_form.errors})
            return self.render_profile_page(request, user_profile, password_form=password_form)

        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'Invalid request'})
        return self.render_profile_page(request, user_profile)
        

def logout_user(request):
    logout(request)
    return redirect('login')

def check_username(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username', None)

        if username and User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'This username is already taken.'}, status=200)
        return JsonResponse({'error': ''}, status=200)

def user_search(request):
    query = request.GET.get('q')
    users = User.objects.filter(username__icontains=query) if query else []
    friends = User.objects.filter(
        Q(friendship_requests_sent__receiver=request.user, friendship_requests_sent__status='accepted') |
        Q(friendship_requests_received__sender=request.user, friendship_requests_received__status='accepted')
    ).distinct()

    friendships = Friendship.objects.filter(
        (Q(sender=request.user) & Q(receiver__in=friends)) | (Q(receiver=request.user) & Q(sender__in=friends))
    )

    friend_requests_in = Friendship.objects.filter(receiver=request.user, status='pending').values_list('sender_id', flat=True)
    friend_requests_out = Friendship.objects.filter(sender=request.user, status='pending').values_list('receiver_id', flat=True)

    for user in users:
        friendship = friendships.filter(sender=user, receiver=request.user).first() or friendships.filter(sender=request.user, receiver=user).first()
        user.friendship_id = friendship.id if friendship else None

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    paginated_users = paginator.get_page(page_number)
    
    for user in users:
        user.img = user.user_profile.get_avatar_url()

    return render(request, 'med/user_search.html', {
        'users': paginated_users,
        'query': query,
        'friends': friends,
        'friend_requests_in': friend_requests_in,
        'friend_requests_out': friend_requests_out,
        'is_search': True,
        'paginator': paginator,
    })

@login_required
def send_friend_request(request, username):
    receiver = get_object_or_404(User, username=username)

    if receiver == request.user:
        return redirect('profile', user_name=request.user.username)
    
    friendship, created = Friendship.objects.get_or_create(sender=request.user, receiver=receiver)

    create_notification(
        receiver=receiver,
        message=f"{request.user.username} sent you a friend request",
    )

    return redirect('profile', user_name=request.user.username)

@login_required
def respond_to_friend_request(request, friendship_id=None, user1_id=None, user2_id=None, response=None):
    if friendship_id:
        friendship = get_object_or_404(Friendship, id=friendship_id)
    elif user1_id and user2_id:
        user1 = get_object_or_404(User, id=user1_id)
        user2 = get_object_or_404(User, id=user2_id)
        friendship = Friendship.objects.filter(
            (Q(sender=user1) & Q(receiver=user2)) | 
            (Q(sender=user2) & Q(receiver=user1)), 
            status='pending'
        ).first()
        if not friendship:
            return redirect('friends_list', user_name=request.user.username)
    else:
        return redirect('friends_list', user_name=request.user.username)

    if friendship.receiver == request.user and response == 'accept':
        friendship.status = 'accepted'
        friendship.save()
    elif (friendship.receiver == request.user or friendship.sender == request.user) and response == 'reject':
        friendship.delete()
    else:
        pass

    return redirect('friends_list', user_name=request.user.username)

def delete_friend(request, friendship_id):
    friendship = get_object_or_404(Friendship, id=friendship_id)

    if friendship.sender == request.user or friendship.receiver == request.user:
        friendship.delete()

    return redirect('friends_list', user_name=request.user.username)

@login_required
def friends_list_view(request, user_name):
    user = get_object_or_404(User, username=user_name)
    is_my_friends = user == request.user

    friendships = Friendship.objects.filter(
        Q(sender=user, status='accepted') |
        Q(receiver=user, status='accepted')
    ).select_related('sender', 'receiver')

    friends = [
        friendship.sender if friendship.receiver == user else friendship.receiver
        for friendship in friendships
    ]

    friend_requests_in = Friendship.objects.filter(receiver=user, status='pending').select_related('sender')
    friend_requests_out = Friendship.objects.filter(sender=user, status='pending').select_related('receiver')

    for friend in friends:
        friendship = friendships.filter(sender=friend, receiver=request.user).first() or friendships.filter(sender=request.user, receiver=friend).first()
        friend.friendship_id = friendship.id if friendship else None

    return render(request, 'med/friends_list.html', {
        'user': user,
        'friends': friends,
        'friend_requests_in': friend_requests_in,
        "in_count": friend_requests_in.count(),
        'friend_requests_out': friend_requests_out,
        'is_my_friends': is_my_friends,
    })

def download_file(request, file):
    base_dir = 'media'
    file_path = os.path.join(base_dir, file)
    
    if not os.path.exists(file_path):
        raise Http404("File does not exist")

    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = 'attachment; filename=' + file
    return response

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
    if user.pk in process_wrods_signals:
        return
    
    process_wrods_signals[user.pk] = True
    
    achievement_type = ['1', '6']

    for ach_type in achievement_type:
        process_achievements(user, ach_type, thresholds)

SITE_LAUNCH_DATE = datetime(2025, 5, 15)

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

def send_group_to_friend(request, group_id, user_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    group = WordGroup.objects.get(user=request.user, id=group_id)
    user = User.objects.get(id=user_id)
    if group:
        create_notification(
            receiver=user,
            message="Your friend {request.user} sends you an invitation to save his group '{group.name}'",
            type='2',
            group=group,
        )

        return redirect('groups')
    else:
        return redirect('groups')

class FriendGroupWordsListView(LoginRequiredMixin, ListView):
    model = Word
    template_name = 'med/friend_group_words.html'
    context_object_name = 'words'
    paginate_by = 25

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)

        user_word_titles = [word.word.lower() for word in Word.objects.filter(user=self.request.user)]

        words = group.words.all()
        for word in words:
                word.is_saved = word.word.lower() in user_word_titles

        return words
    
    def get_context_data(self, **kwargs):
        process_interaction_achivments(self.request.user)

        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)
        notif_id = self.kwargs.get('notif_id')
        context['group'] = group

        context['notif_id'] = notif_id
        notif = Notification.objects.get(id=notif_id)
        notif.is_read = True
        notif.save()
        context['is_usses'] = group.uses_users.filter(id=self.request.user.id).exists()
        if CommunityGroup.objects.filter(group=context['group'], state='added').exists():
            context['is_community'] = True
        else:
            context['is_community'] = False
        return context

def accept_friend_group(request, notif_id):
    notif = Notification.objects.get(id=notif_id)

    group = notif.group
    if group:
        group.uses_users.add(request.user)

    return redirect('groups')

def decline_friend_group(request, notif_id):
    notif = Notification.objects.get(id=notif_id)
    
    if notif:
        notif.delete()
    
    return redirect('notifications')

def tops_by_category(request):
    categories = Category.objects.prefetch_related('tops').all()
    context = {
        'categories': categories,
    }
    return render(request, 'med/tops_by_category.html', context)

def api_get_tops_by_category(request):
    categories = Category.objects.prefetch_related('tops').all()
    categories_data = [
        {
            'id': category.id,
            'name': category.name,
            'last_update': category.last_update,
            'tops': [
                {
                    'id': top.id,
                    'user': top.user.username,
                    'points': top.points,
                } for top in category.tops.all()
            ]
        } for category in categories
    ]

    return JsonResponse({'categories': categories_data})

@login_required
def hide_warning_message(request):
    if request.method == "POST":
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.hide_warning_message = True
        profile.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


class NotiListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'med/notification.html'
    context_object_name = 'notifications'
    paginate_by = 25

    def get_queryset(self):
        user_name = self.request.user.username
        user = get_object_or_404(User, username=user_name)

        queryset = Notification.objects.filter(user=user).order_by('-time_create')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_name = self.request.user.username
        user = get_object_or_404(User, username=user_name)

        context.update({
            'user': user,
            'title': f"{user_name}'s Notifications",
        })
        return context


@login_required
def notifications_api(request):
    user = request.user
    unread_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-time_create')[:5]
    count = unread_notifications.count()
    
    notifications_list = [
        {
            "message": n.message,
            "time": n.time_create.strftime("%d.%m.%Y %H:%M")
        } for n in unread_notifications
    ]

    return JsonResponse({
        "count": count,
        "notifications": notifications_list
    })

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    return JsonResponse({'status': 'success', 'is_read': True})

def create_notification(receiver, message, type='1', is_read=False, group=None):
    try:
        Notification.objects.create(
            user=receiver,
            message=message,
            is_read=is_read,
            type=type,
            group=group,
        )
        return 0
    except:
        return 1

def page_not_found(request, exception):
    return render(request, 'med/404.html')

def soon_page(request):
    return render(request, 'med/soon.html')