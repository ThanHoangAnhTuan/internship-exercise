from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    
    response = exception_handler(exc, context)
    
    if isinstance(exc, ValidationException):
        print(exc.errors)
        response = Response({
            'status': 'error',
            'status_code': exc.status_code,
            'message': exc.detail,
            'errors': exc.errors
        }, status=exc.status_code)
        response.data.pop('detail', None)
        return response
    
    if response is not None:
        response = Response({
            'status': 'error',
            'status_code': response.status_code,
            'message': response.data.get('detail', 'An error occurred'),
            'errors': {'details': response.data.get('detail')}
        }, status=response.status_code)
        response.data.pop('detail', None)
        return response
    
    response = Response({
        'status': 'error',
        'status_code': response.status_code,
        'message': 'Internal server error',
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    response.data.pop('detail', None)
    return response

class ValidationException(APIException):
    status_code = 400
    default_detail = 'Bad Request'
    default_code = 'bad_request'
    
    def __init__(self, message=None, code=None, errors=None):
        if message is None:
            message = self.default_message
        if code is None:
            code = self.default_code
        self.detail = message
        self.code = code
        self.errors = errors
        
    