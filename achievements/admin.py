from django.contrib import admin
from .models import Achievement, UserAchievement

class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'description','icon', 'level', 'ach_type')
    list_filter = ('name', 'description')
    search_fields = ('name', 'description')


class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'time_get')
    list_filter = ('user', 'achievement')
    search_fields = ('user', 'achievement')

admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserAchievement, UserAchievementAdmin)