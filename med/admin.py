from django.contrib import admin

from .models import *

class TopAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'place', 'points')
    list_filter = ('user', 'category', 'points')
    search_fields = ('user', 'category', 'place')

admin.site.register(Top, TopAdmin)