from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import ServiceProviderProfile, Availability
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from apps.events.models import Event, ServiceMatch
from decimal import Decimal
from datetime import time
from .serializers import ServiceProviderProfileSerializer, AvailabilitySerializer
from rest_framework.test import APIRequestFactory
from unittest import expectedFailure

class ProviderViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@example.com', username='testuser', password='testpassword', name='Test User', role='provider')
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')
        self.provider_profile = ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=5, phone='123-456-7890')


    def test_apply(self):
        url = reverse('provider-apply')
        data = {
            'user_id': self.user.id,
            'service_type': 'chef',
            'experience': 5,
            'phone': '123-456-7890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ServiceProviderProfile.objects.filter(user=self.user).exists())

    def test_apply_invalid_data(self):
        url = reverse('provider-apply')
        data = {
            'user_id': self.user.id,
            'service_type': 'invalid',
            'experience': 'abc',
            'phone': '123-456-7890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_nonexistent_user(self):
        url = reverse('provider-apply')
        data = {
            'user_id': 9999,
            'service_type': 'chef',
            'experience': 5,
            'phone': '123-456-7890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_apply_duplicate_profile(self):
        ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=3, phone='987-654-3210')
        url = reverse('provider-apply')
        data = {
            'user_id': self.user.id,
            'service_type': 'chef',
            'experience': 5,
            'phone': '123-456-7890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ServiceProviderProfile.objects.filter(user=self.user).count(),1)
        profile = ServiceProviderProfile.objects.get(user=self.user)
        self.assertEqual(profile.experience, 5)
        self.assertEqual(profile.phone, '123-456-7890')

    def test_dashboard(self):
        url = reverse('provider-dashboard')
        Event.objects.create(provider=self.provider_profile, rate=Decimal('100.00'), status='completed')
        Event.objects.create(provider=self.provider_profile, rate=Decimal('150.00'), status='completed')
        Event.objects.create(provider=self.provider_profile, rate=Decimal('200.00'), status='confirmed')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_bookings'], 3)
        self.assertEqual(response.data['completed_events'], 2)
        self.assertEqual(response.data['upcoming_events'], 1)
        self.assertEqual(response.data['total_earnings'], 350.00)

    def test_dashboard_no_events(self):
        url = reverse('provider-dashboard')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_bookings'], 0)
        self.assertEqual(response.data['completed_events'], 0)
        self.assertEqual(response.data['upcoming_events'], 0)
        self.assertEqual(response.data['total_earnings'], 0)

    def test_availability_update(self):
        url = reverse('provider-availability')
        data = [
            {'day_of_week': 'monday', 'start_time': time(9, 0), 'end_time': time(17, 0)},
            {'day_of_week': 'tuesday', 'start_time': time(10, 0), 'end_time': time(18, 0)},
        ]
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Availability.objects.filter(provider=self.provider_profile).count(), 2)

    def test_availability_update_empty(self):
        url = reverse('provider-availability')
        data = []
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Availability.objects.filter(provider=self.provider_profile).count(), 0)

    def test_availability_update_invalid_data(self):
        url = reverse('provider-availability')
        data = [
            {'day_of_week': 'invalid', 'start_time': time(9, 0), 'end_time': time(17, 0)},
        ]
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_availability_start_time_greater_than_end_time(self):
        url = reverse('provider-availability')
        data = [
            {'day_of_week': 'monday', 'start_time': time(17, 0), 'end_time': time(9, 0)},
        ]
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_availability_invalid_start_time(self):
        url = reverse('provider-availability')
        data = [
            {'day_of_week': 'monday', 'start_time': 'invalid', 'end_time': time(17, 0)},
        ]
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_availability_invalid_end_time(self):
        url = reverse('provider-availability')
        data = [
            {'day_of_week': 'monday', 'start_time': time(9, 0), 'end_time': 'invalid'},
        ]
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upcoming_events(self):
        url = reverse('provider-upcoming_events')
        event = Event.objects.create(provider=self.provider_profile, rate=Decimal('100.00'), status='confirmed')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], event.id)

    def test_upcoming_events_no_events(self):
        url = reverse('provider-upcoming_events')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_event_requests(self):
        url = reverse('provider-event_requests')
        event = Event.objects.create(rate=Decimal('100.00'))
        ServiceMatch.objects.create(provider=self.provider_profile, event=event, status='pending')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_event_requests_no_requests(self):
        url = reverse('provider-event_requests')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_availability_valid_data(self):
        availability = Availability.objects.create(provider=self.provider_profile, day_of_week='monday', start_time=time(9,0), end_time=time(17,0))
        self.assertTrue(availability.is_valid())

    def test_availability_invalid_day(self):
        with self.assertRaises(ValidationError):
            Availability.objects.create(provider=self.provider_profile, day_of_week='invalid', start_time=time(9,0), end_time=time(17,0))

    def test_availability_start_after_end(self):
        with self.assertRaises(ValidationError):
            Availability.objects.create(provider=self.provider_profile, day_of_week='monday', start_time=time(17,0), end_time=time(9,0))

    def test_availability_invalid_start_time(self):
        with self.assertRaises(ValidationError):
            Availability.objects.create(provider=self.provider_profile, day_of_week='monday', start_time='invalid', end_time=time(17,0))

    def test_availability_invalid_end_time(self):
        with self.assertRaises(ValidationError):
            Availability.objects.create(provider=self.provider_profile, day_of_week='monday', start_time=time(9,0), end_time='invalid')

class AvailabilityModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='provider')
        self.profile = ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=5, phone='123-456-7890')

    def test_availability_creation(self):
        availability = Availability.objects.create(provider=self.profile, day_of_week='monday', start_time=time(9, 0), end_time=time(17, 0))
        self.assertEqual(availability.day_of_week, 'monday')
        self.assertEqual(availability.start_time, time(9, 0))
        self.assertEqual(availability.end_time, time(17, 0))

    def test_availability_invalid_day(self):
        with self.assertRaises(ValidationError):
            Availability.objects.create(provider=self.profile, day_of_week='invalid', start_time=time(9, 0), end_time=time(17, 0))

    def test_availability_start_after_end(self):
        with self.assertRaises(ValidationError):
            Availability.objects.create(provider=self.profile, day_of_week='monday', start_time=time(17, 0), end_time=time(9, 0))


class AvailabilitySerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='provider')
        self.profile = ServiceProviderProfile.objects.create(user=self.user, service_type='chef', experience=5, phone='123-456-7890')
        self.availability = Availability.objects.create(provider=self.profile, day_of_week='monday', start_time=time(9, 0), end_time=time(17, 0))

    def test_availabilityserializer(self):
        serializer = AvailabilitySerializer(self.availability)
        self.assertEqual(serializer.data['day_of_week'], 'monday')
        self.assertEqual(serializer.data['start_time'], '09:00:00')
        self.assertEqual(serializer.data['end_time'], '17:00:00')

    def test_availabilityserializer_invalid_data(self):
        data = {'day_of_week': 'invalid', 'start_time': 'invalid', 'end_time': 'invalid'}
        serializer = AvailabilitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue('day_of_week' in serializer.errors)
        self.assertTrue('start_time' in serializer.errors)
        self.assertTrue('end_time' in serializer.errors)

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

class ProviderViewSetIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='provider')
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')

    def test_apply_integration(self):
        url = reverse('provider-apply')
        data = {
            'user_id': self.user.id,
            'service_type': 'chef',
            'experience': 5,
            'phone': '123-456-7890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceProviderProfile.objects.filter(user=self.user).count(), 1)

    def test_dashboard_integration(self):
        url = reverse('provider-dashboard')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Add assertions based on expected dashboard data

    def test_availability_integration(self):
        url = reverse('provider-availability')
        data = [{'day_of_week': 'monday', 'start_time': '09:00:00', 'end_time': '17:00:00'}]
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Availability.objects.filter(provider__user=self.user).count(), 1)
