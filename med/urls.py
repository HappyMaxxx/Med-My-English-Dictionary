from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('confirm_delete/', views.ConfirmDeleteView.as_view(), name='confirm_delete'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/<slug:user_name>/', views.ProfileView.as_view(), name='profile'),
    path('edit_profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('check-username/', views.check_username, name='check_username'),
    path('download/<path:file>/', views.download_file, name='download_file'),
    path('soon/', views.soon_page, name='soon'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate_account'),
    path('tops/', views.tops_by_category, name='tops_by_category'),
    path('api/get-tops-by-category/', views.api_get_tops_by_category, name='api_get_tops_by_category'),
    path("hide-warning/", views.hide_warning_message, name="hide-warning-message"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
