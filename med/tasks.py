from datetime import timezone
from mad.celery import app
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from med.models import *
from dictionary.models import Word
from django.db.models import Count, F
from django.db import transaction

@app.task
def send_activation_email(user_id):
    try:
        user = User.objects.get(pk=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{settings.SITE_URL}{reverse('activate_account', kwargs={'uidb64': uid, 'token': token})}"

        subject = "Activate your account"
        message = f"Hello {user.username},\n\nPlease click the link below to activate your account:\n{activation_link}"
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except User.DoesNotExist:
        pass

@app.task
def update_top():
    categories = {
        'words': calculate_words_top,
        'streak': calculate_streak_top,
        'logins': calculate_logins_top,
    }

    for category_name, calculation_func in categories.items():
        category, created = Category.objects.get_or_create(name=category_name)
        
        with transaction.atomic():
            Top.objects.filter(category=category).delete()
            
            new_top_data = calculation_func()

            for place, (user, points) in enumerate(new_top_data, start=1):
                Top.objects.create(category=category, user=user, place=place, points=points)

        category.save()

def calculate_words_top():
    word_counts = (
        Word.objects.values('user')  
        .annotate(points=Count('id'))  
        .order_by('-points')[:10]
    )
    return [(User.objects.get(pk=data['user']), data['points']) for data in word_counts]

def calculate_streak_top():
    streaks = []
    for user in User.objects.all():
        _, longest_streak, *_ = user.streak.get_streak_data()
        if longest_streak > 0:
            streaks.append((user, longest_streak))
    streaks.sort(key=lambda x: x[1], reverse=True)
    return streaks[:10]

def calculate_logins_top():
    login_counts = (
        UserLogin.objects.values('user')
        .annotate(points=Count('id'))
        .order_by('-points')[:10]
    )
    return [(User.objects.get(pk=data['user']), data['points']) for data in login_counts]