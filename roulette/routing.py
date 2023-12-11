from django.urls import path
from roulette import consumers

websocket_urlpatterns = [
    path('roulette/data', consumers.MyConsumer.as_asgi()),
]
