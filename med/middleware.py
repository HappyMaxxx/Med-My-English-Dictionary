from django.utils.timezone import now
from .models import UserLogin

class TrackUserVisitsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            today = now().date()

            UserLogin.objects.get_or_create(user=request.user, date=today)

        response = self.get_response(request)
        return response
