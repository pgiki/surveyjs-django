from django.utils import timezone
from rest_framework import status
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from rest_framework import viewsets, permissions
from core.utils.otp import PhoneNumber
from core.utils.mixins import MixinViewSet
from . import serializers
from . import models
from .utils import helpers

# extra imports
from django.conf import settings

# from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

# from guardian.shortcuts import assign_perm, get_objects_for_user
from django.contrib.auth import get_user_model

User = get_user_model()


class UserViewSet(MixinViewSet, viewsets.ModelViewSet):
    """ViewSet for the User class"""

    serializer_class = serializers.UserSerializer
    queryset = serializer_class.Meta.model.objects.all().exclude(
        username=settings.getattr('ANONYMOUS_USER_NAME', 'nobody')
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
        data = request.data.copy()
        email = request.data.get("email")
        phone = data.get("phone")
        otp = data.get("otp")

        if otp:
            otp = str(otp)

        if not user.is_authenticated:
            q = Q()
            if email:
                q |= Q(email=email)
            if phone:
                q |= Q(username=phone)

            user = User.objects.filter(q).first()
            if not user:
                errors.append("Invalid email or phone number. Try again")
                return Response({"success": success, "errors": errors})
            else:
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
        data = request.data.copy()
        email = request.data.get("email")
        phone = data.get("phone")

        if not user.is_authenticated:
            q = Q()
            if email:
                q = Q(email=email)
            if phone:
                q |= Q(username=phone)

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
                    "<#> OTP for linkgete is: %(otp)s. Thanks for choosing us!"
                ) % {"otp": str(otp)}
                if email:
                    send_mail(
                        _("Niwezeshe Security Code"),
                        _(
                            "OTP for niwezeshe is: %(otp)s. Thanks for choosing us!\nBest Regards\nLinkGete Team"
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
        detail=False,
        methods=["POST"],
        name="Get or create user",
    )
    def get_or_create(self, request, *args, **kwargs):
        """
        Search or create user if it doesn't exist
        limit this feature to selected user whose profile.can_allocate_loans = True
        """
        status_code = status.HTTP_200_OK
        res = dict()
        username = request.data.get("username")
        user_id = request.data.get("id")
        user = None
        logged_user = request.user
        data = request.data

        if logged_user.profile.can_allocate_loans:
            if user_id:
                user = self.queryset.filter(id=user_id).first()
                if not user:
                    status_code = status.HTTP_404_NOT_FOUND
                    res["detail"] = _("No user with this id exists")
            if username:
                # assume username is phone number
                is_phone_valid, username = helpers.format_phone(username)
                user = self.queryset.filter(username=username).first()
                if not user and (is_phone_valid or username.isalpha()):
                    data["username"] = username
                    if not "password" in data:
                        data["password"] = str(timezone.now())
                    # also check if has any contacts under this name and sign up using the credentials
                    contact = (
                        models.Contact.objects.filter(
                            user=logged_user, phone_numbers__phone=username
                        )
                        .values("first_name", "last_name")
                        .first()
                    )
                    if contact:
                        # add first_name and last_name from contacts
                        data.update(contact)
                    ser = self.serializer_class(data=data)
                    if ser.is_valid():
                        user = ser.save(request=request)
                        status_code = status.HTTP_201_CREATED
                    else:
                        res["errors"] = ser.errors
                        status_code = status.HTTP_400_BAD_REQUEST
                elif not is_phone_valid and not username.isalpha():
                    status_code = status.HTTP_400_BAD_REQUEST
                    res["detail"] = _(
                        "This provided `username` is neither a phone number nor a valid username"
                    )

            if user:
                res.update(
                    self.serializer_class(
                        user, context=self.get_serializer_context()
                    ).data
                )
        else:
            status_code = status.HTTP_403_FORBIDDEN
            res["detail"] = _(
                "You do not have access to this feature. Please contact the admin if you this is an error"
            )
        return Response(res, status=status_code)
