from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('addword/', views.addword, name='addword'),
    path('words/', views.WordListView.as_view(), name='words'),
]