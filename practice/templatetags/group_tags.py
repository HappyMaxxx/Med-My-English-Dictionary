from django import template
from practice.models import CommunityGroup

register = template.Library()

@register.simple_tag
def get_user_pending_groups(request):
    if request.user.is_authenticated:
        groups = CommunityGroup.objects.filter(
            group__user=request.user,
        ).select_related('group') 

        word_groups = [community_group.group for community_group in groups]
        return word_groups
    return []