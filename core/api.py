from rest_framework import status
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from rest_framework import viewsets, permissions
from core.utils.otp import PhoneNumber
from core.utils.mixins import MixinViewSet
from . import serializers
from .utils import helpers
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()


class UserViewSet(MixinViewSet, viewsets.ModelViewSet):
    """ViewSet for the User class"""

    serializer_class = serializers.UserSerializer
    queryset = serializer_class.Meta.model.objects.all().exclude(
        username=getattr(settings, 'ANONYMOUS_USER_NAME', 'nobody')
    )
    filterset_fields = [
        "id",
        "username",
        "first_name",
        "last_name",
    ]

    @action(
        detail=False,
        permission_classes=[permissions.AllowAny],
        methods=["POST"],
        name="Verify the phone number",
    )
    def verify_otp(self, request, *args, **kwargs):
        """
        TODO: decide whether to use same key for every user or separate key for each user
        now using unique key otp generator per user to prevent users requesting OTP which can then use to access others accounts

        used for verifying phone numbers as well as resetting passwords
        """
        user = request.user
        success = False
        phone_obj = None
        errors = []
        email = request.data.get("email")
        phone = request.data.get("phone")
        otp = request.data.get("otp")

        if otp:
            otp = str(otp)

        email = request.data.get("email")
        phone = request.data.get("phone")
        username = request.data.get("phone")

        if not user.is_authenticated:
            q = Q()
            if email:
                q = Q(email=email)
            if phone:
                q |= Q(username=phone)
            if username and username!=phone:
                q |= Q(username=username)
            user = User.objects.filter(q).first()
            if not user:
                errors.append(_("Invalid email or phone number. Try again"))
                return Response({"success": success, "errors": errors})
            else:
                email = user.email
                phone_obj = PhoneNumber(phone)

        if phone:
            if phone_obj and otp:
                # TODO: find a safe way to counter verify firebase OTP
                # TODO: make sure to remove the safe test OTP when in production
                if "firebase" in otp or phone_obj.is_otp_valid(otp) or otp == "000000":
                    success = True
                    if user.is_authenticated:
                        password = request.data.get("password")
                        if password:
                            user.set_password(password)

                        if "firebase" in otp:
                            phone_obj.verification_source = "firebase"
                        else:
                            phone_obj.verification_source = "smsbomba"
                        user.save()
                else:
                    errors.append("Invalid OTP. Try again")
            elif not otp:
                errors.append("`otp` is required")
            else:
                errors.append("This phone number is not valid")
        else:
            errors.append("`phone` is required")
        return Response({"success": success, "errors": errors})
    
    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["POST"],
        name=_("Request otp to be sent to the user"),
    )
    def request_otp(self, request, *args, **kwargs):
        """
        TODO: decide whether to use same key for every user or separate key for each user
        now using unique key otp generator per user to prevent users requesting OTP which can then use to access others accounts
        send the OTP by message to the requested number
        """
        user = request.user
        success = False
        phone_obj = None
        errors = []

        email = request.data.get("email")
        phone = request.data.get("phone")
        username = request.data.get("phone")

        if not user.is_authenticated:
            q = Q()
            if email:
                q = Q(email=email)
            if phone:
                q |= Q(username=phone)
            if username and username!=phone:
                q |= Q(username=username)
            user = User.objects.filter(q).first()
            if not user:
                errors.append(_("Invalid email or phone number. Try again"))
                return Response({"success": success, "errors": errors})
            else:
                email = user.email

        otp = None
        if phone:
            phone_obj = PhoneNumber(phone)
            otp = phone_obj.get_otp()
            try:
                success = True
                message = _(
                    "<#> Your OTP is: %(otp)s. Thanks for choosing us!"
                ) % {"otp": str(otp)}
                if email:
                    send_mail(
                        _("Security Code"),
                        _(
                            "Your OTP is: %(otp)s. Thanks for choosing us!\nBest Regards\nTeam"
                        )
                        % {"otp": str(otp)},
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=True,
                    )
                else:
                    helpers.sendsms(phone=phone, message=message)
            except Exception as e:
                errors.append(_("Error sending OTP: %(error)s") % {"error": str(e)})
                success = True
        else:
            errors.append(_("`phone` is required"))
        return Response({"success": success, "otp": otp, "errors": errors})
    
    @action(
        # permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["POST", "GET"],
        name="Request otp to be sent to the user",
    )
    def delete_account(self, request, *args, **kwargs):
        """
        Send a notification to admins to delete an account
        """
        user = request.user
        user_id = user.id
        body = _(
            "The request to delete account with ID %(user_id)d was received. This process is done manually but processed within 1 working days. You will be notified when ready. We are sorry to see you go"
        ) % {"user_id": user_id}
        users = User.objects.filter(Q(is_superuser=True) | Q(id=user_id))
        helpers.notify_users(
            users=users,
            sender=user,
            target=user,
            level="warning",
            title=_("Account Deletion"),
            body=body,
        )
        return Response({"success": True, "user_id": user_id})

    @action(
        detail=False,
        methods=["POST"],
        name="Check if user exists",
    )
    def check(self, request, *args, **kwargs):
        """
        Search or create user if it doesn't exist
        """
        status_code = status.HTTP_200_OK
        username = request.data.get('username')
        phone = request.data.get('phone')
        email = request.data.get('email')
        q=Q()
        if username:
            q|=Q(username=username)
        if phone and phone!=username:
            q|=Q(username=phone)
        if email:
            q|=Q(email=email)
        res={"exists": self.queryset.filter(q).exists()}
        return Response(res, status=status_code)
