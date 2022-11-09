from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'page_size': self.page_size,
            'count': self.page.paginator.count,
            'results': data,
        })
