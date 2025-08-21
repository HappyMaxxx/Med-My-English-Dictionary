from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('confirm_delete/', views.ConfirmDeleteView.as_view(), name='confirm_delete'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/<slug:user_name>/', views.ProfileView.as_view(), name='profile'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('check-username/', views.check_username, name='check_username'),
    path('search/', views.user_search, name='user_search'),
    path('add-friend/<str:username>/', views.send_friend_request, name='add_friend'),
    path('respond-friend-request/<int:friendship_id>/<str:response>/', views.respond_to_friend_request, name='respond_friend_request'),
    path("respond_friend_request_a/<int:user1_id>/<int:user2_id>/<str:response>/", views.respond_to_friend_request, name='respond_friend_request_a'),
    path('friends/<slug:user_name>/', views.friends_list_view, name='friends_list'),
    path('delete_friend/<int:friendship_id>/', views.delete_friend, name='delete_friend'),
    path('download/<path:file>/', views.download_file, name='download_file'),
    path('soon/', views.soon_page, name='soon'),
    path('achievement/', views.achievement_view, name='achievement'),
    path('add_achievement/<int:ach_id>/', views.add_achievement, name='add_achievement'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    path('tops/', views.tops_by_category, name='tops_by_category'),
    path('api/get-tops-by-category/', views.api_get_tops_by_category, name='api_get_tops_by_category'),
    path("hide-warning/", views.hide_warning_message, name="hide-warning-message"),
    path('notifications/', views.NotiListView.as_view(), name='notifications'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('notification/<int:notification_id>/read/', views.mark_notification_as_read, name='mark_notification_read'),
    path('send_group_to_friend/<int:group_id>/<int:user_id>', views.send_group_to_friend, name='send_group_to_friend'),
    path('decline_friend_group/<int:notif_id>/', views.decline_friend_group, name='decline_friend_group'),
    path('accept_friend_group/<int:notif_id>/', views.accept_friend_group, name='accept_friend_group'),
    path('friend_group_words/<int:notif_id>/<int:group_id>/', views.FriendGroupWordsListView.as_view(), name='friend_group_words'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
