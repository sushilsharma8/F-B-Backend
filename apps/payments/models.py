from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UpiTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, unique=True)
    upi_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)  # e.g., 'pending', 'success', 'failed'
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UPI Transaction - {self.transaction_id}"
