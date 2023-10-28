from copy import copy
from uuid import uuid4
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from . import serializers
from . import models
from core.utils.mixins import MixinViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import (
    SessionAuthentication,
    BasicAuthentication,
    TokenAuthentication,
)
from dj_rest_auth.jwt_auth import JWTCookieAuthentication
from django.utils.translation import gettext as _
from guardian.shortcuts import (
    get_perms,
    get_objects_for_user,
)


class AttachmentViewSet(MixinViewSet, viewsets.ModelViewSet):
    """ViewSet for the Attachment class"""

    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filterset_fields = [
        "id",
        "name",
        "user__id",
    ]


class SurveyViewSet(MixinViewSet, viewsets.ModelViewSet):
    """ViewSet for the Survey class"""

    queryset = models.Survey.objects.all()
    serializer_class = serializers.SurveySerializer
    filterset_fields = [
        "id",
        "name",
        "post_id",
        "user__id",
    ]

    authentication_classes = [
        TokenAuthentication,
        JWTCookieAuthentication,
        SessionAuthentication,
        BasicAuthentication,
    ]

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["GET"],
        name=_("Get active surveys"),
    )
    def getActive(self, request, *args, **kwargs):
        """
        creates responses in bulk from the survey data
        """
        qs = self.filter_queryset(self.get_queryset().filter(is_active=True))
        data = self.serializer_class(
            qs, many=True, context=self.get_serializer_context()
        ).data
        return Response(data)

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["GET"],
        name=_("Get a specific survey"),
    )
    def getSurvey(self, request, *args, **kwargs):
        """
        get a specific survey using survey Id
        """
        survey_id = request.GET.get("surveyId", 0)
        qs = self.filter_queryset(self.get_queryset()).filter(pk=survey_id).first()
        data = self.serializer_class(qs, context=self.get_serializer_context()).data
        return Response(data)

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["GET", "POST"],
        name=_("Get a specific survey"),
    )
    def changeName(self, request, *args, **kwargs):
        """
        Change the name of the survey
        """
        user = request.user
        survey_name = request.GET.get("name", request.data.get("name"))
        survey_id = request.GET.get("id", request.data.get("id"))
        survey = models.Survey.objects.get(id=survey_id)
        if "change_survey" in get_perms(user, survey):
            success = True
            survey.name = survey_name
            survey.save(update_fields=["name"])
        data = {"success": success}
        return Response(data)

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["POST", "GET"],
        name=_("Create a new survey"),
        url_path="create",
    )
    def createSurvey(self, request, *args, **kwargs):
        """
        Create a new survey
        """
        user = request.user
        data = {}
        if user.has_perm("add_survey"):
            survey_data = copy(request.data)
            if not survey_data.get("name"):
                survey_data["name"] = str(uuid4())
            if user.is_authenticated:
                survey_data["user"] = user.id
            ser = self.serializer_class(
                data=survey_data, context=self.get_serializer_context()
            )
            if ser.is_valid():
                ser.save()
                return Response(ser.data, status=201)
            else:
                return Response(ser.errors, status=406)
        return Response(data, status=403)

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["POST"],
        name=_("change Survey Json data"),
    )
    def changeJson(self, request, *args, **kwargs):
        """
        Change the name of the survey
        """
        user = request.user
        survey_json = request.GET.get("json", request.data.get("json"))
        survey_id = request.GET.get("id", request.data.get("id"))
        survey = models.Survey.objects.get(id=survey_id)
        if "change_survey" in get_perms(user, survey):
            update_fields = ["json"]
            if survey_json.get("title"):
                survey.name = survey_json.get("title")
                update_fields.append("name")
            survey.json = survey_json
            survey.save(update_fields=update_fields)
            return Response(
                self.serializer_class(
                    survey, context=self.get_serializer_context()
                ).data
            )
        return Response({})

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["POST"],
        name=_("Save survey Results"),
        url_path="post",
    )
    def saveResults(self, request, *args, **kwargs):
        """
        Change the name of the survey
        """
        user = request.user
        data = request.data.get("surveyResult")
        post_id = request.data.get("postId")
        survey = models.Survey.objects.get(post_id=post_id)
        if "submit_survey" in get_perms(user, survey):
            ser = serializers.ResultSerializer(
                data={"survey": survey.id, "data": data},
                context=self.get_serializer_context(),
            )
            if ser.is_valid():
                ser.save()
                return Response(ser.data)
            else:
                return Response(ser.errors)
        return Response({}, status=403)

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["POST", "GET", "DELETE"],
        name=_("delete specific survey"),
        url_path="delete",
    )
    def deleteSurvey(self, request, *args, **kwargs):
        """
        Change the name of the survey
        """
        user = request.user
        survey_id = request.GET.get("id", request.data.get("id"))
        survey = get_object_or_404(models.Survey, id=survey_id)
        if "delete_survey" in get_perms(user, survey):
            models.Survey.objects.filter(id=survey_id).delete()
            return Response({"success": True, "id": survey_id})
        return Response({}, status=403)

    @action(
        permission_classes=[permissions.AllowAny],
        detail=False,
        methods=["GET"],
        name=_("View Survey results"),
        url_path="results",
    )
    def viewResults(self, request, *args, **kwargs):
        """
        View all the survey results
        """
        user = request.user
        survey_id = request.GET.get("postId")
        survey = models.Survey.objects.get(post_id=survey_id)
        if "survey_view_result" in get_perms(user, survey):
            qs = get_objects_for_user(user, perms=["surveyjs.view_result"]).filter(
                survey=survey
            )
            return Response(
                serializers.ResultSerializer(
                    qs, many=True, context=self.get_serializer_context()
                ).data
            )
        return Response({}, status=403)


class ResultViewSet(MixinViewSet, viewsets.ModelViewSet):
    """ViewSet for the Result class"""

    queryset = models.Result.objects.all()
    serializer_class = serializers.ResultSerializer
    filterset_fields = [
        "id",
        "survey__id",
    ]
