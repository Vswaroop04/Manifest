from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.utils.serializer_helpers import ReturnList


class StandardPaginator(PageNumberPagination):
    page_size = 50
    page_size_query_param = "size"

    def get_paginated_response(self, data: ReturnList) -> Response:
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    (
                        "next",
                        self.page.next_page_number() if self.page.has_next() else None,
                    ),
                    (
                        "previous",
                        self.page.previous_page_number()
                        if self.page.has_previous()
                        else None,
                    ),
                    ("results", data),
                ]
            )
        )

    def get_paginated_response_schema(self, schema: dict) -> dict:  # type: ignore[override]
        return {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "example": 123},
                "next": {"type": "integer", "nullable": True, "example": 4},
                "previous": {"type": "integer", "nullable": True, "example": 3},
                "results": schema,
            },
        }

    def paginate_queryset(self, queryset, request: Request, view=None):  # type: ignore[override]
        return super().paginate_queryset(queryset, request, view)
