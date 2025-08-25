from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from django.contrib.auth.decorators import login_required

from django.http import JsonResponse

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from .models import Notification

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotiListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/notification.html'
    context_object_name = 'notifications'
    paginate_by = 25

    def get_queryset(self):
        user_name = self.request.user.username
        user = get_object_or_404(User, username=user_name)

        queryset = Notification.objects.filter(user=user).order_by('-time_create')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_name = self.request.user.username
        user = get_object_or_404(User, username=user_name)

        context.update({
            'user': user,
            'title': f"{user_name}'s Notifications",
        })
        return context


@login_required
def notifications_api(request):
    user = request.user
    unread_notifications = Notification.objects.filter(user=user, is_read=False).order_by('-time_create')[:5]
    count = unread_notifications.count()
    
    notifications_list = [
        {
            "message": n.message,
            "time": n.time_create.strftime("%d.%m.%Y %H:%M")
        } for n in unread_notifications
    ]

    return JsonResponse({
        "count": count,
        "notifications": notifications_list
    })

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    return JsonResponse({'status': 'success', 'is_read': True})

def create_notification(receiver, message, type='1', is_read=False, group=None, friendship_id=None):
    try:
        Notification.objects.create(
            user=receiver,
            message=message,
            is_read=is_read,
            type=type,
            group=group,
            friendship_id=friendship_id,
        )
        return 0
    except:
        return 1