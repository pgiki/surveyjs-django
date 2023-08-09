from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from .utils import helpers
from .utils.mixins import PermissionsMixin
from django.contrib.auth.models import Group, Permission
# from django.contrib.contenttypes.models import ContentType
from django_restql.mixins import DynamicFieldsMixin
from django_restql.serializers import NestedModelSerializer
from django_restql.fields import DynamicSerializerMethodField, NestedField
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

User = get_user_model()


class PermissionSerializer(DynamicFieldsMixin, NestedModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "content_type"]


class GroupSerializer(DynamicFieldsMixin, NestedModelSerializer):
    permissions = NestedField(
        PermissionSerializer,
        many=True,
        required=False,
    )
    _permissions = DynamicSerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "permissions",
            "_permissions",
            "name",
        ]

    def get__permissions(self, obj, parsed_query=None):
        user = self.context["request"].user
        return helpers.get_permissions(obj=obj, user=user)


class UserSerializer(
    PermissionsMixin, DynamicFieldsMixin, NestedModelSerializer
):
    username = serializers.CharField()
    phone = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"})
    permissions = DynamicSerializerMethodField()
    is_phone_verified = DynamicSerializerMethodField()
    avatar = DynamicSerializerMethodField()

    class Meta:
        model = User
        write_only_fields = ("password", "phone")
        read_only_fields = (
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
            "permissions",
            "is_phone_verified",
        )
        fields = (
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "avatar"
        ) + read_only_fields + write_only_fields

        extra_kwargs = {field: {"read_only": True}
                        for field in read_only_fields}
        extra_kwargs.update(
            {field: {"write_only": True} for field in write_only_fields}
        )
        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=["username"],
                message="Sorry! An account already exists with this username or email",
            )
        ]

    def get_is_phone_verified(self, obj, query=None):
        return True

    def get_avatar(self, obj, query=None):
        profile = getattr(obj, 'profile', None)
        if not profile is None:
            avatar = profile.avatar
            if avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(avatar.url)
                return avatar.url
        return None

    def save(self, request=None, *args, **kwargs):
        if request and not self.instance:
            # remove the phone from validated list data
            is_valid = self.is_valid(raise_exception=True)
            # return None
            # access the validated data
            if is_valid:
                phone = None
                if self.validated_data.get('phone'):
                    phone = self.validated_data.pop('phone')
                    # TODO: find a way to save phone later
                user = super().save(*args, **kwargs)
                password = self.validated_data.get("password")
                if password:
                    user.set_password(password)
                    user.save()
                    self.instance = user
            else:
                return None
        else:
            # updating data
            self.instance = super().save(*args, **kwargs)
        return self.instance
