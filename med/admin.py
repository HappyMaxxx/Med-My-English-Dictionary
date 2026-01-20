from django.contrib import admin

from .models import *

class TopAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'place', 'points')
    list_filter = ('user', 'category', 'points')
    search_fields = ('user', 'category', 'place')


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_chat_id', 'is_bot_active')
    search_fields = ('user', 'telegram_chat_id', 'is_bot_active')


admin.site.register(Top, TopAdmin)
admin.site.register(UserProfile, UserProfileAdmin)