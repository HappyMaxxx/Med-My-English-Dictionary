from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from med.forms import AddWordForm, RegisterUserForm, LoginUserForm

from django.views.generic import ListView, CreateView
from django.contrib.auth.views import LoginView
from django.views.generic.edit import DeleteView
from django.views import View

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.contrib.auth import logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from med.models import *

def index(request):
    return render(request, 'med/index.html')

def about(request):
    return render(request, 'med/about.html')


class AddWordView(LoginRequiredMixin, CreateView):
    form_class = AddWordForm
    template_name = 'med/addword.html'
    success_url = reverse_lazy('words')
    extra_context = {'title': 'Add Word'}

    def form_valid(self, form):
        word = form.save(commit=False)
        word.user = self.request.user
        word.save() 

        return super().form_valid(form)



@method_decorator(login_required, name='dispatch')
class ConfirmDeleteWordsView(View):
    def get(self, request, *args, **kwargs):
        word_ids = request.GET.getlist('word_ids')

        if not word_ids:
            return redirect('words')

        words = Word.objects.filter(id__in=word_ids, user=request.user)

        if not words:
            return redirect('words')

        return render(request, 'med/confirm_delete.html', {
            'words': words,
            'word_ids': word_ids
        })

    def post(self, request, *args, **kwargs):
        word_ids = request.POST.getlist('word_ids')
        if word_ids:
            Word.objects.filter(id__in=word_ids, user=request.user).delete()
        return redirect('words')

class WordListView(ListView):
    paginate_by = 25
    model = Word
    template_name = 'med/words.html'
    context_object_name = 'words'
    extra_context = {'title': "'s dictionary"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"{self.request.user.username}'s Dictionary"
        return context

    def get_queryset(self):
        return Word.objects.filter(user=self.request.user)


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'med/register.html'
    success_url = '/login'
    extra_context = {'title': 'Register'}

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('home')


class LoginUser(LoginView):
    form_class =  LoginUserForm
    template_name = 'med/login.html'
    extra_context = {'title': 'Log in'}

    def get_success_url(self):
        return reverse_lazy('home')



def logout_user(request):
    logout(request)
    return redirect('login')

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>404 Page Not Found</h1>")