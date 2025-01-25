from rest_framework import serializers
from .models import User, UserInfo, UserHealthInfo, UserHealthIndicator, BloodGlucoseIndicator, BloodPressureIndicator
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from .exceptions import ValidationException

# auth serializers
class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=255, required=True, error_messages={
            'required': 'Please enter your full name',
            'max_length': 'Full name must be less than 255 characters'
        })
    date_of_birth = serializers.DateField(required=True, error_messages={'required': 'Please enter your date of birth'})
    gender = serializers.ChoiceField(choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], required=True, 
                                     error_messages={'required': 'Please select gender'})
    height = serializers.FloatField(
        required=True,
        validators=[
            MinValueValidator(1.0, message="Height must greater than 1 cm"),
            MaxValueValidator(300.0, message="Height must less than 300 cm"),
        ]
    )
    weight = serializers.FloatField(
        required=True,
        validators=[
            MinValueValidator(1.0, message="Weight must greater than 1 kg"),
            MaxValueValidator(1000.0, message="Weight must less than 1000 kg"),
        ]
    )
    
    class Meta:
        model = User
        fields = ['phone_number', 'pin', 'full_name', 'date_of_birth', 'gender', 'height', 'weight']
        extra_kwargs = {
            'pin': {'write_only': True}
        }
    
    def validate(self, data):
        date_of_birth = data.get('date_of_birth')
        if date_of_birth and date_of_birth > datetime.now().date():
            raise ValidationException({
                "message": "Register serializer error",
                "errors": {
                    "date_of_birth": "Date of birth cannot be in the future."
                }})
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
    phone_number = serializers.CharField()
    pin = serializers.CharField(write_only=True)

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
    
    
# user info serializers
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


# health indicator serializers
class BloodGlucoseIndicatorSerializer(serializers.Serializer):
    blood_glucose_indicator = serializers.FloatField()
    unit = serializers.ChoiceField(choices=["mg/dL", "mmol/L"])
    meal = serializers.ChoiceField(choices=["pre-meal", "post-meal", "fasting", "before bed"])
    timestamp = serializers.DateTimeField(default=datetime.now, format="%Y-%m-%d %H:%M:%S")
    
class BloodPressureIndicatorSerializer(serializers.Serializer):
    systolic_indicator = serializers.IntegerField()
    diastolic_indicator = serializers.IntegerField()
    unit = serializers.CharField(default="mm Hg")
    timestamp = serializers.DateTimeField(default=datetime.now, format="%Y-%m-%d %H:%M:%S")

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