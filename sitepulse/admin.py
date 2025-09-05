from django.contrib import admin
from .models import Visit

class VisitAdmin(admin.ModelAdmin):
    list_display = ('timestamp',"ip_address",)
    list_filter = ('timestamp', "ip_address",) 
    search_fields = ('timestamp',)

admin.site.register(Visit, VisitAdmin)