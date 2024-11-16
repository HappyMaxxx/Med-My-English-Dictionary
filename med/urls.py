from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('addword/', views.AddWordView.as_view(), name='addword'),
    path('confirm_delete/', views.ConfirmDeleteView.as_view(), name='confirm_delete'),
    path('words/', views.WordListView.as_view(), name='words'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('edit_word/<int:word_id>/', views.EditWordView.as_view(), name='edit_word'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('groups/', views.GroupListView.as_view(), name='groups'),
    path('groups/<int:group_id>/', views.GroupWordsView.as_view(), name='group_words'),
    path('create_group/', views.CreateGroupView.as_view(), name='create_group'),
    path('select_group/', views.SelectGroupView.as_view(), name='select_group'),
]