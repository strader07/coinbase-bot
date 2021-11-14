from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from app import consumer

ws_pattern= [
    path('ws/account/',consumer.Accounts.as_asgi()),
]

application= ProtocolTypeRouter(
    {
        'websocket':AuthMiddlewareStack(URLRouter(ws_pattern))
    }
)