import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from api.routings  import websocket_urlpatterns
from channels.auth import AuthMiddlewareStack
from api.middlewares import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        ) 
    ),
})
