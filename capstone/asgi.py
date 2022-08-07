"""
ASGI config for capstone project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
import django
from channels.routing import ProtocolTypeRouter,URLRouter
from django.core.asgi import get_asgi_application
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')


import group.routing
import group.urls
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'websocket':AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                group.routing.websocket_urlpatterns
            )
        )
    )
})
