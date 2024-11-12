from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.views.generic import ListView, CreateView

from med.forms import AddWordForm
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

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>404 Page Not Found</h1>")