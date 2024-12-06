from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.db.models import Q
from .models import Event, ServiceMatch, Service
from .serializers import EventSerializer, ServiceMatchSerializer, ServiceSerializer
from apps.providers.models import ServiceProviderProfile
from backend.logger import log
from logging import INFO, ERROR
from rest_framework.pagination import PageNumberPagination
from django.db.models import Prefetch
from apps.payments.models import UpiTransaction
from apps.payments.serializers import UpiTransactionSerializer
from django.http import Http404

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Event.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        event = serializer.save()
        self._create_matches(event)

    def _create_matches(self, event):
        for service in event.services.all():
            available_providers = ServiceProviderProfile.objects.filter(
                service_type=service.category,
                is_available=True
            )
            
            for provider in available_providers[:3]:
                ServiceMatch.objects.create(
                    service=service,
                    provider=provider,
                    proposed_rate=100
                )

    @action(detail=True)
    def matches(self, request, pk=None):
        event = self.get_object()
        matches = ServiceMatch.objects.filter(
            service__event=event,
            status='pending'
        ).prefetch_related(Prefetch('service', queryset=Service.objects.select_related('event')))
        log(level=INFO, function='matches', message=f"Matches queryset: {matches}")
        serializer = ServiceMatchSerializer(matches, many=True)
        log(level=INFO, function='matches', message=f"Serialized matches: {serializer.data}")
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='matches/(?P<match_id>[^/.]+)/accept')
    def accept_match(self, request, pk=None, match_id=None):
        event = self.get_object()
        try:
            match = ServiceMatch.objects.get(
                id=match_id,
                service__event=event,
                status='pending'
            )
            match.status = 'accepted'
            match.save()
            
            service = match.service
            service.provider = match.provider
            service.rate = match.proposed_rate
            service.status = 'confirmed'
            service.save()
            
            ServiceMatch.objects.filter(
                service=service,
                status='pending'
            ).exclude(id=match.id).update(status='declined')
            
            return Response(ServiceMatchSerializer(match).data)
        except ServiceMatch.DoesNotExist:
            return Response(
                {'error': 'Match not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='matches/(?P<match_id>[^/.]+)/decline')
    def decline_match(self, request, pk=None, match_id=None):
        event = self.get_object()
        try:
            match = ServiceMatch.objects.get(
                id=match_id,
                service__event=event,
                status='pending'
            )
            match.status = 'declined'
            match.save()
            return Response(ServiceMatchSerializer(match).data)
        except ServiceMatch.DoesNotExist:
            return Response(
                {'error': 'Match not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='initiate-upi-payment')
    def initiate_upi_payment(self, request, pk=None):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            raise Http404

        amount = request.data.get('amount')
        if amount is None:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)

        upi_transaction = UpiTransaction.objects.create(
            user=request.user,
            event=event,
            transaction_id='temp_id',  # Replace with actual transaction ID generation
            upi_id=request.data.get('upi_id'),
            amount=amount,
            status='pending'
        )

        serializer = UpiTransactionSerializer(upi_transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = PageNumberPagination

class ServiceMatchViewSet(viewsets.ModelViewSet):
    queryset = ServiceMatch.objects.all()
    serializer_class = ServiceMatchSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = PageNumberPagination
