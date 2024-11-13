from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('addword/', views.AddWordView.as_view(), name='addword'),
    path('confirm_delete/', views.ConfirmDeleteWordsView.as_view(), name='confirm_delete_words'),
    path('words/', views.WordListView.as_view(), name='words'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('edit_word/<int:word_id>/', views.EditWordView.as_view(), name='edit_word'),
]