from mad.celery import app
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from med.models import User

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