import pyotp
import base64

# django models
from django.conf import settings


class PhoneNumber:
    def __init__(self, phone, **kwargs):
        self.phone = phone

    def is_otp_valid(self, otp):
        """For validating otps shared to contacts"""
        OTP_KEY = base64.b32encode(self.phone.encode("ascii")).decode()
        totp = pyotp.TOTP(OTP_KEY)
        return totp.verify(otp, valid_window=settings.OTP_VALID_WINDOW)

    def get_otp(self):
        OTP_KEY = base64.b32encode(self.phone.encode("ascii")).decode()
        totp = pyotp.TOTP(OTP_KEY)
        return totp.now()
