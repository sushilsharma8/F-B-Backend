from django.db import models
from backend import settings
from apps.providers.models import ServiceProviderProfile

class Event(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events'
    )
    date = models.DateTimeField()
    address = models.CharField(max_length=255)
    guest_count = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('matched', 'Matched'),
            ('confirmed', 'Confirmed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    additional_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Event by {self.client.name} on {self.date}"

class Service(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='services'
    )
    category = models.CharField(
        max_length=20,
        choices=[
            ('chef', 'Chef'),
            ('bartender', 'Bartender'),
            ('server', 'Server'),
        ]
    )
    provider = models.ForeignKey(
        ServiceProviderProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services'
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('matched', 'Matched'),
            ('confirmed', 'Confirmed'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )

    def __str__(self):
        return f"{self.category} for {self.event}"

class ServiceMatch(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    provider = models.ForeignKey(
        ServiceProviderProfile,
        on_delete=models.CASCADE,
        related_name='event_matches'
    )
    proposed_rate = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('service', 'provider')

    def __str__(self):
        return f"Match: {self.provider} for {self.service}"
