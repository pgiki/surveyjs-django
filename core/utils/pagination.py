# for pagination
from django.conf import settings
from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    page_size = 15
    page_size_query_param = "size"
    max_page_size = 10000

    def get_paginated_response(self, data):
        current_page = self.request.GET.get("page", "1")
        if current_page.isdigit():
            current_page = int(current_page)
        else:
            current_page = 1
        total_pages = self.page.paginator.num_pages
        is_paginated = self.page.has_next() or self.page.has_previous()

        return Response(
            {
                "page": current_page,
                "is_paginated": is_paginated,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "count": self.page.paginator.count,
                "total_pages": total_pages,
                "results": data,
            }
        )
