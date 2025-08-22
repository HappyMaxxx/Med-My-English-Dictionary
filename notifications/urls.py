from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.NotiListView.as_view(), name='notifications'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('notification/<int:notification_id>/read/', views.mark_notification_as_read, name='mark_notification_read'),
]
