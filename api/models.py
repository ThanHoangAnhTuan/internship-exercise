from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from .managers import UserManager
from mongoengine import Document, fields, ListField, EmbeddedDocumentField, EmbeddedDocument
from datetime import datetime

class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=10, unique=True, validators=[
            RegexValidator(
                regex=r'^0\d{9}$', 
                message="The phone number must start with 0 and have 10 digits."
            )
        ])
    pin = models.CharField(max_length=128, validators=[RegexValidator(regex=r'^\d{6}$', message="PIN must be 6 digits long.")], null=False, blank=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    password = None
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.phone_number
    
    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)

    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin)
    
class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_info')
    full_name = models.CharField(max_length=255, null=False, blank=False)
    date_of_birth = models.DateField(null=False, blank=False)
    gender = models.CharField(max_length=5, choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], null=False, blank=False)
    
    def __str__(self):
        return f"UserInfo for {self.full_name}"

class UserHealthInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_health_info')
    height = models.FloatField(null=False, blank=False, validators=[
            MinValueValidator(1.0, message="Height must greater than 1 cm"),
            MaxValueValidator(300.0, message="Height must less than 300 cm"),
        ])
    weight = models.FloatField(null=False, blank=False, validators=[
            MinValueValidator(1.0, message="Weight must greater than 1 kg"),
            MaxValueValidator(1000.0, message="Weight must less than 1000 kg"),
        ])
    blood_glucose = models.FloatField(null=True, blank=True) # (mg/dL or mmol/L)
    blood_pressure = models.IntegerField(null=True, blank=True)  # (mm Hg)
    
    def __str__(self):
        return f"UserHealthInfo for {self.user.phone_number}"

class BloodGlucoseIndicator(EmbeddedDocument):
    blood_glucose_indicator = fields.FloatField(required=True)
    unit = fields.StringField(choices=["mg/dL", "mmol/L"], required=True)
    timestamp = fields.DateTimeField(default=datetime.now)
    meal = fields.StringField(choices=["pre-meal", "post-meal", "fasting", "before go to bed"], required=True)

class BloodPressureIndicator(EmbeddedDocument):
    systolic_indicator = fields.IntField(required=True)
    diastolic_indicator = fields.IntField(required=True)
    unit = fields.StringField(default="mm Hg")
    timestamp = fields.DateTimeField(default=datetime.now)
    
class UserHealthIndicator(Document):
    user_id = fields.IntField(required=True, unique=True)
    blood_glucose_list = ListField(EmbeddedDocumentField(BloodGlucoseIndicator))
    blood_pressure_list = ListField(EmbeddedDocumentField(BloodPressureIndicator))
    meta = {
        'collection': 'user_health_indicator',
        'indexes': ['user_id'],
        'ordering': ['-timestamp']
    }
    
