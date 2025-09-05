from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Visit
from collections import defaultdict
import json
from django.contrib.auth.decorators import login_required

@login_required
def stats_view(request):
    if not request.user.is_staff:
        return redirect('profile', user_name=request.user.username)

    kyiv_tz = timezone.get_current_timezone()
    today = timezone.now().astimezone(kyiv_tz).date()
    month_start = today.replace(day=1)

    hourly_visits = defaultdict(set)
    visits_today = Visit.objects.filter(timestamp__date=today)
    for visit in visits_today:
        hour = visit.timestamp.astimezone(kyiv_tz).hour
        hourly_visits[hour].add(visit.ip_address)

    monthly_visits = defaultdict(set)
    visits_month = Visit.objects.filter(timestamp__gte=month_start)
    for visit in visits_month:
        day = visit.timestamp.astimezone(kyiv_tz).day
        monthly_visits[day].add(visit.ip_address)

    hourly_labels = list(range(24))
    hourly_data = [len(hourly_visits[hour]) for hour in hourly_labels]
    monthly_labels = list(range(1, (today - month_start).days + 2))
    monthly_data = [len(monthly_visits[day]) for day in monthly_labels]

    context = {
        'hourly_data': json.dumps(hourly_data),
        'hourly_labels': json.dumps(hourly_labels),
        'monthly_data': json.dumps(monthly_data),
        'monthly_labels': json.dumps(monthly_labels),
    }
    return render(request, 'sitepulse/stats.html', context)