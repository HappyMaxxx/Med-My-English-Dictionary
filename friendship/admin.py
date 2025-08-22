from django.contrib import admin
from .models import Friendship

class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('status', 'sender', 'receiver')
    list_filter = ('status',)
    search_fields = ('sender', 'receiver',)

admin.site.register(Friendship, FriendshipAdmin)