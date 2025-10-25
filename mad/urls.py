from django.contrib import admin
from django.urls import include, path, re_path
from med.views import page_not_found
from django.conf import settings
from django.conf.urls import handler404
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('med.urls')),
    path('', include('practice.urls')),
    path('', include('dictionary.urls')),
    path('', include('friendship.urls')),
    path('', include('achievements.urls')),
    path('', include('notifications.urls')),
    path('', include('sitepulse.urls')),
    path('', include('premium.urls')),
    path('', include('api.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),]
urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),]

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns

handler404 = page_not_found