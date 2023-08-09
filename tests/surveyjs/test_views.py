import pytest
import test_helpers

from django.urls import reverse


pytestmark = [pytest.mark.django_db]


def tests_Attachment_list_view(client):
    instance1 = test_helpers.create_surveyjs_Attachment()
    instance2 = test_helpers.create_surveyjs_Attachment()
    url = reverse("surveyjs_Attachment_list")
    response = client.get(url)
    assert response.status_code == 200
    assert str(instance1) in response.content.decode("utf-8")
    assert str(instance2) in response.content.decode("utf-8")


def tests_Attachment_create_view(client):
    user = test_helpers.create_User()
    result = test_helpers.create_surveys_Result()
    url = reverse("surveyjs_Attachment_create")
    data = {
        "file": "aFile",
        "user": user.pk,
        "result": result.pk,
    }
    response = client.post(url, data)
    assert response.status_code == 302


def tests_Attachment_detail_view(client):
    instance = test_helpers.create_surveyjs_Attachment()
    url = reverse("surveyjs_Attachment_detail", args=[instance.pk, ])
    response = client.get(url)
    assert response.status_code == 200
    assert str(instance) in response.content.decode("utf-8")


def tests_Attachment_update_view(client):
    user = test_helpers.create_User()
    result = test_helpers.create_surveys_Result()
    instance = test_helpers.create_surveyjs_Attachment()
    url = reverse("surveyjs_Attachment_update", args=[instance.pk, ])
    data = {
        "file": "aFile",
        "user": user.pk,
        "result": result.pk,
    }
    response = client.post(url, data)
    assert response.status_code == 302


def tests_Survey_list_view(client):
    instance1 = test_helpers.create_surveyjs_Survey()
    instance2 = test_helpers.create_surveyjs_Survey()
    url = reverse("surveyjs_Survey_list")
    response = client.get(url)
    assert response.status_code == 200
    assert str(instance1) in response.content.decode("utf-8")
    assert str(instance2) in response.content.decode("utf-8")


def tests_Survey_create_view(client):
    user = test_helpers.create_User()
    url = reverse("surveyjs_Survey_create")
    data = {
        "post_id": "b297a243-b621-4907-8581-e9b3ac146a07",
        "json": {},
        "name": "text",
        "is_active": True,
        "user": user.pk,
    }
    response = client.post(url, data)
    assert response.status_code == 302


def tests_Survey_detail_view(client):
    instance = test_helpers.create_surveyjs_Survey()
    url = reverse("surveyjs_Survey_detail", args=[instance.pk, ])
    response = client.get(url)
    assert response.status_code == 200
    assert str(instance) in response.content.decode("utf-8")


def tests_Survey_update_view(client):
    user = test_helpers.create_User()
    instance = test_helpers.create_surveyjs_Survey()
    url = reverse("surveyjs_Survey_update", args=[instance.pk, ])
    data = {
        "post_id": "b297a243-b621-4907-8581-e9b3ac146a07",
        "json": {},
        "name": "text",
        "is_active": True,
        "user": user.pk,
    }
    response = client.post(url, data)
    assert response.status_code == 302


def tests_Result_list_view(client):
    instance1 = test_helpers.create_surveyjs_Result()
    instance2 = test_helpers.create_surveyjs_Result()
    url = reverse("surveyjs_Result_list")
    response = client.get(url)
    assert response.status_code == 200
    assert str(instance1) in response.content.decode("utf-8")
    assert str(instance2) in response.content.decode("utf-8")


def tests_Result_create_view(client):
    survey = test_helpers.create_surveys_Survey()
    user = test_helpers.create_User()
    url = reverse("surveyjs_Result_create")
    data = {
        "data": {},
        "survey": survey.pk,
        "user": user.pk,
    }
    response = client.post(url, data)
    assert response.status_code == 302


def tests_Result_detail_view(client):
    instance = test_helpers.create_surveyjs_Result()
    url = reverse("surveyjs_Result_detail", args=[instance.pk, ])
    response = client.get(url)
    assert response.status_code == 200
    assert str(instance) in response.content.decode("utf-8")


def tests_Result_update_view(client):
    survey = test_helpers.create_surveys_Survey()
    user = test_helpers.create_User()
    instance = test_helpers.create_surveyjs_Result()
    url = reverse("surveyjs_Result_update", args=[instance.pk, ])
    data = {
        "data": {},
        "survey": survey.pk,
        "user": user.pk,
    }
    response = client.post(url, data)
    assert response.status_code == 302
