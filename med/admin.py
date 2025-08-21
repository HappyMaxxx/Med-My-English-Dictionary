from django.contrib import admin

from .models import *


class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('status', 'sender', 'receiver')
    list_filter = ('status',)
    search_fields = ('sender', 'receiver',)


class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description','icon', 'level', 'ach_type')
    list_filter = ('name', 'description')
    search_fields = ('name', 'description')


class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'time_get')
    list_filter = ('user', 'achievement')
    search_fields = ('user', 'achievement')

class TopAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'place', 'points')
    list_filter = ('user', 'category', 'points')
    search_fields = ('user', 'category', 'place')

admin.site.register(Friendship, FriendshipAdmin)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserAchievement, UserAchievementAdmin)
admin.site.register(Top, TopAdmin)