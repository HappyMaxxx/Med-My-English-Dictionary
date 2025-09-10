from django.urls import path
from . import views

urlpatterns = [
    path('subscriptions/', views.subscriptions, name='subscriptions'),
    path('subscribe/<str:plan>/', views.subscribe, name='subscribe'),
    path('faq/', views.faq, name='faq'),
]