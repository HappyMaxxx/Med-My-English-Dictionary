from django.db import models
from django.contrib.auth.models import User

class Friendship(models.Model):
    sender = models.ForeignKey(User, related_name="friendship_requests_sent", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="friendship_requests_received", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')