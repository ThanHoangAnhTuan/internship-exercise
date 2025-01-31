from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from asgiref.sync import sync_to_async
from .models import User

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        token = None
        
        if b"authorization" in headers:
            auth_header = headers[b"authorization"].decode("utf-8")
            if auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]
        
        if token:
            try:
                access_token = AccessToken(token)
                scope["user"] = await sync_to_async(User.objects.get)(id=access_token['user_id'])
            except Exception as e:
                print("error: ", e)
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)