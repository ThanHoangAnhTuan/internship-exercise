from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView, ListCreateAPIView
from drf_spectacular.utils import extend_schema
from pymemcache.client.base import Client
import json

from .serializers import RegisterSerializer, LoginSerializer, UserInfoSerializer, UserHealthInfoSerializer, \
    BloodGlucoseIndicatorSerializer, BloodPressureIndicatorSerializer
from .models import UserHealthIndicator, User
from .pagination import Pagination
from .utils import save_blood_indicator

client = Client('localhost')

# auth
class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserInfoSerializer},
        description="Endpoint to register a new user"
    )
    def perform_create(self, serializer):
        user = serializer.save()
        self.user_info_serializer = UserInfoSerializer(user.user_info)
        self.user_health_info_serializer = UserHealthInfoSerializer(user.user_health_info)
        
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer=serializer)
        return Response({
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": "User created successfully.",
            "data": {
                "user_info": self.user_info_serializer.data,
                "user_health_info": self.user_health_info_serializer.data
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    @extend_schema(
        request=LoginSerializer,
        responses={200: None},
        description="Endpoint to authenticate a user and return tokens"
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        
        old_refresh_token = request.COOKIES.get('refresh_token')
        if old_refresh_token:
            try:
                old_refresh = RefreshToken(old_refresh_token)
                old_refresh.blacklist()
            except Exception as e:
                pass
        
        user_info_serializer = {}
        if hasattr(user, 'user_info') and user.user_info:
            user_info_serializer = UserInfoSerializer(user.user_info).data
        
        user_health_info_serializer = {}
        if hasattr(user, 'user_health_info') and user.user_health_info:
            user_health_info_serializer = UserHealthInfoSerializer(user.user_health_info).data
        
        refresh = RefreshToken.for_user(user)
        response = Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Login successful",
                "data": {
                    "user_info": user_info_serializer,
                    "user_health_info": user_health_info_serializer,
                },
                "access_token": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            # secure=True,
            samesite='Lax'
        )
        return response

class RefreshTokenView(GenericAPIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=None,
        responses={200: None},
        description="Endpoint to refresh the access token"
    )
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "access_token": str(refresh.access_token)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid refresh token", 
                "errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(GenericAPIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=None,
        responses={200: None},
        description="Endpoint to log out a user"
    )
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        response = Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Logout successful"
        }, status=status.HTTP_200_OK)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                response.data = {
                    "status": "error",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid or expired refresh token"
                }
                response.status_code = status.HTTP_400_BAD_REQUEST
        response.delete_cookie('refresh_token')
        return response

# User info
class UserInfoView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserInfoSerializer
    
    @extend_schema(
        responses={200: UserInfoSerializer, 404: None},
        description="Endpoint to retrieve user info",
    )
    def retrieve(self, request, *args, **kwargs):
        user_info = getattr(request.user, 'user_info', None)
        if not user_info:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "User info not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        user_info_data = client.get(f"user_info_${request.user.id}")
        if user_info_data:
            user_info_data = json.loads(user_info_data.decode('utf-8'))
        if not user_info_data:
            user_info_serializer = self.get_serializer(user_info)
            user_info_data = user_info_serializer.data
            client.set(f"user_info_${request.user.id}", json.dumps(user_info_data).encode('utf-8'))
            
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "User info retrieved successfully",
            "data": {
                "user_info": user_info_data
            }}, status=status.HTTP_200_OK)

class CreateUserInfoView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserInfoSerializer
    
    @extend_schema(
        request=UserInfoSerializer,
        responses={201: UserInfoSerializer},
        description="Endpoint to create user info"
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        client.set(f"user_info_${request.user.id}", json.dumps(serializer.data).encode('utf-8'))

        
        return Response({
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": "User info created successfully",
            "data": {
                "user_info": serializer.data
            }}, status=status.HTTP_201_CREATED)
            
class UpdateUserInfo(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserInfoSerializer
    
    @extend_schema(
        request=UserInfoSerializer,
        responses={200: UserInfoSerializer, 404: None},
        description="Endpoint to update user info"
    )
    def update(self, request, *args, **kwargs):
        user_info = getattr(request.user, 'user_info', None)
        if not user_info:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "User info not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(user_info, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        client.set(f"user_info_${request.user.id}", json.dumps(serializer.data).encode('utf-8'))

        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "User info updated successfully",
            "data": {
                "user_info": serializer.data
            }
        }, status=status.HTTP_200_OK)
        
class DeleteUserInfo(DestroyAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: None, 404: None},
        description="Endpoint to delete user info"
    )
    def destroy(self, request, *args, **kwargs):
        user_info = getattr(request.user, 'user_info', None)
        if not user_info:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,   
                "message": "User info not found"
            }, status=status.HTTP_404_NOT_FOUND)
        user_info.delete()
        client.delete(f"user_info_${request.user.id}")
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "User info deleted successfully"
        }, status=status.HTTP_200_OK)
        

# User health info
class UserHealthInfoView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserHealthInfoSerializer
    
    @extend_schema(
        responses={200: UserHealthInfoSerializer},
        description="Retrieve user health information"
    )
    def retrieve(self, request, *args, **kwargs):
        user_health_info = getattr(request.user, 'user_health_info', None)
        if not user_health_info:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "User health info not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        user_health_info_data = client.get(f"user_health_info_${request.user.id}")
        if user_health_info_data:
            user_health_info_data = json.loads(user_health_info_data.decode('utf-8'))
        else:
            user_health_info_serializer = self.get_serializer(user_health_info)
            user_health_info_data = user_health_info_serializer.data
            client.set(f"user_health_info_${request.user.id}", json.dumps(user_health_info_data).encode('utf-8'))
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "User health info retrieved successfully",
            "data": {
                "user_health_info": user_health_info_data
            }
        }, status=status.HTTP_200_OK)

class CreateUserHealthInfo(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserHealthInfoSerializer
    
    @extend_schema(
        request=UserHealthInfoSerializer,
        responses={201: UserHealthInfoSerializer},
        description="Create user health information"
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        client.set(f"user_health_info_${request.user.id}", json.dumps(serializer.data).encode('utf-8'))
        return Response({
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": "User health info created successfully",
            "data": {
                "user_health_info": serializer.data
            }}, status=status.HTTP_201_CREATED)

class UpdateUserHealthInfo(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserHealthInfoSerializer
    
    @extend_schema(
        request=UserHealthInfoSerializer,
        responses={200: UserHealthInfoSerializer},
        description="Update user health information"
    )
    def update(self, request, *args, **kwargs):
        user_health_info = getattr(request.user, 'user_health_info', None)
        if not user_health_info:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "User health info not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(user_health_info, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        client.set(f"user_health_info_${request.user.id}", json.dumps(serializer.data))
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "User health info updated successfully",
            "data": {
                "user_health_info": serializer.data
            }
        }, status=status.HTTP_200_OK)

class DeleteUserHealthInfo(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: None},
        description="Delete user health information"
    )
    def destroy(self, request, *args, **kwargs):
        user_health_info = getattr(request.user, 'user_health_info', None)
        if not user_health_info:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "User health info not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        user_health_info.delete()
        client.delete(f"user_health_info_${request.user.id}")
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "User health info deleted successfully"
        }, status=status.HTTP_200_OK)

# User Blood Glucose Indicator
class BloodGlucoseIndicatorView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BloodGlucoseIndicatorSerializer
    pagination_class = Pagination
    
    @extend_schema(
        request=BloodGlucoseIndicatorSerializer,
        responses={201: BloodGlucoseIndicatorSerializer},
        description="Create a blood glucose indicator"
    )
    def post(self, request):
        user_id = request.user.id
        result = save_blood_indicator(user_id, request.data)
        return Response(result, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        user_id = self.request.user.id
        try:
            user_health_indicator = UserHealthIndicator.objects.get(user_id=user_id)
            return user_health_indicator.blood_glucose_list
        except UserHealthIndicator.DoesNotExist:
            return []
    
    @extend_schema(
        responses={200: BloodGlucoseIndicatorSerializer(many=True)},
        description="Retrieve all blood glucose indicators"
    )
    def get(self, request):
        queryset = list(self.get_queryset())
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, "glucose")
        
        if page is not None:
            return paginator.get_paginated_response(page, "Retrieve blood glucose indicator list", "blood_glucose_list")
        
        serializer = BloodGlucoseIndicatorSerializer(queryset, many=True)
        
        return Response({
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Blood glucose indicator retrieved successfully",
            "data": {
                "blood_glucose_list": serializer.data
            }
        }, status=status.HTTP_200_OK)

class BloodPressureIndicatorView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BloodPressureIndicatorSerializer
    pagination_class = Pagination
    
    @extend_schema(
        request=BloodPressureIndicatorSerializer,
        responses={201: BloodPressureIndicatorSerializer},
        description="Create a blood pressure indicator"
    )
    def post(self, request):
        user_id = request.user.id
        result = save_blood_indicator(user_id, request.data)
        return Response(result, status=status.HTTP_201_CREATED)
        
    def get_queryset(self):
        user_id = self.request.user.id
        try:
            user_health_indicator = UserHealthIndicator.objects.get(user_id=user_id)
            return user_health_indicator.blood_pressure_list
        except UserHealthIndicator.DoesNotExist:
            return []
    
    @extend_schema(
        responses={200: BloodPressureIndicatorSerializer(many=True)},
        description="Retrieve all blood pressure indicators"
    )
    def get(self, request):
        try:
            queryset = list(self.get_queryset())
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request, "pressure")
            
            if page is not None:
                return paginator.get_paginated_response(page, "Retrieve blood pressure indicator list", "blood_pressure_list")
            
            serializer = BloodPressureIndicatorSerializer(queryset, many=True)
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Blood pressure indicator retrieved successfully",
                "data": {
                    "blood_pressure_list": serializer.data
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
