import re
import string
from django.http import FileResponse, Http404, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from med.forms import AddWordForm, ChengePasswordForm, RegisterUserForm, LoginUserForm, WordForm, GroupForm, EditProfileForm, AvatarUpdateForm, WordsShowForm, TextForm
from django.views.generic import ListView, CreateView
from django.contrib.auth.views import LoginView
from django.views import View
from django.core.files.storage import default_storage
from django.views.decorators.cache import cache_page

from django.core.files.base import ContentFile
from PIL import Image
import base64

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator

from django.db import transaction
from django.db.models import Q, Count

from django.http import JsonResponse
import json

from django.core.paginator import Paginator

from urllib.parse import urlparse

import openpyxl

from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from med.models import *

MAX_GROUP_COUNT = 20

practice_cards = {
    'test': {
        'word': 'Test',
        'img': 'med/img/practice/dice_light.png',
        'dark_img': 'med/img/practice/dice_dark.png',
        'href': '#'
    },
    'reading': {
        'word': 'Reading',
        'img': 'med/img/practice/read_light.png',
        'dark_img': 'med/img/practice/read_dark.png',
        'href': 'practice_reading'
    },
    'groups': {
        'word': 'Groups',
        'img': 'med/img/practice/group_light.png',
        'dark_img': 'med/img/practice/group_dark.png',
        'href': 'practice_groups'
    },
}

@cache_page(60 * 15)
def index(request):
    if request.user.is_authenticated:
        return redirect('profile', user_name=request.user.username)
    return render(request, 'med/index.html')

@cache_page(60 * 15)
def about(request):
    return render(request, 'med/about.html')


@method_decorator(login_required, name='dispatch')
class AddWordView(LoginRequiredMixin, CreateView):
    form_class = AddWordForm
    template_name = 'med/add_word.html'
    extra_context = {'title': 'Add Word'}

    def get_success_url(self):
        return reverse_lazy('words', kwargs={'user_name': self.request.user.username})

    def form_valid(self, form):
        word = form.save(commit=False)
        word.user = self.request.user
        word.save()

        group_name = f"All {self.request.user.username}'s "
        group, created = WordGroup.objects.get_or_create(
            name=group_name,
            is_main=True,
            user=self.request.user
        )

        group.words.add(word)

        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ConfirmDeleteView(View):
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


@method_decorator(login_required, name='dispatch')
class EditWordView(View):
    def get(self, request, word_id, *args, **kwargs):
        word = get_object_or_404(Word, id=word_id, user=request.user)
        form = WordForm(instance=word)
        return render(request, 'med/edit_word.html', {'form': form, 'word': word})

    def post(self, request, word_id, *args, **kwargs):
        word = get_object_or_404(Word, id=word_id, user=request.user)
        form = WordForm(request.POST, instance=word)
        if form.is_valid():
            form.save()
            return redirect('words', user_name=request.user.username)
        return render(request, 'med/edit_word.html', {'form': form, 'word': word})
    

@method_decorator(login_required, name='dispatch')
class WordListView(ListView):
    model = Word
    template_name = 'med/words.html'
    context_object_name = 'words'
    paginate_by = 25

    def get_queryset(self):
        user_name = self.kwargs['user_name']
        user = get_object_or_404(User, username=user_name)

        self.is_my_dict = user == self.request.user

        return Word.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, username=self.kwargs['user_name'])
        request_user = self.request.user

        friends = User.objects.filter(
            Q(friendship_requests_sent__receiver=user, friendship_requests_sent__status='accepted') |
            Q(friendship_requests_received__sender=user, friendship_requests_received__status='accepted')
        ).distinct()

        is_friends = request_user in friends

        context.update({
            'user_name': self.kwargs['user_name'],
            'user': user,
            'title': f"{self.kwargs['user_name']}'s Dictionary",
            'is_my_dict': getattr(self, 'is_my_dict', False),
            'is_dict': True,
            'logged_user': request_user,
            'access': UserProfile.objects.get(user=user).access_dictionary,
            'is_friends': is_friends,
        })
        return context


class BaseGroupView(ListView):
    template_name = 'med/groups.html'

    def get_common_context(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = WordGroup.objects.filter(user=self.request.user).order_by('-is_main', 'name')
        context['used_groups'] = WordGroup.objects.filter(uses_users=self.request.user)
        context['len_groups'] = max(context['groups'].count() + context['used_groups'].count() - 1, 0)
        context['max_group_count'] = MAX_GROUP_COUNT if self.request.user.username != 'grouper' else 100
        return context


class GroupListView(BaseGroupView):
    model = WordGroup

    def get_context_data(self, **kwargs):
        context = self.get_common_context(**kwargs)
        context['title'] = "Groups"
        context['title1'] = "Words"
        context['is_group'] = False
        return context


class GroupWordsView(BaseGroupView):
    model = Word
    context_object_name = 'words'
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)

        if request.user != group.user and request.user not in group.uses_users.all():
            return HttpResponseRedirect(reverse('groups'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = self.get_common_context(**kwargs)

        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)
        is_my_group = group.user == self.request.user

        context.update({
            'is_my_group': is_my_group,
            'is_uses': not is_my_group and group.uses_users.filter(id=self.request.user.id).exists(),
            'title': "Groups",
            'title1': f"{group.name} Words ({group.user.username})" if not is_my_group else f"{group.name} Words",
            'is_main': group.is_main,
            'group_id': group_id,
            'is_group': True,
            'words_f_g': True,
        })

        if context['is_uses']:
            all_words = Word.objects.filter(user=self.request.user)

            user_word_titles = [word.word.lower() for word in all_words]

            group_words = group.words.all()

            for word in group_words:
                word.is_saved = word.word.lower() in user_word_titles

            context['words'] = group_words
        return context

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)
        return group.words.all()


@method_decorator(login_required, name='dispatch')
class CreateGroupView(View):
    def get(self, request, *args, **kwargs):

        len_groups = WordGroup.objects.filter(user=request.user).count()

        if request.user.username == 'grouper' and len_groups >= 101:
            return redirect('groups')

        if len_groups >= (MAX_GROUP_COUNT + 1) and request.user.username != 'grouper':
            return redirect('groups')
        
        form = GroupForm()
        return render(request, 'med/create_group.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = GroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['name']
            if WordGroup.objects.filter(name=group_name, user=request.user).exists():
                form.add_error('name', "Group with this name already exists")
                return render(request, 'med/create_group.html', {'form': form})

            group = form.save(commit=False)
            group.user = request.user
            group.save()
            return redirect('groups')

        return render(request, 'med/create_group.html', {'form': form})


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'med/register.html'
    success_url = '/login'
    extra_context = {'title': 'Register'}

    @transaction.atomic
    def form_valid(self, form):
        user = form.save()
        print(form.cleaned_data)
        raw_password = form.cleaned_data.get('password1')
        print("Введений пароль:", raw_password)
        login(self.request, user)
        return redirect('profile', user_name=user.username)


class LoginUser(LoginView):
    form_class =  LoginUserForm
    template_name = 'med/login.html'
    extra_context = {'title': 'Log in'}

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'user_name': self.request.user.username})


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request, user_name, **kwargs):
        def get_user_data(user):
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            is_favorite = user_profile.what_type_show == 'fav'

            if is_favorite:
                recent_words = Word.objects.filter(user=user, is_favourite=True)[:user_profile.words_num_in_prof]
            else:
                recent_words = Word.objects.filter(user=user)[:user_profile.words_num_in_prof]

            words = Word.objects.filter(user=user)
            word_count = words.count()
            group_count = max((WordGroup.objects.filter(user=user).count() + WordGroup.objects.filter(uses_users=self.request.user).count()) - 1, 0)

            friends = User.objects.filter(
                Q(friendship_requests_sent__receiver=user, friendship_requests_sent__status='accepted') |
                Q(friendship_requests_received__sender=user, friendship_requests_received__status='accepted')
            ).distinct()

            word_stats = words.values('word_type').annotate(count=Count('id'))
            word_type_data = [
                {
                    'name': word_type['word_type'].capitalize(),
                    'y': word_type['count']
                }
                for word_type in word_stats
            ]

            return {
                'user_profile': user_profile,
                'recent_words': recent_words,
                'word_count': word_count,
                'group_count': group_count,
                'friends': friends,
                'friend_count': friends.count(),
                'is_favorite': is_favorite,
                'word_type_data': json.dumps(word_type_data),
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
    

class SelectGroupView(View):
    def get(self, request):
        word_ids = request.GET.getlist('word_ids')
        if not word_ids:
            return redirect('words', user_name=request.user.username)
        words = Word.objects.filter(id__in=word_ids)
        groups = WordGroup.objects.filter(user=request.user, is_main=False)
        return render(request, 'med/select_group.html', {
            'words': words,
            'word_ids': word_ids,
            'groups': groups,
        })

    def post(self, request, *args, **kwargs):
        word_ids = request.POST.getlist('word_ids')
        group_id = request.POST.get('group')

        if group_id:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
        else:
            redirect('words', user_name=request.user.username)
        
        group_words = group.words.all()
        words = Word.objects.filter(id__in=word_ids, user=request.user)

        for word in words:
            if word not in group_words:
                group.words.add(word)

        return redirect('group_words', group_id=group_id)
    

@method_decorator(login_required, name='dispatch')
class EditProfileView(View):
    def get(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile_form = EditProfileForm(instance=request.user)
        words_show_form = WordsShowForm(instance=user_profile)
        avatar_form = AvatarUpdateForm(instance=user_profile)
        password_form = ChengePasswordForm(user=request.user)
        return render(request, 'med/edit_profile.html', {
            'user_profile': user_profile,
            'profile_form': profile_form,
            'words_show_form': words_show_form,
            'avatar_form': avatar_form,
            'password_form': password_form,
        })

    def post(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)

        if 'delete_avatar' in request.POST:
            if user_profile.avatar and os.path.isfile(user_profile.avatar.path):
                os.remove(user_profile.avatar.path)
            user_profile.avatar = None
            user_profile.save()
            return redirect('profile', user_name=request.user.username)
        
        if 'update_profile' in request.POST:
            profile_form = EditProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                return redirect('profile', user_name=request.user.username)

        if 'update_words_show' in request.POST:
            words_show_form = WordsShowForm(request.POST, instance=user_profile)
            if words_show_form.is_valid():
                words_show_form.save()
                return redirect('profile', user_name=request.user.username)

        if 'cropped_avatar' in request.POST:
            avatar_data = request.POST.get('cropped_avatar')

            if avatar_data:
                try:
                    format, imgstr = avatar_data.split(';base64,')
                    extension = format.split('/')[-1]

                    avatar_file = ContentFile(base64.b64decode(imgstr))

                    user_profile = UserProfile.objects.get(user=request.user)

                    new_name = f"{request.user.username}_{now().strftime('%Y%m%d%H%M')}_{request.user.id}.{extension}"
                    old_avatar_path = user_profile.avatar.path if user_profile.avatar else None
                    if old_avatar_path:
                        old_avatar_path = old_avatar_path.replace('/media/', '/media/avatars/')

                    if old_avatar_path and os.path.isfile(old_avatar_path):
                        default_storage.delete(old_avatar_path)

                    user_profile.avatar.save(new_name, avatar_file)

                    return redirect('profile', user_name=request.user.username)
                except Exception as e:
                    print(f"Error saving avatar: {e}")
                    messages.error(request, "Failed to update avatar. Please try again.")
                    
        if 'change_password' in request.POST:
            password_form = ChengePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, request.user)
                return redirect('profile', user_name=request.user.username)

        profile_form = EditProfileForm(instance=request.user)
        words_show_form = WordsShowForm(instance=user_profile)
        avatar_form = AvatarUpdateForm(instance=user_profile)
        password_form = ChengePasswordForm(user=request.user)

        return render(request, 'med/edit_profile.html', {
            'profile_form': profile_form,
            'words_show_form': words_show_form,
            'avatar_form': avatar_form,
            'password_form': password_form,
        })
        

def logout_user(request):
    logout(request)
    return redirect('login')

def make_favourite(request, word_id):
    try:
        word = get_object_or_404(Word, id=word_id, user=request.user)
        word.is_favourite = not word.is_favourite
        word.save()
        return redirect('words', user_name=request.user.username)
    except:
        return redirect('login')

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>404 Page Not Found</h1>")

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
    )

    friends = [
        friendship.sender if friendship.receiver == user else friendship.receiver
        for friendship in friendships
    ]

    friend_requests_in = Friendship.objects.filter(receiver=user, status='pending')
    friend_requests_out = Friendship.objects.filter(sender=user, status='pending')

    for user in friends:
        friendship = friendships.filter(sender=user, receiver=request.user).first() or friendships.filter(sender=request.user, receiver=user).first()
        user.friendship_id = friendship.id if friendship else None

    return render(request, 'med/friends_list.html', {
        'friends': friends, 
        'friend_requests_in': friend_requests_in,
        'friend_requests_out': friend_requests_out,
        'is_my_friends': is_my_friends,
    })


# @cache_page(60 * 15)
def practice_view(request):
    return render(request, 'med/practice.html', {'cards': practice_cards.values()})

def reading_view(request):
    texts = ReadingText.objects.all()
    paginator = Paginator(texts, 25)
    page_number = request.GET.get('page')
    paginated_texts = paginator.get_page(page_number)
    page_obj = paginator.get_page(page_number)
    return render(request, 'med/reading.html', {'texts': paginated_texts, 'paginator': paginator, 'page_obj': page_obj})

def parct_groups_view(request):
    groups = WordGroup.objects.filter(user__username='grouper', is_main=False)

    for group in groups:
        group.words_count = group.words.count()
    groups = sorted(groups, key=lambda x: x.words_count, reverse=False)

    paginator = Paginator(groups, 25)
    page_number = request.GET.get('page')
    paginated_groups = paginator.get_page(page_number)
    page_obj = paginator.get_page(page_number)

    return render(request, 'med/practice_groups.html', {'groups': paginated_groups, 'paginator': paginator, 'page_obj': page_obj})

def split_content_by_phrases(content, translations):
    words = content.split()
    result = []
    i = 0
    lower_translations = {k.lower(): v for k, v in translations.items()}

    def clean_word(word):
        return word.strip(string.punctuation).lower()

    while i < len(words):
        match = None
        for j in range(len(words), i, -1):
            phrase = " ".join(words[i:j])
            cleaned_phrase = clean_word(phrase)
            if cleaned_phrase in lower_translations:
                match = (phrase, lower_translations[cleaned_phrase])
                i = j
                break
        if match:
            result.append(match)
        else:
            word = words[i]
            result.append((word, None))
            i += 1
    return result

def reading_text_view(request, text_id):
    text = get_object_or_404(ReadingText, id=text_id)
    base_url = None
    if text.is_auth_a:
        url = text.auth
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    content_phrases = []
    for paragraph in text.content.splitlines():
        phrases = split_content_by_phrases(paragraph, text.words_with_translations)
        content_phrases.append(phrases)

    return render(request, 'med/read_text.html', {
        'text': text,
        'base_url': base_url,
        'content_phrases': content_phrases
    })

def word_detail_view(request, word, text_id):
    text = get_object_or_404(ReadingText, content__icontains=word, id=text_id)
    translation = text.words_with_translations.get(word.lower(), 'The translation is not found')

    sentences = re.split(r'(?<=[.!?])[\s\n]+', text.content)
    example_sentence = next((sentence for sentence in sentences if word in sentence), 'The example sentence is not found')

    return render(request, 'med/word_detail.html', {'word': word, 'translation': translation, 'example': example_sentence, 'text_id': text_id})

def word_couner(text):
    words = text.split()
    return len(words)

def time_counter(words):
    return round(words / 60)

def text_add_view(request):
    form = TextForm()

    if request.method == 'POST':
        form = TextForm(request.POST)
        word_count = word_couner(form.data['content'])
        time_count = time_counter(word_count)
        if form.is_valid():
            form.instance.word_count = word_count
            form.instance.time_to_read = time_count
            form.save()
            return redirect('practice_reading')
        
    return render(request, 'med/add_text.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class EditTextView(View):
    def get(self, request, text_id, *args, **kwargs):
        text = get_object_or_404(ReadingText, id=text_id)
        form = TextForm(instance=text)
        return render(request, 'med/edit_text.html', {'form': form, 'text': text})

    def post(self, request, text_id, *args, **kwargs):
        text = get_object_or_404(ReadingText, id=text_id)
        form = TextForm(request.POST, instance=text)
        word_count = word_couner(form.data['content'])
        time_count = time_counter(word_count)
        if form.is_valid():
            form.instance.word_count = word_count
            form.instance.time_to_read = time_count
            form.save()
            return redirect('reading_text', text_id=text_id)
        return render(request, 'med/edit_text.html', {'form': form, 'text': text})


@method_decorator(login_required, name='dispatch')
class PracticeGroupWordsListView(ListView):
    model = Word
    template_name = 'med/group_words.html'
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
        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)
        context['group'] = group
        context['is_usses'] = group.uses_users.filter(id=self.request.user.id).exists()
        return context
    
def add_as_uses(request, group_id):
    group = get_object_or_404(WordGroup, id=group_id)
    group.uses_users.add(request.user)
    return redirect('group_words_practice', group_id=group_id)

def leave_group(request, group_id, fp):

    if fp.lower() in ['true', '1', 'yes']:
        is_fp = True
    elif fp.lower() in ['false', '0', 'no']:
        is_fp = False

    group = get_object_or_404(WordGroup, id=group_id)
    group.uses_users.remove(request.user)
    if is_fp:
        return redirect('group_words_practice', group_id=group_id)
    return redirect('groups')


def save_word(request, word_id):
    word = get_object_or_404(Word, id=word_id)
    existing_word = Word.objects.filter(user=request.user, id=word.id).first()
    group_name = f"All {request.user.username}'s "

    if not existing_word:
        Word.objects.create(user=request.user, word=word.word, translation=word.translation,
                            word_type=word.word_type, example=word.example, is_favourite=False)

        new_word = Word.objects.get(word=word.word, user=request.user)

        group, created = WordGroup.objects.get_or_create(
            name=group_name,
            is_main=True,
            user=request.user
        )

        group.words.add(new_word)

    return redirect('words', user_name=request.user.username)

def save_group_words(request, group_id):
    user = request.user
    group = get_object_or_404(WordGroup, id=group_id)
    words = group.words.all()
    word_ids = [word.id for word in words]
    group_name = f"All {user.username}'s "
    all_my_words = Word.objects.filter(user=user)

    new_group = WordGroup.objects.create(
        name=f"{group.name}",
        user=user
    )

    for word_id in word_ids:
        original_word = get_object_or_404(Word, id=word_id)

        if not all_my_words.filter(word=original_word.word).exists():
            copied_word = Word.objects.create(
                word=original_word.word,
                translation=original_word.translation,
                example=original_word.example,
                word_type=original_word.word_type,
                user=user,
            )
            
            # all words groop
            group1, created = WordGroup.objects.get_or_create(
                name=group_name,
                is_main=True,
                user=user
            )

            group1.words.add(copied_word)

            new_group.words.add(copied_word)

        else:
            word = all_my_words.get(word=original_word.word)
            new_group.words.add(word)
    
    group.uses_users.remove(user)
    return redirect('groups')


from django.contrib import messages

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        group_name = f"All {request.user.username}'s "
        group, created = WordGroup.objects.get_or_create(
            name=group_name,
            is_main=True,
            user=request.user
        )
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name.lower()

        try:
            if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                wb = openpyxl.load_workbook(uploaded_file)
                sheet = wb[wb.sheetnames[0]]
                words = []
                for row in sheet.iter_rows(values_only=True):
                    if len(row) == 3:
                        words.append(row)
                wb.close()

                if words[0] == ('Word', 'Translation', 'Example'):
                    for word in words[1:]:
                        word = Word.objects.create(
                            word=word[0],
                            translation=word[1],
                            example=word[2],
                            user=request.user,
                        )
                        group.words.add(word)
                    return redirect('words', user_name=request.user.username)
                else:
                    messages.error(request, "Excel file format is incorrect. First row should be 'Word', 'Translation', 'Example'.")
                    return render(request, 'med/words_ff.html')

            elif file_name.endswith('.txt'):
                content = uploaded_file.read().decode('utf-8')
                try:
                    json_data = json.loads(content)
                    if isinstance(json_data, list):
                        for item in json_data:
                            if all(k in item for k in ('word', 'translation', 'example')):
                                word_type = item.get('word_type', 'other') 
                                
                                word = Word.objects.create(
                                    word=item['word'],
                                    translation=item['translation'],
                                    example=item['example'],
                                    word_type=word_type, 
                                    user=request.user,
                                )
                                group.words.add(word)
                        return redirect('words', user_name=request.user.username)
                    else:
                        messages.error(request, "JSON file should contain a list of objects with keys: 'word', 'translation', 'example'.")
                        return render(request, 'med/words_ff.html')
                except json.JSONDecodeError:
                    messages.error(request, "Invalid JSON format in text file.")
                    return render(request, 'med/words_ff.html')

            else:
                messages.error(request, "Unsupported file format. Please upload .xlsx, .xls, or .txt file.")
                return render(request, 'med/words_ff.html')

        except Exception as e:
            messages.error(request, f"An error occurred while processing the file: {e}")
            return render(request, 'med/words_ff.html')

    return render(request, 'med/words_ff.html')


def download_file(request, file):
    base_dir = 'media'
    file_path = os.path.join(base_dir, file)
    
    if not os.path.exists(file_path):
        raise Http404("File does not exist")

    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = 'attachment; filename=' + file
    return response

def save_all_words_as_json(request):
    user = request.user
    words = Word.objects.filter(user=user)
    data = []

    for word in words:
        data.append({
            'word': word.word,
            'translation': word.translation,
            'example': word.example,
            'word_type': word.word_type,
        })
    
    file_name = f"{user.username}_words.json"
    file_path = os.path.join('media', file_name)

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    return redirect('download_file', file=file_name)