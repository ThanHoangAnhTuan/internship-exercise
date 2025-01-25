from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer, LoginSerializer, UserInfoSerializer, UserHealthInfoSerializer, \
    BloodGlucoseIndicatorSerializer, BloodPressureIndicatorSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import UserHealthIndicator, BloodGlucoseIndicator, BloodPressureIndicator
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular import openapi

# auth
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserInfoSerializer},
        description="Endpoint to register a new user"
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_info_serializer = UserInfoSerializer(user.user_info)
            user_health_info_serializer = UserHealthInfoSerializer(user.user_health_info)
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "User created successfully.",
                "data": {
                    "user_info": user_info_serializer.data,
                    "user_health_info": user_health_info_serializer.data
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=LoginSerializer,
        responses={200: None},
        description="Endpoint to authenticate a user and return tokens"
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
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
                },"access_token": str(refresh.access_token)}, 
                status=status.HTTP_200_OK)
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                # secure=True,
                samesite='Lax'
            )
            return response
        print("Login view")
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Login failed",
            "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
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

class LogoutView(APIView):
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
class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: UserInfoSerializer},
        description="Endpoint to retrieve user info",
    )
    def get(self, request):
        if hasattr(request.user, 'user_info') and request.user.user_info:
            user_info_serializer = UserInfoSerializer(request.user.user_info)
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "User info retrieved successfully",
                "data": {
                    "user_info": user_info_serializer.data
                }}, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": "User info not found"
            }, status=status.HTTP_404_NOT_FOUND)

class CreateUserInfoView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=UserInfoSerializer,
        responses={201: UserInfoSerializer},
        description="Endpoint to create user info"
    )
    def post(self, request):
        serializer = UserInfoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "User info created successfully",
                "data": {
                    "user_info": serializer.data
                }}, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "User info not created",
            "errors": {
                serializer.errors
            }}, status=status.HTTP_400_BAD_REQUEST)
            
class UpdateUserInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=UserInfoSerializer,
        responses={200: UserInfoSerializer},
        description="Endpoint to update user info"
    )
    def put(self, request):
        if hasattr(request.user, 'user_info') and request.user.user_info:
            user_info = request.user.user_info
            serializer = UserInfoSerializer(user_info, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "status_code": status.HTTP_200_OK,
                    "message": "User info updated successfully",
                    "data": {
                        "user_info": serializer.data
                    }}, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "User info not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "User info not updated",
                "errors": {
                    serializer.errors
                }}, status=status.HTTP_400_BAD_REQUEST)

class DeleteUserInfo(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        responses={200: None},
        description="Endpoint to delete user info"
    )
    def delete(self, request):
        if hasattr(request.user, 'user_info') and request.user.user_info:
            request.user.user_info.delete()
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "User info deleted successfully"}, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": "User info not found"}, status=status.HTTP_404_NOT_FOUND)


# User health info
class UserHealthInfoView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: UserHealthInfoSerializer},
        description="Retrieve user health information"
    )
    def get(self, request):
        if hasattr(request.user, 'user_health_info') and request.user.user_health_info:
            user_health_info_serializer = UserHealthInfoSerializer(request.user.user_health_info)
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "User health info retrieved successfully",
                "data": {
                    "user_info": user_health_info_serializer.data
                }}, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": "User health info not found"}, status=status.HTTP_404_NOT_FOUND)

class CreateUserHealthInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=UserHealthInfoSerializer,
        responses={201: UserHealthInfoSerializer},
        description="Create user health information"
    )
    def post(self, request):
        serializer = UserHealthInfoSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "User health info created successfully",
                "data": {
                    "user_health_info": serializer.data
                }}, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "User health info not created",
            "errors": {
                serializer.errors
            }}, status=status.HTTP_400_BAD_REQUEST)

class UpdateUserHealthInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=UserHealthInfoSerializer,
        responses={200: UserHealthInfoSerializer},
        description="Update user health information"
    )
    def put(self, request):
        if hasattr(request.user, 'user_health_info') and request.user.user_health_info:
            user_health_info = request.user.user_health_info
            serializer = UserHealthInfoSerializer(user_health_info, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "status_code": status.HTTP_200_OK,
                    "message": "User health info updated successfully",
                    "data": {
                        "user_health_info": serializer.data
                    }}, status=status.HTTP_200_OK)
            return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "User health info not updated",
            "errors": {
                serializer.errors
            }}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "User health info not found"}, status=status.HTTP_404_NOT_FOUND)

class DeleteUserHealthInfo(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: None},
        description="Delete user health information"
    )
    def delete(self, request):
        if hasattr(request.user, 'user_health_info') and request.user.user_health_info:
            request.user.user_health_info.delete()
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "User health info deleted successfully"}, status=status.HTTP_200_OK)
        return Response({
            "status": "error",
            "status_code": status.HTTP_404_NOT_FOUND,
            "message": "User health info not found"}, status=status.HTTP_404_NOT_FOUND)


# User Blood Glucose Indicator
class BloodGlucoseIndicatorView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=BloodGlucoseIndicatorSerializer,
        responses={201: BloodGlucoseIndicatorSerializer},
        description="Create a blood glucose indicator"
    )
    def post(self, request):
        user_id = request.user.id
        try:
            user_health_indicator = UserHealthIndicator.objects.get(user_id=user_id)
        except UserHealthIndicator.DoesNotExist:
            user_health_indicator = UserHealthIndicator(user_id=user_id, blood_glucose_list=[], blood_pressure_list=[])
            user_health_indicator.save()
        
        serializer = BloodGlucoseIndicatorSerializer(data=request.data)
        if serializer.is_valid():
            blood_glucose = BloodGlucoseIndicator(**serializer.validated_data)
            user_health_indicator.blood_glucose_list.insert(0, blood_glucose)
            user_health_indicator.save()
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "Blood glucose indicator created successfully",
                "data": {
                    "blood_glucose_indicator": serializer.data
                }}, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Blood glucose indicator not created",
            "errors": {
                serializer.errors
            }}, status=status.HTTP_400_BAD_REQUEST)
    
    
    @extend_schema(
        responses={200: BloodGlucoseIndicatorSerializer(many=True)},
        description="Retrieve all blood glucose indicators"
    )
    def get(self, request):
        user_id = request.user.id
        try:
            user_health_indicator = UserHealthIndicator.objects.get(user_id=user_id)
            blood_glucose_list = user_health_indicator.blood_glucose_list
            serializer = BloodGlucoseIndicatorSerializer(blood_glucose_list, many=True)
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Blood glucose indicator retrieved successfully",
                "data": {
                    "blood_glucose_list": serializer.data
                }}, status=status.HTTP_200_OK)
        except UserHealthIndicator.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Blood glucose indicator not found"}, status=status.HTTP_404_NOT_FOUND)

class BloodPressureIndicatorView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=BloodPressureIndicatorSerializer,
        responses={201: BloodPressureIndicatorSerializer},
        description="Create a blood pressure indicator"
    )
    def post(self, request):
        user_id = request.user.id
        try:
            user_health_indicator = UserHealthIndicator.objects.get(user_id=user_id)
        except UserHealthIndicator.DoesNotExist:
            user_health_indicator = UserHealthIndicator(user_id=user_id, blood_glucose_list=[], blood_pressure_list=[])
            user_health_indicator.save()
        
        serializer = BloodPressureIndicatorSerializer(data=request.data)
        if serializer.is_valid():
            blood_pressure = BloodPressureIndicator(**serializer.validated_data)
            user_health_indicator.blood_pressure_list.insert(0, blood_pressure)
            user_health_indicator.save()
            return Response({
                "status": "success",
                "status_code": status.HTTP_201_CREATED,
                "message": "Blood pressure indicator created successfully",
                "data": {
                    "blood_pressure_indicator": serializer.data
                }}, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Blood pressure indicator not created",
            "errors": {
                serializer.errors
            }}, status=status.HTTP_400_BAD_REQUEST)
    
    
    @extend_schema(
        responses={200: BloodPressureIndicatorSerializer(many=True)},
        description="Retrieve all blood pressure indicators"
    )
    def get(self, request):
        user_id = request.user.id
        try:
            user_health_indicator = UserHealthIndicator.objects.get(user_id=user_id)
            blood_pressure_list = user_health_indicator.blood_pressure_list
            serializer = BloodPressureIndicatorSerializer(blood_pressure_list, many=True)
            return Response({
                "status": "success",
                "status_code": status.HTTP_200_OK,
                "message": "Blood pressure indicator retrieved successfully",
                "data": {
                    "blood_pressure_list": serializer.data
                }}, status=status.HTTP_200_OK)
        except UserHealthIndicator.DoesNotExist:
            return Response({
                "status": "error",
                "status_code": status.HTTP_404_NOT_FOUND,
                "message": "Blood pressure indicator not found"}, status=status.HTTP_404_NOT_FOUND)
