from django.contrib import admin
from .models import ServiceProviderProfile, Availability

@admin.register(ServiceProviderProfile)
class ServiceProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_type', 'rating', 'is_available')
    list_filter = ('service_type', 'is_available')
    search_fields = ('user__email', 'user__name')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('provider', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week',)