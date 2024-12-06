import unittest
from decimal import Decimal
from django.test import TestCase
from .models import Event, Service, ServiceMatch
from apps.providers.models import ServiceProviderProfile
from django.contrib.auth.models import User
from datetime import datetime, time
from .serializers import EventSerializer, ServiceSerializer, ServiceMatchSerializer
from rest_framework.test import APIRequestFactory
from rest_framework import status
from unittest import expectedFailure
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

class EventModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        self.provider = ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=5, phone='123-456-7890')

    def test_event_creation(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        self.assertEqual(event.status, 'pending')
        self.assertEqual(str(event), f"Event by {self.user.name} on 2024-05-10 19:00:00")

    def test_event_creation_invalid_guest_count(self):
        with self.assertRaises(ValidationError) as context:
            Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=-1)
        self.assertTrue('Ensure this value is greater than or equal to 0.' in str(context.exception))

    def test_event_creation_invalid_status(self):
        with self.assertRaises(ValidationError) as context:
            Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10, status='invalid')
        self.assertTrue('invalid status' in str(context.exception))


    def test_service_creation(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        service = Service.objects.create(event=event, category='chef', provider=self.provider, rate=Decimal('100.00'))
        self.assertEqual(service.status, 'pending')
        self.assertEqual(str(service), f"chef for {event}")

    def test_servicematch_creation(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        service = Service.objects.create(event=event, category='chef', provider=self.provider, rate=Decimal('100.00'))
        match = ServiceMatch.objects.create(service=service, provider=self.provider, proposed_rate=Decimal('100.00'))
        self.assertEqual(match.status, 'pending')
        self.assertEqual(str(match), f"Match: {self.provider} for {service}")

    def test_service_unique_together(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        service = Service.objects.create(event=event, category='chef', provider=self.provider, rate=Decimal('100.00'))
        with self.assertRaises(Exception) as context:
            ServiceMatch.objects.create(service=service, provider=self.provider, proposed_rate=Decimal('100.00'))
        self.assertTrue('unique constraint' in str(context.exception))

    def test_service_invalid_rate(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        with self.assertRaises(Exception) as context:
            Service.objects.create(event=event, category='chef', provider=self.provider, rate='invalid')
        self.assertTrue('invalid literal' in str(context.exception))

    def test_service_invalid_category(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        with self.assertRaises(Exception) as context:
            Service.objects.create(event=event, category='invalid', provider=self.provider, rate=Decimal('100.00'))
        self.assertTrue('value is not a valid choice' in str(context.exception))

    def test_servicematch_invalid_status(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        service = Service.objects.create(event=event, category='chef', provider=self.provider, rate=Decimal('100.00'))
        with self.assertRaises(Exception) as context:
            ServiceMatch.objects.create(service=service, provider=self.provider, proposed_rate=Decimal('100.00'), status='invalid')
        self.assertTrue('value is not a valid choice' in str(context.exception))

    def test_servicematch_invalid_rate(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        service = Service.objects.create(event=event, category='chef', provider=self.provider, rate=Decimal('100.00'))
        with self.assertRaises(Exception) as context:
            ServiceMatch.objects.create(service=service, provider=self.provider, proposed_rate='invalid')
        self.assertTrue('invalid literal' in str(context.exception))

class EventSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')

    def test_event_serializer(self):
        event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        serializer = EventSerializer(event)
        self.assertEqual(serializer.data['date'], '2024-05-10T19:00:00Z')
        self.assertEqual(serializer.data['address'], '123 Main St')
        self.assertEqual(serializer.data['guest_count'], 10)

    def test_event_serializer_invalid_data(self):
        data = {'date': 'invalid', 'address': '123 Main St', 'guest_count': 'abc'}
        serializer = EventSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue('date' in serializer.errors)
        self.assertTrue('guest_count' in serializer.errors)

class ServiceSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        self.provider = ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=5, phone='123-456-7890')
        self.event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)

    def test_service_serializer(self):
        service = Service.objects.create(event=self.event, category='chef', provider=self.provider, rate=Decimal('100.00'))
        serializer = ServiceSerializer(service)
        self.assertEqual(serializer.data['category'], 'chef')
        self.assertEqual(serializer.data['rate'], '100.00')

    def test_service_serializer_invalid_data(self):
        data = {'category': 'invalid', 'rate': 'abc'}
        serializer = ServiceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue('category' in serializer.errors)
        self.assertTrue('rate' in serializer.errors)

class ServiceMatchSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        self.provider = ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=5, phone='123-456-7890')
        self.event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        self.service = Service.objects.create(event=self.event, category='chef', provider=self.provider, rate=Decimal('100.00'))

    def test_servicematch_serializer(self):
        match = ServiceMatch.objects.create(service=self.service, provider=self.provider, proposed_rate=Decimal('100.00'))
        serializer = ServiceMatchSerializer(match)
        self.assertEqual(serializer.data['proposed_rate'], '100.00')

    def test_servicematch_serializer_invalid_data(self):
        data = {'proposed_rate': 'abc'}
        serializer = ServiceMatchSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue('proposed_rate' in serializer.errors)

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

class EventViewSetIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')

    def test_create_event(self):
        url = reverse('event-list')
        data = {
            'date': '2024-05-10T19:00:00Z',
            'address': '123 Main St',
            'guest_count': 10,
            'additional_details': 'Some details'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)

class ServiceViewSetIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        self.provider = ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=5, phone='123-456-7890')
        self.event = Event.objects.create(client=self.user, date=datetime(2024, 5, 10, 19, 0), address='123 Main St', guest_count=10)
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')

    def test_create_service(self):
        url = reverse('service-list')
        data = {
            'event': self.event.id,
            'category': 'chef',
            'provider': self.provider.id,
            'rate': '100.00'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Service.objects.count(), 1)
