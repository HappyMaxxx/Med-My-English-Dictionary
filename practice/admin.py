from django.contrib import admin
from .models import ReadingText, CommunityGroup

class TextAdmin(admin.ModelAdmin):
    list_display = ('title',"eng_level",)
    list_filter = ('title', "eng_level",) 
    search_fields = ('title',)

class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = ('group', "state",)
    list_filter = ('state',) 

admin.site.register(ReadingText, TextAdmin)
admin.site.register(CommunityGroup, CommunityGroupAdmin)