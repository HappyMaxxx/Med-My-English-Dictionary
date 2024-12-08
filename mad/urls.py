from django.contrib import admin
from django.urls import include, path
from med.views import page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('med.urls')),
]

hendler404 = page_not_found