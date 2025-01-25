from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, phone_number, pin, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required.")
        if not pin:
            raise ValueError("PIN is required.")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_pin(pin)
        user.save()
        return user