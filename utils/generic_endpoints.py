from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import status


def get_paginated_queryset(self, queryset: QuerySet) -> JsonResponse:
    page = self.paginate_queryset(queryset)

    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = self.get_serializer(page, many=True)
    return JsonResponse(status=status.HTTP_200_OK, data=serializer.data, safe=False)