from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from django.db.models import Q

from django.core.paginator import Paginator

from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Friendship
from notifications.models import Notification
from dictionary.models import Word, WordGroup
from practice.models import CommunityGroup
from django.contrib.auth.models import User

from notifications.views import create_notification
from achievements.signals import AchievementProcessor

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def user_search(request):
    query = request.GET.get('q')
    users = User.objects.filter(username__icontains=query) if query else []
    friends = User.objects.filter(
        Q(friendship_requests_sent__receiver=request.user, friendship_requests_sent__status='accepted') |
        Q(friendship_requests_received__sender=request.user, friendship_requests_received__status='accepted')
    ).distinct()

    friendships = Friendship.objects.filter(
        (Q(sender=request.user) & Q(receiver__in=friends)) | (Q(receiver=request.user) & Q(sender__in=friends))
    )

    friend_requests_in = Friendship.objects.filter(receiver=request.user, status='pending').values_list('sender_id', flat=True)
    friend_requests_out = Friendship.objects.filter(sender=request.user, status='pending').values_list('receiver_id', flat=True)

    for user in users:
        friendship = friendships.filter(sender=user, receiver=request.user).first() or friendships.filter(sender=request.user, receiver=user).first()
        user.friendship_id = friendship.id if friendship else None

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    paginated_users = paginator.get_page(page_number)

    return render(request, 'friendship/user_search.html', {
        'users': paginated_users,
        'query': query,
        'friends': friends,
        'friend_requests_in': friend_requests_in,
        'friend_requests_out': friend_requests_out,
        'is_search': True,
        'paginator': paginator,
    })

@login_required
def send_friend_request(request, username):
    receiver = get_object_or_404(User, username=username)
    referer = request.META.get('HTTP_REFERER', reverse('profile', kwargs={'user_name': request.user.username}))

    if receiver == request.user:
        return HttpResponseRedirect(referer)
    
    friendship, created = Friendship.objects.get_or_create(sender=request.user, receiver=receiver)

    create_notification(
        receiver=receiver,
        message=f"{request.user.username} sent you a friend request",
        type='3',
        friendship_id=friendship.pk,
    )

    return HttpResponseRedirect(referer)

@login_required
def cancel_friend_request(request, username):
    receiver = get_object_or_404(User, username=username)
    referer = request.META.get('HTTP_REFERER', reverse('profile', kwargs={'user_name': request.user.username}))

    friendship = Friendship.objects.filter(sender=request.user, receiver=receiver, status='pending').first()
    
    if not friendship:
        return HttpResponseRedirect(referer)
    
    friendship.delete()
    
    return HttpResponseRedirect(referer)

@login_required
def respond_to_friend_request(request, friendship_id=None, user1_id=None, user2_id=None, response=None):
    referer = request.META.get('HTTP_REFERER', reverse('profile', kwargs={'user_name': request.user.username}))

    if friendship_id:
        friendship = get_object_or_404(Friendship, id=friendship_id)
    elif user1_id and user2_id:
        user1 = get_object_or_404(User, id=user1_id)
        user2 = get_object_or_404(User, id=user2_id)
        friendship = Friendship.objects.filter(
            (Q(sender=user1) & Q(receiver=user2)) | 
            (Q(sender=user2) & Q(receiver=user1)), 
            status='pending'
        ).first()
        if not friendship:
            return HttpResponseRedirect(referer)
    else:
        return HttpResponseRedirect(referer)

    if friendship.receiver != request.user:
        return HttpResponseRedirect(referer)

    if response == 'accept':
        friendship.status = 'accepted'
        friendship.save()
    elif response == 'reject':
        friendship.delete()

    return HttpResponseRedirect(referer)

def delete_friend(request, friendship_id):
    friendship = get_object_or_404(Friendship, id=friendship_id)

    if friendship.sender == request.user or friendship.receiver == request.user:
        friendship.delete()

    return redirect('friends_list', user_name=request.user.username)

@login_required
def friends_list_view(request, user_name):
    user = get_object_or_404(User, username=user_name)
    is_my_friends = user == request.user

    friendships = Friendship.objects.filter(
        Q(sender=user, status='accepted') |
        Q(receiver=user, status='accepted')
    ).select_related('sender', 'receiver')

    friends = [
        friendship.sender if friendship.receiver == user else friendship.receiver
        for friendship in friendships
    ]

    friend_requests_in = Friendship.objects.filter(receiver=user, status='pending').select_related('sender')
    friend_requests_out = Friendship.objects.filter(sender=user, status='pending').select_related('receiver')

    for friend in friends:
        friendship = friendships.filter(sender=friend, receiver=request.user).first() or friendships.filter(sender=request.user, receiver=friend).first()
        friend.friendship_id = friendship.id if friendship else None

    return render(request, 'friendship/friends_list.html', {
        'user': user,
        'friends': friends,
        'friend_requests_in': friend_requests_in,
        "in_count": friend_requests_in.count(),
        'friend_requests_out': friend_requests_out,
        'is_my_friends': is_my_friends,
    })

def send_group_to_friend(request, group_id, user_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    group = WordGroup.objects.get(user=request.user, id=group_id)
    user = User.objects.get(id=user_id)
    if group:
        create_notification(
            receiver=user,
            message="Your friend {request.user} sends you an invitation to save his group '{group.name}'",
            type='2',
            group=group,
        )

        return redirect('groups')
    else:
        return redirect('groups')

class FriendGroupWordsListView(LoginRequiredMixin, ListView):
    model = Word
    template_name = 'friendship/friend_group_words.html'
    context_object_name = 'words'
    paginate_by = 25

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)

        user_word_titles = [word.word.lower() for word in Word.objects.filter(user=self.request.user)]

        words = group.words.all()
        for word in words:
                word.is_saved = word.word.lower() in user_word_titles

        return words
    
    def get_context_data(self, **kwargs):
        processor = AchievementProcessor()
        processor.process_interaction_achievements(self.request.user)

        context = super().get_context_data(**kwargs)
        group_id = self.kwargs.get('group_id')
        group = get_object_or_404(WordGroup, id=group_id)
        notif_id = self.kwargs.get('notif_id')
        context['group'] = group

        context['notif_id'] = notif_id
        notif = Notification.objects.get(id=notif_id)
        notif.is_read = True
        notif.save()
        context['is_usses'] = group.uses_users.filter(id=self.request.user.id).exists()
        if CommunityGroup.objects.filter(group=context['group'], state='added').exists():
            context['is_community'] = True
        else:
            context['is_community'] = False
        return context

def accept_friend_group(request, notif_id):
    notif = Notification.objects.get(id=notif_id)

    group = notif.group
    if group:
        group.uses_users.add(request.user)

    return redirect('groups')

def decline_friend_group(request, notif_id):
    notif = Notification.objects.get(id=notif_id)
    
    if notif:
        notif.delete()
    
    return redirect('notifications')