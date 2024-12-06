from rest_framework import serializers
from .models import Event, Service, ServiceMatch
from apps.providers.serializers import ServiceProviderProfileSerializer

class ServiceSerializer(serializers.ModelSerializer):
    provider = ServiceProviderProfileSerializer(read_only=True)
    
    class Meta:
        model = Service
        fields = (
            'id',
            'category',
            'provider',
            'rate',
            'status'
        )

class ServiceMatchSerializer(serializers.ModelSerializer):
    provider = ServiceProviderProfileSerializer(read_only=True)
    
    class Meta:
        model = ServiceMatch
        fields = (
            'id',
            'provider',
            'proposed_rate',
            'status'
        )

class EventSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    matches = ServiceMatchSerializer(many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = (
            'id',
            'date',
            'address',
            'guest_count',
            'status',
            'additional_details',
            'services',
            'matches'
        )
        read_only_fields = ('status',)

    def create(self, validated_data):
        services_data = self.context['request'].data.get('services', [])
        event = Event.objects.create(
            client=self.context['request'].user,
            **validated_data
        )
        
        for service_type in services_data:
            Service.objects.create(
                event=event,
                category=service_type
            )
        
        return event