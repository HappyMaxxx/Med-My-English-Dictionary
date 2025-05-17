from django.contrib import admin

from .models import *


class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'translation', 'time_create', 'time_update', 'word_type')
    list_display_links = ('word', 'translation')
    list_filter = ('user', 'time_create')
    search_fields = ('word', 'translation')


class WordGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_main')
    list_filter = ('name',)
    search_fields = ('name',)


class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('status', 'sender', 'receiver')
    list_filter = ('status',)
    search_fields = ('sender', 'receiver',)


class TextAdmin(admin.ModelAdmin):
    list_display = ('title',"eng_level",)
    list_filter = ('title', "eng_level",) 
    search_fields = ('title',)


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

admin.site.register(Word, WordAdmin)
admin.site.register(WordGroup, WordGroupAdmin)
admin.site.register(Friendship, FriendshipAdmin)
admin.site.register(ReadingText, TextAdmin)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserAchievement, UserAchievementAdmin)
admin.site.register(Top, TopAdmin)