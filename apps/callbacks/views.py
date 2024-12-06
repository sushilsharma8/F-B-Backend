from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CallbackRequestSerializer
from .models import CallbackRequest

class CallbackRequestView(APIView):
    def post(self, request, format=None):
        serializer = CallbackRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Callback request received successfully.'}, status=201)
        return Response(serializer.errors, status=400)
