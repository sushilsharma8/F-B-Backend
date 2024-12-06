from rest_framework import serializers
from .models import UpiTransaction

class UpiTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpiTransaction
        fields = '__all__'
