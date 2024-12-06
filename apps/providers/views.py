from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from backend.logger import log
from logging import INFO, ERROR
from django.db.models import Sum, Count, Avg
from .models import ServiceProviderProfile, Availability
from .serializers import (
    ServiceProviderProfileSerializer,
    ProviderApplicationSerializer,
    AvailabilitySerializer,
    ProviderDashboardStatsSerializer
)
from apps.events.models import Event
from apps.events.serializers import EventSerializer, ServiceMatchSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

class ProviderViewSet(viewsets.ModelViewSet):
    queryset = ServiceProviderProfile.objects.all()
    serializer_class = ServiceProviderProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.action == 'apply':
            return ProviderApplicationSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'])
    def apply(self, request):
        log(level=INFO, function="ProviderViewSet", message="Applying for provider")
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            provider = serializer.save()
            return Response(
                ServiceProviderProfileSerializer(provider).data,
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            log(level=ERROR, function="ProviderViewSet", message=f"Validation error during provider application: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log(level=ERROR, function="ProviderViewSet", message=f"Unexpected error during provider application: {e}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False)
    def dashboard(self, request):
        try:
            provider = request.user.profile
            events = Event.objects.filter(provider=provider)
            stats = events.aggregate(
                total_bookings=Count('id'),
                completed_events=Count('id', filter=Q(status='completed')),
                upcoming_events=Count('id', filter=Q(status='confirmed')),
                total_earnings=Sum('rate'),
                average_rating=Avg('rate')
            )
            stats['average_rating'] = stats['average_rating'] or 0
            stats['total_earnings'] = stats['total_earnings'] or 0
            serializer = ProviderDashboardStatsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            log(level=ERROR, function="ProviderViewSet", message=f"Error fetching dashboard stats for provider {provider.id if provider else 'unknown'}: {e}")
            return Response({"error": "Failed to fetch dashboard stats."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False)
    def upcoming_events(self, request):
        try:
            provider = request.user.profile
            events = provider.events.filter(status='confirmed')
            return Response(EventSerializer(events, many=True).data)
        except Exception as e:
            log(level=ERROR, function="ProviderViewSet", message=f"Error fetching upcoming events for provider {request.user.id}: {e}")
            return Response({"error": "Failed to fetch upcoming events."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False)
    def event_requests(self, request):
        try:
            provider = request.user.profile
            requests = provider.event_matches.filter(status='pending')
            return Response(ServiceMatchSerializer(requests, many=True).data)
        except Exception as e:
            log(level=ERROR, function="ProviderViewSet", message=f"Error fetching event requests for provider {request.user.id}: {e}")
            return Response({"error": "Failed to fetch event requests."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['put'])
    def availability(self, request):
        provider = request.user.profile
        serializer = AvailabilitySerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        Availability.objects.filter(provider=provider).delete()
        availability_objects = [
            Availability(provider=provider, **item)
            for item in serializer.validated_data
        ]
        Availability.objects.bulk_create(availability_objects)
        
        return Response(serializer.data)
