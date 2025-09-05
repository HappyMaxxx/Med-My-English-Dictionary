from django.db import models

class Visit(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45)
    page_url = models.CharField(max_length=200)

    def __str__(self):
        return f"Visit at {self.timestamp} from {self.ip_address}"