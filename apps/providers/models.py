from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator

class ServiceProviderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    service_type = models.CharField(
        max_length=20,
        choices=[
            ('chef', 'Chef'),
            ('bartender', 'Bartender'),
            ('server', 'Server'),
        ]
    )
    experience = models.TextField(help_text="Please describe your professional experience in detail.")
    phone = models.CharField(max_length=20, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be in the format: '+999999999'. Up to 15 digits allowed.")])
    address = models.TextField()
    driving_license = models.CharField(max_length=20, blank=True, null=True)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    interview_scheduled = models.DateTimeField(null=True, blank=True)
    google_meet_link = models.URLField(null=True, blank=True)
    application_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.service_type}"

class Availability(models.Model):
    provider = models.ForeignKey(
        ServiceProviderProfile,
        on_delete=models.CASCADE,
        related_name='availability'
    )
    day_of_week = models.IntegerField(
        choices=[
            (0, 'Monday'),
            (1, 'Tuesday'),
            (2, 'Wednesday'),
            (3, 'Thursday'),
            (4, 'Friday'),
            (5, 'Saturday'),
            (6, 'Sunday'),
        ]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('provider', 'day_of_week')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.provider.user.username} - {self.get_day_of_week_display()}"
