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
            public_key = """-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEApxHd1H4JBJx0rbKg9D8+qzHyjhoDK+h4Ht+FIQsaLKEMDqs+Q8izMRrlcpCqXvoNylZd+N0sJHepwR1sxlXsELGZlJr1MZLXBe5YMNVXXbOJzVJQZcEgaDOgL+mmPRNb9OqJG4TecmGi+sdw6o5OHI14X2hsOpLJ1hlyetZOX6cx23/pxAfpgTRfrdPWZGDOlrWTktPr5Dx3+lWXYmwXBdaqM284Lw2VIoGKQvuADshlWtYks+m2L8VrDOYpehFhQ9vbpyfg0+zVdOM+VtmWPAqLFDRBXBfVmmqDkIOZs53STIhlrywvhEuKlWLvhToGWsKimoomYSobUJj40NlALQIDAQAB\n-----END PUBLIC KEY-----"""
            decoded_token = jwt.decode(token, public_key, algorithms=["RS256"], audience="account")
        except jwt.exceptions.DecodeError:
            return JsonResponse(data='Token decoding failure', status=status.HTTP_401_UNAUTHORIZED, safe=False)

        return func(self, request, decoded_token=decoded_token, *args, **kwargs)
    return inner