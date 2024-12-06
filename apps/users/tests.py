import unittest
from django.test import TestCase
from django.contrib.auth.hashers import check_password
from .models import User
from .serializers import UserSerializer
from rest_framework.test import APIRequestFactory
from rest_framework import status

class UserModelTests(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        self.assertTrue(check_password('testpassword', user.password))
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertEqual(user.role, 'client')

    def test_user_creation_invalid_role(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='invalid')
        self.assertTrue('invalid role' in str(context.exception))

    def test_user_creation_duplicate_email(self):
        User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        with self.assertRaises(Exception) as context:
            User.objects.create_user(username='testuser2', password='testpassword2', email='test@example.com', name='Test User 2', role='provider')
        self.assertTrue('unique constraint' in str(context.exception))

    def test_user_str(self):
        user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        self.assertEqual(str(user), 'test@example.com')

class UserSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_user_serializer(self):
        user = User.objects.create_user(username='testuser', password='testpassword', email='test@example.com', name='Test User', role='client')
        serializer = UserSerializer(user)
        self.assertEqual(serializer.data['email'], 'test@example.com')
        self.assertEqual(serializer.data['name'], 'Test User')
        self.assertEqual(serializer.data['role'], 'client')

    def test_user_serializer_invalid_data(self):
        data = {'email': 'invalid', 'name': 'Test User', 'role': 'client'}
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue('email' in serializer.errors)

    def test_user_serializer_create(self):
        data = {'email': 'newuser@example.com', 'username': 'newuser', 'name': 'New User', 'password': 'newpassword', 'role': 'provider'}
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.name, 'New User')
        self.assertEqual(user.role, 'provider')
        self.assertTrue(check_password('newpassword', user.password))
