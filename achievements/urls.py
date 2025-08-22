from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    path('achievement/', views.achievement_view, name='achievement'),
    path('add_achievement/<int:ach_id>/', views.add_achievement, name='add_achievement'),
]