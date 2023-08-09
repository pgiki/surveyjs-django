from django import forms
from django.contrib.auth.models import User
from surveyjs.models import Result, Survey
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from . import models


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = models.Attachment
        fields = [
            "file",
            "user",
            "result",
        ]

    def __init__(self, *args, **kwargs):
        super(AttachmentForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.all()
        self.fields["result"].queryset = Result.objects.all()



class SurveyForm(forms.ModelForm):
    class Meta:
        model = models.Survey
        fields = [
            "post_id",
            "json",
            "name",
            "is_active",
            "user",
        ]

    def __init__(self, *args, **kwargs):
        super(SurveyForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.all()



class ResultForm(forms.ModelForm):
    class Meta:
        model = models.Result
        fields = [
            "data",
            "survey",
            "user",
        ]

    def __init__(self, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)
        self.fields["survey"].queryset = Survey.objects.all()
        self.fields["user"].queryset = User.objects.all()

