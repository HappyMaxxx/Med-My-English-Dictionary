from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
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
    path('profile/<slug:user_name>/', views.ProfileView.as_view(), name='profile'),
    path('groups/', views.GroupListView.as_view(), name='groups'),
    path('groups/<int:group_id>/', views.GroupWordsView.as_view(), name='group_words'),
    path('create_group/', views.CreateGroupView.as_view(), name='create_group'),
    path('select_group/', views.SelectGroupView.as_view(), name='select_group'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('make_favourite/<int:word_id>/', views.make_favourite, name='make_favourite'),
    path('check-username/', views.check_username, name='check_username'),
    path('search/', views.user_search, name='user_search'),
    path('add-friend/<str:username>/', views.send_friend_request, name='add_friend'),
    path('respond-friend-request/<int:friendship_id>/<str:response>/', views.respond_to_friend_request, name='respond_friend_request'),
    path("respond_friend_request_a/<int:user1_id>/<int:user2_id>/<str:response>/", views.respond_to_friend_request, name='respond_friend_request_a'),
    path('friends/<slug:user_name>/', views.friends_list_view, name='friends_list'),
    path('delete_friend/<int:friendship_id>/', views.delete_friend, name='delete_friend'),
    path('practice/', views.practice_view, name='practice'),
    path('practice/reading/', views.reading_view, name='practice_reading'),
    path('practice/reading/<int:text_id>/', views.reading_text_view, name='reading_text'),
    path('word/<int:text_id>/<str:word>/', views.word_detail_view, name='word_detail'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)