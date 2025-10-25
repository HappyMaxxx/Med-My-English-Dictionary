from django.urls import path
from .views import TokenView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('token/', TokenView.as_view(), name='token'),
]