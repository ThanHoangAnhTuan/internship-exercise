from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

class Pagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def paginate_queryset(self, queryset, request, type, view=None):
        data_list = []
        if type == "glucose":
            for item in queryset:
                item_dict = {
                    'blood_glucose_indicator': item.blood_glucose_indicator,
                    'unit': item.unit,
                    'timestamp': item.timestamp,
                    'meal': item.meal
                }
                data_list.append(item_dict)
        elif type == "pressure":
            for item in queryset:
                item_dict = {
                    'systolic_indicator': item.systolic_indicator,
                    'diastolic_indicator': item.diastolic_indicator,
                    'unit': item.unit,
                    'timestamp': item.timestamp,
                }
                data_list.append(item_dict)
        
        self.request = request
        page_size = self.get_page_size(request)
        if not page_size:
            return None
    
        if len(data_list) <= page_size:
            return None

        paginator = self.django_paginator_class(data_list, page_size)
        page_number = self.get_page_number(request, paginator)

        self.page = paginator.page(page_number)
        self.paginator = paginator
        
        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True

        return list(self.page)
    
    def get_paginated_response(self, data, message, detail):
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": message,
            "data": {
                detail: data
            },
            "meta": {
                "pagination": {
                    "total": self.paginator.count,            
                    "count": len(data),       
                    "per_page": self.page_size,          
                    "current_page": self.page.number,       
                    "total_pages": self.paginator.num_pages,       
                    "links": {
                        "next": self.get_next_link(),
                        "previous": self.get_previous_link()
                    }
                }
            }
        }, status=status.HTTP_200_OK)  