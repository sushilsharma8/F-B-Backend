from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.EventViewSet, basename='event')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'matches', views.ServiceMatchViewSet, basename='match')

urlpatterns = [
    path('', include(router.urls)),
]
