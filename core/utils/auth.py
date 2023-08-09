from django.contrib.auth.backends import BaseBackend
from django.db.models import Q
from django.contrib.auth import get_user_model
UserProfile=get_user_model()

'''
  curl -X POST http://127.0.0.1:8000/api/v1/login/ 'Authorization: Token 3097411c832f3f79431c40c68e329a7cc3b160c0'
'''

class AuthBackend(BaseBackend):
    supports_object_permissions = True
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, userID):
      """
      get user by id, username, email or phone
      """
      user=UserProfile.objects.filter(
              Q(username=userID) | Q(email=userID) #| Q(phone=userID)
      ).first()
      return user

    def authenticate(self, request, username=None, password=None, token=None):
      user = self.get_user(username)
      return user if (user and user.check_password(password)) else None



