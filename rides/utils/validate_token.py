import os
from functools import wraps

import jwt
from django.http import JsonResponse
from rest_framework import status


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

        return func(self, request, decoded_token=decoded_token, *args, **kwargs)

    return inner
