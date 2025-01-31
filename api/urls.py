from django.urls import path
from .views import RegisterView, LoginView, UserInfoView, UserHealthInfoView, RefreshTokenView, LogoutView, CreateUserInfoView, \
    UpdateUserInfo, DeleteUserInfo, CreateUserHealthInfo, UpdateUserHealthInfo, DeleteUserHealthInfo, BloodGlucoseIndicatorView, \
    BloodPressureIndicatorView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    
    path('user-info/', UserInfoView.as_view(), name='get-user-info'),
    path('create-user-info/', CreateUserInfoView.as_view(), name='create-user-info'),
    path('update-user-info/', UpdateUserInfo.as_view(), name='update-user-info'),
    path('delete-user-info/', DeleteUserInfo.as_view(), name='delete-user-info'),
    
    path('user-health-info/', UserHealthInfoView.as_view(), name='get-user-health-info'),
    path('create-user-health-info/', CreateUserHealthInfo.as_view(), name='create-user-health-info'),
    path('update-user-health-info/', UpdateUserHealthInfo.as_view(), name='update-user-health-info'),
    path('delete-user-health-info/', DeleteUserHealthInfo.as_view(), name='delete-user-health-info'),
    
    path('blood-glucose-indicator/', BloodGlucoseIndicatorView.as_view(), name='blood-glucose-indicator'),
    path('blood-pressure-indicator/', BloodPressureIndicatorView.as_view(), name='blood-pressure-indicator'),
]
