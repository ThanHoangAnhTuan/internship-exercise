from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    
    response = exception_handler(exc, context)
    
    if isinstance(exc, ValidationException):
        response = Response({
            'status': exc.code,
            'status_code': exc.status_code,
            'message': exc.detail,
            'errors': exc.errors
        }, status=exc.status_code)
        return response
    
    if response is not None:
        response = Response({
            'status': 'error',
            'status_code': response.status_code,
            'message': 'An error occurred',
            'errors': response.data
        }, status=response.status_code)
        return response
    
    response = Response({
        'status': 'error',
        'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'message': 'Internal server error',
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response
class ValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Bad Request'
    default_code = 'error'
    
    def __init__(self, message=None, errors=None):
        self.detail = self.default_detail
        self.code = self.default_code
        self.errors = errors
        
    