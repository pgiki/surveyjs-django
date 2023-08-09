from django.contrib import admin
from django import forms
from guardian.admin import GuardedModelAdmin
from import_export.admin import ImportExportModelAdmin

from . import models


class AttachmentAdminForm(forms.ModelForm):

    class Meta:
        model = models.Attachment
        fields = "__all__"


class AttachmentAdmin(GuardedModelAdmin, ImportExportModelAdmin):
    form = AttachmentAdminForm
    list_display = [
        "id",
        "last_updated",
        "file",
        "created",
    ]


class SurveyAdminForm(forms.ModelForm):

    class Meta:
        model = models.Survey
        fields = "__all__"


class SurveyAdmin(GuardedModelAdmin, ImportExportModelAdmin):
    form = SurveyAdminForm
    list_display = [
         "id",
        "created",
        "post_id",
        "last_updated",
        "json",
        "name",
        "is_active",
    ]

class ResultAdminForm(forms.ModelForm):

    class Meta:
        model = models.Result
        fields = "__all__"


class ResultAdmin(GuardedModelAdmin, ImportExportModelAdmin):
    form = ResultAdminForm
    list_display = [
         "id",
        "data",
        "last_updated",
        "created",
    ]


admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.Survey, SurveyAdmin)
admin.site.register(models.Result, ResultAdmin)
