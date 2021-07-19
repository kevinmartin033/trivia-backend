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

    "websocket": URLRouter([
        url('game/', GameConsumer.as_asgi())
    ])
})


# def main():
#     """Run administrative tasks."""
#     # try:
#     #     from django.core.management import execute_from_command_line
#     # except ImportError as exc:
#     #     raise ImportError(
#     #         "Couldn't import Django. Are you sure it's installed and "
#     #         "available on your PYTHONPATH environment variable? Did you "
#     #         "forget to activate a virtual environment?"
#     #     ) from exc
#     # execute_from_command_line(sys.argv)


# if __name__ == '__main__':
#     main()



