from rest_framework.pagination import PageNumberPagination

class StudentPagination(PageNumberPagination):
    page_size = 25  # how many students per page
    page_size_query_param = "page_size"  # optional: allow ?page_size=50
    max_page_size = 100