from django.http import HttpResponseNotFound
from django.shortcuts import render

def index(request):
    return render(request, 'med/index.html')

def about(request):
    return render(request, 'med/about.html')

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена</h1>")