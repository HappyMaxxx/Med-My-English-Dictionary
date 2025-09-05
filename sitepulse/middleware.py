from django.utils import timezone
from datetime import timedelta
from .models import Visit

class VisitTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = request.META.get('REMOTE_ADDR')
        now = timezone.now()
        one_hour_ago = now.replace(minute=0, second=0, microsecond=0)

        recent_visit = Visit.objects.filter(
            ip_address=ip_address,
            timestamp__gte=one_hour_ago
        ).exists()

        if not recent_visit:
            Visit.objects.create(
                ip_address=ip_address,
                page_url=request.path
            )

        response = self.get_response(request)
        return response