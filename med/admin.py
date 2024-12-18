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

admin.site.register(Word, WordAdmin)
admin.site.register(WordGroup, WordGroupAdmin)
admin.site.register(Friendship, FriendshipAdmin)
admin.site.register(ReadingText, TextAdmin)