from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Visit
from collections import defaultdict
import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from datetime import datetime

@login_required
def stats_view(request):
    if not request.user.is_staff:
        return redirect('profile', user_name=request.user.username)

    kyiv_tz = timezone.get_current_timezone()
    
    # Get selected date from GET parameters or use today
    selected_date_str = request.GET.get('selected_date')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date() if selected_date_str else timezone.now().astimezone(kyiv_tz).date()
    except ValueError:
        return HttpResponseBadRequest("Invalid date format")

    # Get selected month from GET parameters or use current month
    selected_month_str = request.GET.get('selected_month')
    try:
        selected_month = datetime.strptime(selected_month_str, '%Y-%m').date() if selected_month_str else selected_date.replace(day=1)
    except ValueError:
        return HttpResponseBadRequest("Invalid month format")

    # Calculate month start and end for monthly stats
    month_start = selected_month.replace(day=1)
    month_end = (month_start.replace(month=month_start.month % 12 + 1, day=1) - timezone.timedelta(days=1)) if month_start.month != 12 else month_start.replace(year=month_start.year + 1, month=1, day=31)

    # Hourly visits for selected date
    hourly_visits = defaultdict(set)
    visits_selected_date = Visit.objects.filter(
        timestamp__date=selected_date
    )
    for visit in visits_selected_date:
        hour = visit.timestamp.astimezone(kyiv_tz).hour
        hourly_visits[hour].add(visit.ip_address)

    # Monthly visits for selected month
    monthly_visits = defaultdict(set)
    visits_month = Visit.objects.filter(
        timestamp__gte=month_start,
        timestamp__lte=month_end
    )
    for visit in visits_month:
        day = visit.timestamp.astimezone(kyiv_tz).day
        monthly_visits[day].add(visit.ip_address)

    # Prepare data for charts
    hourly_labels = list(range(24))
    hourly_data = [len(hourly_visits[hour]) for hour in hourly_labels]
    monthly_labels = list(range(1, (month_end.day + 1)))
    monthly_data = [len(monthly_visits[day]) for day in monthly_labels]

    context = {
        'hourly_data': json.dumps(hourly_data),
        'hourly_labels': json.dumps(hourly_labels),
        'monthly_data': json.dumps(monthly_data),
        'monthly_labels': json.dumps(monthly_labels),
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'selected_month': month_start.strftime('%Y-%m'),
    }
    return render(request, 'sitepulse/stats.html', context)