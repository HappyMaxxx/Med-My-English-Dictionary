from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from med.forms import AddWordForm, RegisterUserForm, LoginUserForm, WordForm, GroupForm

from django.views.generic import ListView, CreateView
from django.contrib.auth.views import LoginView
from django.views import View

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.db import transaction

from django.core.paginator import Paginator

from django.contrib.auth import logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from med.models import *

def index(request):
    return render(request, 'med/index.html')

def about(request):
    return render(request, 'med/about.html')


@method_decorator(login_required, name='dispatch')
class AddWordView(LoginRequiredMixin, CreateView):
    form_class = AddWordForm
    template_name = 'med/addword.html'
    success_url = reverse_lazy('words')
    extra_context = {'title': 'Add Word'}

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
        
        if group_id:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            return render(request, 'med/confirm_delete.html', {
                'is_group': True,
                'group_name': group.name,
                'group_id': group_id,
                'text': 'Are you sure you want to delete this group?'
            })

        elif word_ids:
            words = Word.objects.filter(id__in=word_ids, user=request.user)
            if not words:
                return redirect('words')
            return render(request, 'med/confirm_delete.html', {
                'is_group': False,
                'words': words,
                'word_ids': word_ids,
                'text': 'Are you sure you want to delete these words?' if len(words) > 1 else 'Are you sure you want to delete this word?'
            })

        return redirect('profile') 

    def post(self, request, *args, **kwargs):
        word_ids = request.POST.getlist('word_ids')
        group_id = request.POST.get('group_id')

        if group_id:
            group = get_object_or_404(WordGroup, id=group_id, user=request.user)
            group.delete()
            return redirect('groups')
        
        elif word_ids:
            Word.objects.filter(id__in=word_ids, user=request.user).delete()
            return redirect('words')

        return redirect('profile')

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
    paginate_by = 25
    model = Word
    template_name = 'med/words.html'
    context_object_name = 'words'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"{self.request.user.username}'s Dictionary"
        return context

    def get_queryset(self):
        return Word.objects.filter(user=self.request.user)


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
        return redirect('profile')


class LoginUser(LoginView):
    form_class =  LoginUserForm
    template_name = 'med/login.html'
    extra_context = {'title': 'Log in'}

    def get_success_url(self):
        return reverse_lazy('profile')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request, *args, **kwargs):
        recent_words = Word.objects.filter(user=request.user)[:5]
        word_count = Word.objects.filter(user=request.user).count()
        group_count = WordGroup.objects.filter(user=request.user).count()
        return render(request, 'med/profile.html', {'recent_words': recent_words, 'word_count': word_count, 'group_count': group_count})
    

def logout_user(request):
    logout(request)
    return redirect('login')

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>404 Page Not Found</h1>")