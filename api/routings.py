from .consumers import RequestConsumer
from django.urls import path

websocket_urlpatterns = [
    path('ws/blood-indicator/', RequestConsumer.as_asgi()),
]