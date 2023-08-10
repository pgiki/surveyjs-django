from django.db import models
from django.urls import reverse
from uuid import uuid4
from django.conf import settings


class Attachment(models.Model):

    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, help_text='The person who uploaded the document')
    result = models.ForeignKey("surveyjs.Result", on_delete=models.CASCADE, null=True, blank=True, help_text='The result which this attachment is originated to')

    # Fields
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    file = models.FileField(upload_to="upload/files/")
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        pass

    def __str__(self):
        return str(self.file)



class Survey(models.Model):

    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, help_text='The person who created the survey')

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    post_id = models.UUIDField(blank=True, default=uuid4)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    json = models.JSONField(default=dict, blank=True)
    name = models.CharField(max_length=255, default=uuid4, blank=True)
    is_active = models.BooleanField(default=True, blank=True)

    class Meta:
        permissions = (("submit_survey", "Can submit survey"),("survey_view_result", "Can view survey results"),)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = str(uuid4())
        return super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)



class Result(models.Model):

    # Relationships
    survey = models.ForeignKey("surveyjs.Survey", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, help_text='The person who submitted the survey if submitted while logged in')

    # Fields
    data = models.JSONField(default=dict, blank=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        pass

    def __str__(self):
        return str(self.data)[:10]


