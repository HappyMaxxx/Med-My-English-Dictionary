from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    path('search/', views.user_search, name='user_search'),
    path('add-friend/<str:username>/', views.send_friend_request, name='add_friend'),
    path('respond-friend-request/<int:friendship_id>/<str:response>/', views.respond_to_friend_request, name='respond_friend_request'),
    path("respond_friend_request_a/<int:user1_id>/<int:user2_id>/<str:response>/", views.respond_to_friend_request, name='respond_friend_request_a'),
    path('cancel_friend_request/<str:username>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('friends/<slug:user_name>/', views.friends_list_view, name='friends_list'),
    path('delete_friend/<int:friendship_id>/', views.delete_friend, name='delete_friend'),
    path('send_group_to_friend/<int:group_id>/<int:user_id>', views.send_group_to_friend, name='send_group_to_friend'),
    path('decline_friend_group/<int:notif_id>/', views.decline_friend_group, name='decline_friend_group'),
    path('accept_friend_group/<int:notif_id>/', views.accept_friend_group, name='accept_friend_group'),
    path('friend_group_words/<int:notif_id>/<int:group_id>/', views.FriendGroupWordsListView.as_view(), name='friend_group_words'),
]
