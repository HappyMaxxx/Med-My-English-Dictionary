from django.contrib import admin
from django.urls import include, path
from med.views import page_not_found
from django.conf import settings
from django.conf.urls import handler404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('med.urls')),
    path('', include('practice.urls')),
    path('', include('dictionary.urls')),
    path('', include('friendship.urls')),
    path('', include('achievements.urls')),
    path('', include('notifications.urls')),
]

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns

handler404 = page_not_found