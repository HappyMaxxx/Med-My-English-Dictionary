from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('addword/', views.AddWordView.as_view(), name='addword'),
    path('confirm_delete/', views.ConfirmDeleteView.as_view(), name='confirm_delete'),
    path('words/<slug:user_name>', views.WordListView.as_view(), name='words'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('edit_word/<int:word_id>/', views.EditWordView.as_view(), name='edit_word'),
    path('profile/<slug:user_name>', views.ProfileView.as_view(), name='profile'),
    path('groups/', views.GroupListView.as_view(), name='groups'),
    path('groups/<int:group_id>/', views.GroupWordsView.as_view(), name='group_words'),
    path('create_group/', views.CreateGroupView.as_view(), name='create_group'),
    path('select_group/', views.SelectGroupView.as_view(), name='select_group'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('make_favourite/<int:word_id>', views.make_favourite, name='make_favourite'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)