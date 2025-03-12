from django import template

register = template.Library()

@register.simple_tag
def get_unread_notifications_count(request):
    if request.user.is_authenticated:
        return request.user.notification_set.filter(is_read=False).count()
    return 0

@register.simple_tag
def get_latest_unread_notifications(request, limit=5):
    if request.user.is_authenticated:
        return request.user.notification_set.filter(is_read=False)[:limit]
    return []