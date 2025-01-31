from .serializers import BloodGlucoseIndicatorSerializer, BloodPressureIndicatorSerializer
from .models import UserHealthIndicator, BloodGlucoseIndicator, BloodPressureIndicator
from rest_framework import status

def save_blood_indicator(user_id, data):
    try:
        user_health_indicator = UserHealthIndicator.objects.get(user_id=user_id)
    except UserHealthIndicator.DoesNotExist:
        user_health_indicator = UserHealthIndicator(user_id=user_id, blood_glucose_list=[], blood_pressure_list=[])
        user_health_indicator.save()
        
    if data["type"] == "glucose":
        serializer = BloodGlucoseIndicatorSerializer(data=data)
        if not serializer.is_valid():
            return {
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Error occurred",
                "errors": serializer.errors
            }
        blood_glucose = BloodGlucoseIndicator(**serializer.validated_data)
        user_health_indicator.blood_glucose_list.insert(0, blood_glucose)
    elif data["type"] == "pressure":
        serializer = BloodPressureIndicatorSerializer(data=data)
        if not serializer.is_valid():
            return {
                "status": "error",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Error occurred",
                "errors": serializer.errors
            }
        blood_pressure = BloodPressureIndicator(**serializer.validated_data)
        user_health_indicator.blood_pressure_list.insert(0, blood_pressure)
    else:
        return {
            "status": "error",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid type",
            "errors": {
                "type": "Valid types are 'glucose' and 'pressure'"
            }
        }
    user_health_indicator.save()
    return {
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": f"Blood {data["type"]} indicator created successfully",
            "data": {
                f"blood_{data["type"]}_indicator": serializer.data
            }
        }