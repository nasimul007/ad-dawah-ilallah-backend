import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 20                # default items per page
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        page_size = self.get_page_size(self.request)
        total_pages = math.ceil(total / page_size)

        return Response({
            "data": data,
            "meta": {
                "total": total,
                "page": self.page.number,
                "page_size": page_size,
                "total_pages": total_pages,
            },
            "links": {
                "next": self.get_next_link(),
                "prev": self.get_previous_link(),
            }
        })
