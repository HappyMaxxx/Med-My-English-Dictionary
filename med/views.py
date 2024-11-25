from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from med.forms import AddWordForm, ChengePasswordForm, RegisterUserForm, LoginUserForm, WordForm, GroupForm, EditProfileForm, AvatarUpdateForm, WordsShowForm
from django.views.generic import ListView, CreateView
from django.contrib.auth.views import LoginView
from django.views import View
from django.core.files.storage import default_storage

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator

from django.db import transaction
from django.db.models import Q

from django.http import JsonResponse
import json

from django.core.paginator import Paginator

from django.contrib.auth import logout, login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
import os
from med.models import *

def index(request):
    if request.user.is_authenticated:
        return redirect('profile', user_name=request.user.username)
    return render(request, 'med/index.html')

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
            return redirect('words')
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

        if user == self.request.user:
            self.is_my_dict = True
        else:
            self.is_my_dict = False

        return Word.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_name'] = self.kwargs['user_name']
        context['user'] = get_object_or_404(User, username=self.kwargs['user_name'])
        context['title'] = f"{self.kwargs['user_name']}'s Dictionary"
        context['is_my_dict'] = getattr(self, 'is_my_dict', False)
        context['is_dict'] = True
        context['logged_user'] = self.request.user
        context['access'] = UserProfile.objects.get(user=context['user']).access_dictionary
        return context


class GroupListView(ListView):
    model = WordGroup
    # paginate_by = 5
    template_name = 'med/groups.html'
    context_object_name = 'groups'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Groups"
        context['title1'] = "Words"
        context['is_group'] = False
        return context

    def get_queryset(self):
        return WordGroup.objects.filter(user=self.request.user)

class GroupWordsView(ListView):
    model = Word
    template_name = 'med/groups.html'
    context_object_name = 'words'

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
        context['groups'] = WordGroup.objects.filter(user=self.request.user)
        context['is_main'] = self.is_main()
        context['group_id'] = self.kwargs.get('group_id')
        context['is_group'] = True
        context['words_f_g'] = True
        return context

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id, user=self.request.user)
        return group.words.all()

@method_decorator(login_required, name='dispatch')
class CreateGroupView(View):
    def get(self, request, *args, **kwargs):
        form = GroupForm()

        return render(request, 'med/create_group.html', {'form': form,})

    def post(self, request, *args, **kwargs):
        form = GroupForm(request.POST)
        if form.is_valid():
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
        curent_loged_user_name = request.user.username
        profile_user = user_name

        if curent_loged_user_name == profile_user:
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)

            if user_profile.what_type_show == 'fav':
                recent_words = Word.objects.filter(user=request.user, is_favourite=True)[:user_profile.words_num_in_prof]
            else:
                recent_words = Word.objects.filter(user=request.user)[:user_profile.words_num_in_prof]

            word_count = Word.objects.filter(user=request.user).count()
            group_count = WordGroup.objects.filter(user=request.user).count()

            friends = User.objects.filter(
                Q(friendship_requests_sent__receiver=request.user, friendship_requests_sent__status='accepted') |
                Q(friendship_requests_received__sender=request.user, friendship_requests_received__status='accepted')
            ).distinct()

            friend_requests = Friendship.objects.filter(receiver=request.user, status='pending')

            return render(request, 'med/profile.html', {
                'user': request.user,
                'recent_words': recent_words,
                'word_count': word_count,
                'group_count': group_count,
                'friend_count': friends.count(), 
                'friend_requests': friend_requests,
                'is_favorite': True if user_profile.what_type_show == 'fav' else False,
                'user_profile': user_profile,
                'is_my_profile': True,
                'is_profile': True,
                'friends': friends,
            })
        
        else:
            user = get_object_or_404(User, username=user_name)
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            is_friends = False

            if user_profile.what_type_show == 'fav':
                recent_words = Word.objects.filter(user=user, is_favourite=True)[:user_profile.words_num_in_prof]
            else:
                recent_words = Word.objects.filter(user=user)[:user_profile.words_num_in_prof]

            word_count = Word.objects.filter(user=user).count()
            group_count = WordGroup.objects.filter(user=user).count()

            friends = User.objects.filter(
                Q(friendship_requests_sent__receiver=user, friendship_requests_sent__status='accepted') |
                Q(friendship_requests_received__sender=user, friendship_requests_received__status='accepted')
            ).distinct()

            if request.user in friends:
                is_friends = True

            return render(request, 'med/profile.html', {
                'user': user,
                'logged_user': request.user,
                'recent_words': recent_words,
                'word_count': word_count,
                'group_count': group_count,
                'friend_count': friends.count(),
                'is_favorite': True if user_profile.what_type_show == 'fav' else False,
                'user_profile': user_profile,
                'is_my_profile': False,
                'is_profile': True,
                'is_friends': is_friends,
                'friends': friends,
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
        print(word)
        print(word.is_favourite)
        word.is_favourite = not word.is_favourite
        print(word.is_favourite)
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
    return render(request, 'med/user_search.html', {'users': users, 'query': query, 'is_search': True, 'friends': friends})

@login_required
def send_friend_request(request, username):
    receiver = get_object_or_404(User, username=username)
    if receiver == request.user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('profile', user_name=request.user.username)
    
    friendship, created = Friendship.objects.get_or_create(sender=request.user, receiver=receiver)
    if created:
        messages.success(request, "Friend request sent.")
    else:
        messages.warning(request, "Friend request already sent.")
    return redirect('profile', user_name=request.user.username)

@login_required
def respond_to_friend_request(request, friendship_id, response):
    friendship = get_object_or_404(Friendship, id=friendship_id, receiver=request.user)
    if response == 'accept':
        friendship.status = 'accepted'
        friendship.save()
        messages.success(request, "Friend request accepted.")
    elif response == 'reject':
        friendship.status = 'rejected'
        friendship.save()
        messages.info(request, "Friend request rejected.")
    return redirect('friends_list', user_name=request.user.username)

@login_required
def friends_list_view(request, user_name):
    user = get_object_or_404(User, username=user_name)
    friendships = Friendship.objects.filter(
        Q(sender=user, status='accepted') |
        Q(receiver=user, status='accepted')
    )

    friends = [friendship.sender if friendship.receiver == user else friendship.receiver for friendship in friendships]

    friend_requests = Friendship.objects.filter(receiver=user, status='pending')
    return render(request, 'med/friends_list.html', {
        'friends': friends, 
        'friend_requests': friend_requests,
    })