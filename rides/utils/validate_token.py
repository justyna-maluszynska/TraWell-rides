import os
from functools import wraps

import jwt
from django.http import JsonResponse
from rest_framework import status

from users.models import User


def validate_token(func):
    @wraps(func)
    def inner(self, request, *args, **kwargs):
        try:
            token = request.headers['Authorization'].split(' ')[1]
        except (KeyError, IndexError):
            return JsonResponse(data='Invalid token provided', status=status.HTTP_401_UNAUTHORIZED, safe=False)

        try:
            public_key = f"""-----BEGIN PUBLIC KEY-----\n{os.environ.get("TOKEN_KEY")}\n-----END PUBLIC KEY-----"""
            decoded_token = jwt.decode(token, public_key, algorithms=["RS256"], audience="account")
        except jwt.exceptions.DecodeError:
            return JsonResponse(data='Token decoding failure', status=status.HTTP_401_UNAUTHORIZED, safe=False)

        user_email = decoded_token['email']
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_404_NOT_FOUND, data="User not found", safe=False)

        return func(self, request, user=user, *args, **kwargs)

    return inner
