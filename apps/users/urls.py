from django.urls import path
from .views import ProfileView, PasswordChangeView

urlpatterns = [
    path('profile/', ProfileView.as_view()),
    path('password/', PasswordChangeView.as_view()),
]
