from django.contrib import admin
from django.urls import include, path
from med.views import page_not_found
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('med.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

hendler404 = page_not_found