from rest_framework import serializers
from . import models
# from core.utils.mixins import PermissionsMixin
from django_restql.mixins import DynamicFieldsMixin
from django_restql.serializers import NestedModelSerializer
from django_restql.fields import DynamicSerializerMethodField, NestedField
from core.serializers import UserSerializer

class AttachmentSerializer(DynamicFieldsMixin, NestedModelSerializer):
    user = NestedField(
        UserSerializer,
        accept_pk=True,
        required=False,
        default=serializers.CurrentUserDefault(),
        create_ops=["create"],
        update_ops=["add", "create", "remove", "update"],
    )
    class Meta:
        model = models.Attachment
        fields = [
            "last_updated",
            "file",
            "created",
            "user",
            "result",
        ]

class SurveySerializer(DynamicFieldsMixin, NestedModelSerializer):
    user = NestedField(
        UserSerializer,
        accept_pk=True,
        required=False,
        default=serializers.CurrentUserDefault(),
        create_ops=["create"],
        update_ops=["add", "create", "remove", "update"],
    )
    postId = serializers.CharField(source='post_id', required=False)
    class Meta:
        model = models.Survey
        fields = [
            "id",
            "created",
            "last_updated",
            "post_id",
            "postId",
            "json",
            "name",
            "is_active",
            "user",
        ]

class ResultSerializer(DynamicFieldsMixin, NestedModelSerializer):
    user = NestedField(
        UserSerializer,
        accept_pk=True,
        required=False,
        default=serializers.CurrentUserDefault(),
        create_ops=["create"],
        update_ops=["add", "create", "remove", "update"],
    )
    survey = NestedField(
        SurveySerializer,
        accept_pk=True,
        required=False,
        default=serializers.CurrentUserDefault(),
        create_ops=["create"],
        update_ops=["add", "create", "remove", "update"],
    )
    class Meta:
        model = models.Result
        fields = [
            "id",
            "last_updated",
            "created",
            "data",
            "survey",
            "user",
        ]
