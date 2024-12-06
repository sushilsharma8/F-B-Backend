from rest_framework import serializers
from .models import CallbackRequest

class CallbackRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallbackRequest
        fields = ['name', 'phone_number', 'email', 'best_time', 'message']
