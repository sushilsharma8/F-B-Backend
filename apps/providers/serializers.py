from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ServiceProviderProfile, Availability

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ('day_of_week', 'start_time', 'end_time')

class ServiceProviderProfileSerializer(serializers.ModelSerializer):
    availability = AvailabilitySerializer(many=True, read_only=True)
    
    class Meta:
        model = ServiceProviderProfile
        fields = (
            'id',
            'service_type',
            'experience',
            'phone',
            'address',
            'driving_license',
            'rating',
            'is_available',
            'availability'
        )

class ProviderApplicationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    service_type = serializers.ChoiceField(choices=['chef', 'bartender', 'server'])
    address = serializers.CharField()
    driving_license = serializers.CharField(allow_null=True, allow_blank=True)
    
    class Meta:
        model = ServiceProviderProfile
        fields = (
            'user_id',
            'service_type',
            'experience',
            'phone',
            'address',
            'driving_license',
            'interview_scheduled', 
            'google_meet_link', 
            'application_status'
        )

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        
        try:
            profile = ServiceProviderProfile.objects.get(user=user)
            #If profile already exists, update it instead of creating a new one.
            for key, value in validated_data.items():
                setattr(profile, key, value)
            profile.save()
            return profile
        except ServiceProviderProfile.DoesNotExist:
            profile = ServiceProviderProfile.objects.create(
                user=user,
                **validated_data
            )
            return profile

class ProviderDashboardStatsSerializer(serializers.Serializer):
    total_bookings = serializers.IntegerField()
    completed_events = serializers.IntegerField()
    upcoming_events = serializers.IntegerField()
    average_rating = serializers.FloatField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
