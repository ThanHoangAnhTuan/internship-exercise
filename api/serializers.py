from rest_framework import serializers
from .models import User, UserInfo, UserHealthInfo, UserHealthIndicator, BloodGlucoseIndicator, BloodPressureIndicator
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from .exceptions import ValidationException
import re

class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=255, required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.CharField(required=True)
    height = serializers.FloatField(required=True)
    weight = serializers.FloatField(required=True)
    
    class Meta:
        model = User
        fields = ['phone_number', 'pin', 'full_name', 'date_of_birth', 'gender', 'height', 'weight']
        extra_kwargs = {
            'pin': {'write_only': True}
        }
    
    def validate_date_of_birth(self, data):
        if data > datetime.now().date():
            raise ValidationException(
                errors= {
                    "date_of_birth": [
                        "Date of birth cannot be in the future."
                    ]
                }
            )
        return data
    
    def validate_gender(self, data):
        if data not in ["Male", "Female"]:
            raise ValidationException(
                    errors= {
                        "gender": [
                            "Gender must be Male or Female."
                        ]
                    }
                )
        return data
    
    def validate_height(self, data):
        if data > 300 or data < 1:
            raise ValidationException(
                errors= {
                    "height": [
                        "Height must be greater than 1cm and less than 300cm."
                    ]
                }
            )
        return data

    def validate_weight(self, data):
        if data > 1000 or data < 1:
            raise ValidationException(
                errors= {
                    "weight": [
                        "weight must be greater than 1kg and less than 1000kg."
                    ]
                }
            )
        return data
    
    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            pin=validated_data['pin']
        )
        UserInfo.objects.create(
            user= user,
            full_name= validated_data['full_name'],
            date_of_birth= validated_data['date_of_birth'],
            gender= validated_data['gender'],
        )
        UserHealthInfo.objects.create(
            user=user,
            height=validated_data['height'],
            weight=validated_data['weight']
        )
        return user
    
class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    pin = serializers.CharField(write_only=True)
    
    def validate_phone_number(self, data):
        if not re.fullmatch(r"0\d{9}", data):
            raise ValidationException(
                errors= {
                    "phone_number": [
                        "Phone number must start with 0 and be exactly 10 digits."
                    ]
                }
            )
        return data 
    
    def validate_pin(self, data):
        if not re.fullmatch(r"\d{6}", data):
            raise ValidationException(
                errors= {
                    "pin": [
                        "Pin must be exactly 6 digits."
                    ]
                }
            )
        return data 

    def validate(self, data):
        phone_number = data.get('phone_number')
        pin = data.get('pin')
        
        try:
            user = User.objects.get(phone_number=phone_number)
            if not user.check_pin(pin):
                raise ValidationException(
                    message="Login serializer error",
                    errors= {"details": "Invalid phone number or PIN"}
                )
        except User.DoesNotExist:
            raise ValidationException(
                message="Login serializer error",
                errors= {"details": "Invalid phone number or PIN"}
            )
        return user
    
    
class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ['full_name', 'date_of_birth', 'gender']
    
    def create(self, validated_data):
        user = self.context['request'].user
        if UserInfo.objects.filter(user=user).exists():
            raise ValidationException(
                message="User info serializer error",
                errors= {"details": "User info already exists"}
            )
        return UserInfo.objects.create(user=user, **validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('user', None)
        return representation

class UserHealthInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHealthInfo
        fields = ['height', 'weight', 'blood_glucose', 'blood_pressure']
    
    def create(self, validated_data):
        user = self.context['request'].user
        if UserHealthInfo.objects.filter(user=user).exists():
            raise ValidationException(
                message="User health info serializer error",
                errors= {"details": "User health info already exists"}
            )
        return UserHealthInfo.objects.create(user=user, **validated_data)
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('user', None)
        if representation['blood_glucose'] is None:
            representation.pop('blood_glucose', None)
        if representation['blood_pressure'] is None:
            representation.pop('blood_pressure', None)
        return representation


class BloodGlucoseIndicatorSerializer(serializers.Serializer):
    blood_glucose_indicator = serializers.FloatField()
    unit = serializers.ChoiceField(choices=["mg/dL", "mmol/L"])
    meal = serializers.ChoiceField(choices=["pre-meal", "post-meal", "fasting", "before bed"])
    timestamp = serializers.DateTimeField(default=datetime.now, format="%Y-%m-%d %H:%M:%S")
    
    def validate_blood_glucose_indicator(self, value):
        if value <= 0:
            raise ValidationException("Blood glucose indicator must be greater than 0")
        return value
    
class BloodPressureIndicatorSerializer(serializers.Serializer):
    systolic_indicator = serializers.IntegerField()
    diastolic_indicator = serializers.IntegerField()
    unit = serializers.ChoiceField(choices=["mm Hg"])
    timestamp = serializers.DateTimeField(default=datetime.now, format="%Y-%m-%d %H:%M:%S")
    
    def validate_systolic_indicator(self, data):
        if data <= 0:
            raise ValidationException(
                errors= {
                    "systolic_indicator": [
                        "Systolic indicator must be greater than 0 mm Hg"
                    ]
                }
            )
        return data
    
    def validate_diastolic_indicator(self, data):
        if data <= 0:
            raise ValidationException(
                errors= {
                    "diastolic_indicator": [
                        "Diastolic indicator must be greater than 0 mm Hg"
                    ]
                }
            )
        return data
    
class UserHealthIndicatorSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    blood_glucose_list = BloodGlucoseIndicatorSerializer(many=True)
    blood_pressure_list = BloodPressureIndicatorSerializer(many=True)
    
    def create(self, validated_data):
        user_id = validated_data['user_id']
        blood_glucose_list = validated_data['blood_glucose_list']
        blood_pressure_list = validated_data['blood_pressure_list']
        
        user_health_indicator = UserHealthIndicator.objects.create(
            user_id=user_id,
            blood_glucose_list=blood_glucose_list,
            blood_pressure_list=blood_pressure_list
        )
        return user_health_indicator 
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('user_id', None)
        return representation