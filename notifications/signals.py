from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Notification)
def notification_updated(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    group_name = f'user_{instance.user_id}'

    notifications = Notification.objects.filter(
        user_id=instance.user_id, is_read=False
    ).order_by('-time_create')[:5]

    data = [
        {"message": n.message, "time": n.time_create.strftime("%d.%m.%Y %H:%M")}
        for n in notifications
    ]

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_notification',
            'count': notifications.count(),
            'notifications': data
        }
    )