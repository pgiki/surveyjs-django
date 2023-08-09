from django.views import generic
from django.urls import reverse_lazy
from . import models
from . import forms


class AttachmentListView(generic.ListView):
    model = models.Attachment
    form_class = forms.AttachmentForm


class AttachmentCreateView(generic.CreateView):
    model = models.Attachment
    form_class = forms.AttachmentForm


class AttachmentDetailView(generic.DetailView):
    model = models.Attachment
    form_class = forms.AttachmentForm


class AttachmentUpdateView(generic.UpdateView):
    model = models.Attachment
    form_class = forms.AttachmentForm
    pk_url_kwarg = "pk"


class AttachmentDeleteView(generic.DeleteView):
    model = models.Attachment
    success_url = reverse_lazy("surveyjs_Attachment_list")


class SurveyListView(generic.ListView):
    model = models.Survey
    form_class = forms.SurveyForm


class SurveyCreateView(generic.CreateView):
    model = models.Survey
    form_class = forms.SurveyForm


class SurveyDetailView(generic.DetailView):
    model = models.Survey
    form_class = forms.SurveyForm


class SurveyUpdateView(generic.UpdateView):
    model = models.Survey
    form_class = forms.SurveyForm
    pk_url_kwarg = "pk"


class SurveyDeleteView(generic.DeleteView):
    model = models.Survey
    success_url = reverse_lazy("surveyjs_Survey_list")


class ResultListView(generic.ListView):
    model = models.Result
    form_class = forms.ResultForm


class ResultCreateView(generic.CreateView):
    model = models.Result
    form_class = forms.ResultForm


class ResultDetailView(generic.DetailView):
    model = models.Result
    form_class = forms.ResultForm


class ResultUpdateView(generic.UpdateView):
    model = models.Result
    form_class = forms.ResultForm
    pk_url_kwarg = "pk"


class ResultDeleteView(generic.DeleteView):
    model = models.Result
    success_url = reverse_lazy("surveyjs_Result_list")
