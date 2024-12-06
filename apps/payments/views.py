from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UpiTransactionSerializer
from .models import UpiTransaction

class UpiPaymentView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id') # Get Supabase user ID from request
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Attempt to find the user in the database using the provided user_id.
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpiTransactionSerializer(data={**request.data, 'user': user.id}) # Add user to serializer data
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
