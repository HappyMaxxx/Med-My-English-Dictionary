from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from med.forms import AddWordForm, RegisterUserForm, LoginUserForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, login
from med.models import *

def index(request):
    return render(request, 'med/index.html')

def about(request):
    return render(request, 'med/about.html')


class AddWordView(CreateView):
    form_class = AddWordForm
    template_name = 'med/addword.html'
    success_url = '/words'
    extra_context = {'title': 'Add Word'}


class WordListView(ListView):
    paginate_by = 25
    model = Word
    template_name = 'med/words.html'
    context_object_name = 'words'
    extra_context = {'title': "'s dictionary"}


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
    extra_context = {'title': 'Login'}

    def get_success_url(self):
        return reverse_lazy('home')



def logout_user(request):
    logout(request)
    return redirect('login')

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>404 Page Not Found</h1>")