import re
import string
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from med.forms import AddWordForm, ChengePasswordForm, RegisterUserForm, LoginUserForm, WordForm, GroupForm, EditProfileForm, AvatarUpdateForm, WordsShowForm, TextForm
from django.views.generic import ListView, CreateView
from django.contrib.auth.views import LoginView
from django.views import View
from django.core.files.storage import default_storage
from django.views.decorators.cache import cache_page

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator

from django.db import transaction
from django.db.models import Q

from django.http import JsonResponse
import json

from django.core.paginator import Paginator

from urllib.parse import urlparse

from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from med.models import *

MAX_GROUP_COUNT = 10

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
    template_name = 'med/addword.html'
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

        if group_id and word_ids:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            words = group.words.filter(id__in=word_ids)
            return render(request, 'med/confirm_delete.html', {
                'is_group': True,
                'words': words,
                'word_ids': word_ids,
                'group_name': group.name,
                'group_id': group_id,
                'text': f'Are you sure you want to delete these words from group {group.name}?' if len(words) > 1 else f'Are you sure you want to delete this word from group {group.name}?'
            })

        elif group_id and not word_ids:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            return render(request, 'med/confirm_delete.html', {
                'is_group': True,
                'group_name': group.name,
                'group_id': group_id,
                'text': 'Are you sure you want to delete this group?'
            })

        elif word_ids and not group_id:
            words = Word.objects.filter(id__in=word_ids, user=request.user)
            if not words:
                return redirect('words')
            return render(request, 'med/confirm_delete.html', {
                'is_group': False,
                'words': words,
                'word_ids': word_ids,
                'text': 'Are you sure you want to delete these words?' if len(words) > 1 else 'Are you sure you want to delete this word?'
            })

        return redirect('profile', user_name=request.user.username) 

    def post(self, request, *args, **kwargs):
        word_ids = request.POST.getlist('word_ids')
        group_id = request.POST.get('group_id')
        
        if group_id and not word_ids:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            group.delete()
            return redirect('groups')
        
        elif word_ids and not group_id:
            Word.objects.filter(id__in=word_ids, user=request.user).delete()
            return redirect('words', user_name=request.user.username)

        elif group_id and word_ids:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            words = group.words.filter(id__in=word_ids)
            for word in words:
                group.words.remove(word)

            return redirect('group_words', group_id=group_id)

        return redirect('profile', user_name=request.user.username)


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


class GroupListView(ListView):
    model = WordGroup
    template_name = 'med/groups.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Groups"
        context['title1'] = "Words"
        context['is_group'] = False
        context['groups'] = WordGroup.objects.filter(user=self.request.user).order_by('-is_main', 'name')
        context['len_groups'] = max(context['groups'].count() - 1, 0)
        context['max_group_count'] = MAX_GROUP_COUNT
        return context


class GroupWordsView(ListView):
    model = Word
    template_name = 'med/groups.html'
    context_object_name = 'words'
    paginate_by = 25

    def is_main(self):
        group_id = self.kwargs.get('group_id')
        is_main = get_object_or_404(WordGroup, id=group_id, user=self.request.user).is_main
        return is_main

    def get_name(self): 
        group_id = self.kwargs.get('group_id')
        name = get_object_or_404(WordGroup, id=group_id, user=self.request.user).name
        return name
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Groups"
        context['title1'] = f"{self.get_name()} Words"
        context['groups'] = WordGroup.objects.filter(user=self.request.user).order_by('-is_main', 'name')
        context['len_groups'] = max(context['groups'].count() - 1, 0)
        context['is_main'] = self.is_main()
        context['group_id'] = self.kwargs.get('group_id')
        context['is_group'] = True
        context['words_f_g'] = True
        context['max_group_count'] = MAX_GROUP_COUNT
        return context

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id, user=self.request.user)
        return group.words.all()


@method_decorator(login_required, name='dispatch')
class CreateGroupView(View):
    def get(self, request, *args, **kwargs):

        len_groups = WordGroup.objects.filter(user=request.user).count()

        if len_groups >= MAX_GROUP_COUNT + 1:
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


            word_count = Word.objects.filter(user=user).count()
            group_count = WordGroup.objects.filter(user=user).count()

            friends = User.objects.filter(
                Q(friendship_requests_sent__receiver=user, friendship_requests_sent__status='accepted') |
                Q(friendship_requests_received__sender=user, friendship_requests_received__status='accepted')
            ).distinct()

            return {
                'user_profile': user_profile,
                'recent_words': recent_words,
                'word_count': word_count,
                'group_count': group_count,
                'friends': friends,
                'friend_count': friends.count(),
                'is_favorite': is_favorite,
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
            'profile_form': profile_form,
            'words_show_form': words_show_form,
            'avatar_form': avatar_form,
            'password_form': password_form,
        })

    def post(self, request, *args, **kwargs):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
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

        if 'update_avatar' in request.POST:
            if request.POST.get('avatar') == '' and not request.POST.get('avatar-clear'):
                return redirect('edit_profile')

            old_avatar_path = None

            if user_profile.avatar:
                old_avatar_path = user_profile.avatar.path  

            avatar_form = AvatarUpdateForm(request.POST, request.FILES, instance=user_profile)
            if avatar_form.is_valid():
                avatar_form.save()
                if old_avatar_path:
                    if os.path.isfile(old_avatar_path):
                        default_storage.delete(old_avatar_path)
                return redirect('profile', user_name=request.user.username)
            
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
    return render(request, 'med/practice.html')

def reading_view(request):
    texts = ReadingText.objects.all()
    return render(request, 'med/reading.html', {'texts': texts})

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
        