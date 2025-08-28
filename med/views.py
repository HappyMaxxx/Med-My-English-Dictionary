from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from med.forms import (ChengePasswordForm, RegisterUserForm, LoginUserForm, EditProfileForm, 
                       AvatarUpdateForm, WordsShowForm)
from django.views.generic import CreateView
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

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
import os

from notifications.views import create_notification

from med.models import User, UserProfile, Category, Top
from achievements.models import UserAchievement
from friendship.models import Friendship
from dictionary.models import Word, WordGroup
from practice.models import ReadingText

from med.tasks import send_activation_email

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

            if user_profile.changed_order:
                achievements_order = user_profile.achicment_order.strip('[]').replace('"', '').split(",")

                order = [int(i) for i in achievements_order]

                achievements = UserAchievement.objects.filter(
                    user=request.user,
                    id__in=achievements_order
                ).order_by(Case(*[When(id=id, then=pos) for pos, id in enumerate(order)]))
            else:
                achievements = UserAchievement.objects.filter(user=request.user)[:5]

            streak = user.streak.get_streak_data()

            current_streak, max_streak, current_start, current_end, longest_start, longest_end, status = streak

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
                'status': status,
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

def download_file(request, file):
    base_dir = 'media'
    file_path = os.path.join(base_dir, file)
    
    if not os.path.exists(file_path):
        raise Http404("File does not exist")

    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = 'attachment; filename=' + file
    return response

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

def page_not_found(request, exception):
    return render(request, 'med/404.html')

def soon_page(request):
    return render(request, 'med/soon.html')