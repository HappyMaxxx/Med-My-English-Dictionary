from django.urls import path
from .views import (TokenView, WordDetailView, WordListCreateView)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('api/v1/token/', TokenView.as_view(), name='token'),
    path('api/v1/words/', WordListCreateView.as_view(), name='word-list-create'),
    path('api/v1/words/<int:pk>/', WordDetailView.as_view(), name='word-detail'),
]