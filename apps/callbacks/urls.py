from django.urls import path
from .views import CallbackRequestView

urlpatterns = [
    path('', CallbackRequestView.as_view()),
]
