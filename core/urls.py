from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers
from . import api

from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title="Yagete API")

router = routers.DefaultRouter()
router.register("User", api.UserViewSet)
urlpatterns = (
    url(r"^$", schema_view),
    path("api/v1/", include(router.urls)),
)
