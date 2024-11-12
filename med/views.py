from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.views.generic import ListView

from med.forms import AddWordForm
from med.models import *

def index(request):
    return render(request, 'med/index.html')

def about(request):
    return render(request, 'med/about.html')

def addword(request):
    if request.method == 'POST':
        form = AddWordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('words')

    else:
        form = AddWordForm()

    return render(request, 'med/addword.html', {'title': 'Add New Word', 'form': form})


class WordListView(ListView):
    model = Word
    template_name = 'med/words.html'
    context_object_name = 'words'

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>404 Page Not Found</h1>")