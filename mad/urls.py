from django.contrib import admin
from django.urls import include, path
from debug_toolbar.toolbar import debug_toolbar_urls
from med.views import page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('med.urls')),
]+ debug_toolbar_urls()

hendler404 = page_not_found