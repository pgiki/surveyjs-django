from django.urls import path, include
from rest_framework import routers

from . import api
from . import views


router = routers.DefaultRouter(trailing_slash=False)
# First addition
# Now setup a router that does not require a trailing slash
slashless_router = routers.DefaultRouter(trailing_slash=False)


router.register("Attachment", api.AttachmentViewSet)
router.register("Survey", api.SurveyViewSet)
router.register("Result", api.ResultViewSet)
slashless_router.registry = router.registry[:]

urlpatterns = (
    path("api/v1/", include(router.urls)),
    path("api/v1/", include(slashless_router.urls)),
    path("surveyjs/Attachment/", views.AttachmentListView.as_view(), name="surveyjs_Attachment_list"),
    path("surveyjs/Attachment/create/", views.AttachmentCreateView.as_view(), name="surveyjs_Attachment_create"),
    path("surveyjs/Attachment/detail/<int:pk>/", views.AttachmentDetailView.as_view(), name="surveyjs_Attachment_detail"),
    path("surveyjs/Attachment/update/<int:pk>/", views.AttachmentUpdateView.as_view(), name="surveyjs_Attachment_update"),
    path("surveyjs/Attachment/delete/<int:pk>/", views.AttachmentDeleteView.as_view(), name="surveyjs_Attachment_delete"),
    path("surveyjs/Survey/", views.SurveyListView.as_view(), name="surveyjs_Survey_list"),
    path("surveyjs/Survey/create/", views.SurveyCreateView.as_view(), name="surveyjs_Survey_create"),
    path("surveyjs/Survey/detail/<int:pk>/", views.SurveyDetailView.as_view(), name="surveyjs_Survey_detail"),
    path("surveyjs/Survey/update/<int:pk>/", views.SurveyUpdateView.as_view(), name="surveyjs_Survey_update"),
    path("surveyjs/Survey/delete/<int:pk>/", views.SurveyDeleteView.as_view(), name="surveyjs_Survey_delete"),
    path("surveyjs/Result/", views.ResultListView.as_view(), name="surveyjs_Result_list"),
    path("surveyjs/Result/create/", views.ResultCreateView.as_view(), name="surveyjs_Result_create"),
    path("surveyjs/Result/detail/<int:pk>/", views.ResultDetailView.as_view(), name="surveyjs_Result_detail"),
    path("surveyjs/Result/update/<int:pk>/", views.ResultUpdateView.as_view(), name="surveyjs_Result_update"),
    path("surveyjs/Result/delete/<int:pk>/", views.ResultDeleteView.as_view(), name="surveyjs_Result_delete"),

)
