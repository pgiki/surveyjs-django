from django.urls import path, include
from rest_framework import routers
from django.views.generic import TemplateView
from . import api


router = routers.DefaultRouter(trailing_slash=False)
# First addition
# Now setup a router that does not require a trailing slash
slashless_router = routers.DefaultRouter(trailing_slash=False)


router.register("Attachment", api.AttachmentViewSet)
router.register("Survey", api.SurveyViewSet)
router.register("Result", api.ResultViewSet)
slashless_router.registry = router.registry[:]

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("api/v1/", include(slashless_router.urls)),
]
# these are path defined in the surveyjs
for p in ["", "about", "run/<slug:slug>", "edit/<slug:slug>", "results/<slug:slug>"]:
    urlpatterns.append(
        path(p, TemplateView.as_view(template_name='surveyjs-react-client/index.html'))
    )