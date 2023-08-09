import random
import string

from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType

from surveyjs import models as surveyjs_models


def random_string(length=10):
    # Create a random string of length length
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def create_User(**kwargs):
    defaults = {
        "username": "%s_username" % random_string(5),
        "email": "%s_username@tempurl.com" % random_string(5),
    }
    defaults.update(**kwargs)
    return User.objects.create(**defaults)


def create_AbstractUser(**kwargs):
    defaults = {
        "username": "%s_username" % random_string(5),
        "email": "%s_username@tempurl.com" % random_string(5),
    }
    defaults.update(**kwargs)
    return AbstractUser.objects.create(**defaults)


def create_AbstractBaseUser(**kwargs):
    defaults = {
        "username": "%s_username" % random_string(5),
        "email": "%s_username@tempurl.com" % random_string(5),
    }
    defaults.update(**kwargs)
    return AbstractBaseUser.objects.create(**defaults)


def create_Group(**kwargs):
    defaults = {
        "name": "%s_group" % random_string(5),
    }
    defaults.update(**kwargs)
    return Group.objects.create(**defaults)


def create_ContentType(**kwargs):
    defaults = {
    }
    defaults.update(**kwargs)
    return ContentType.objects.create(**defaults)


def create_surveyjs_Attachment(**kwargs):
    defaults = {}
    defaults["file"] = ""
    if "user" not in kwargs:
        defaults["user"] = create_User()
    if "result" not in kwargs:
        defaults["result"] = create_surveys_Result()
    defaults.update(**kwargs)
    return surveyjs_models.Attachment.objects.create(**defaults)
def create_surveyjs_Survey(**kwargs):
    defaults = {}
    defaults["post_id"] = ""
    defaults["json"] = ""
    defaults["name"] = ""
    defaults["is_active"] = ""
    if "user" not in kwargs:
        defaults["user"] = create_User()
    defaults.update(**kwargs)
    return surveyjs_models.Survey.objects.create(**defaults)
def create_surveyjs_Result(**kwargs):
    defaults = {}
    defaults["data"] = ""
    if "survey" not in kwargs:
        defaults["survey"] = create_surveys_Survey()
    if "user" not in kwargs:
        defaults["user"] = create_User()
    defaults.update(**kwargs)
    return surveyjs_models.Result.objects.create(**defaults)
