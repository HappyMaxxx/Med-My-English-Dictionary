from django.contrib import admin
from .models import Word, WordGroup

class WordAdmin(admin.ModelAdmin):
    list_display = ('word', 'translation', 'time_create', 'time_update', 'word_type')
    list_display_links = ('word', 'translation')
    list_filter = ('user', 'time_create')
    search_fields = ('word', 'translation')

class WordGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_main')
    list_filter = ('name',)
    search_fields = ('name',)

admin.site.register(Word, WordAdmin)
admin.site.register(WordGroup, WordGroupAdmin)