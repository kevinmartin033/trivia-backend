"""
ASGI config for app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""
"""
WSGI config for app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""
import django
from django.contrib import admin
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url
from django.core.asgi import get_asgi_application
from app.consumers import GameConsumer

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
application = ProtocolTypeRouter({
    # Django's ASGI application to handle traditional HTTP requests
    "http": get_asgi_application(),

    # move to routes
    "websocket": URLRouter([
        url(r"game/(?P<game_id>.+)/", GameConsumer.as_asgi())
    ])
})
