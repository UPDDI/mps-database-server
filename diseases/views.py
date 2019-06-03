from django.views.generic import ListView, DetailView  # , CreateView
# from mps.mixins import SpecificGroupRequiredMixin
from .models import Disease
from assays.models import AssayDataPoint
from microdevices.models import OrganModel
from drugtrials.models import FindingResult
from assays.utils import get_user_accessible_studies
from assays.views import (
    get_queryset_with_organ_model_map,
    get_queryset_with_number_of_data_points,
    get_queryset_with_stakeholder_sign_off
)


class DiseaseList(ListView):
    model = Disease
    template_name = 'diseases/disease_list.html'

    def get_queryset(self):
        queryset = Disease.objects.all()
        for disease in queryset:
            disease.trials = FindingResult.objects.filter(
                drug_trial__disease=disease
            )

            # TODO TODO TODO MUST REVISE
            disease.models = OrganModel.objects.filter(disease=disease)

            disease.studies = get_user_accessible_studies(
                self.request.user
            ).filter(
                assaymatrixitem__organ_model_id__in=disease.models
            ).distinct()

            disease.datapoints = AssayDataPoint.objects.filter(
                study_id__in=disease.studies
            ).count()
        return queryset


class DiseaseOverview(DetailView):
    model = Disease
    template_name = 'diseases/disease_overview.html'


class DiseaseBiology(DetailView):
    model = Disease
    template_name = 'diseases/disease_biology.html'


class DiseaseClinicalData(DetailView):
    model = Disease
    template_name = 'diseases/disease_clinicaldata.html'

    def get_context_data(self, **kwargs):
        context = super(DiseaseClinicalData, self).get_context_data(**kwargs)
        context['trial_findings'] = FindingResult.objects.filter(
            drug_trial__disease=self.object
        )
        return context


class DiseaseModel(DetailView):
    model = Disease
    template_name = 'diseases/disease_model.html'

    def get_context_data(self, **kwargs):
        context = {}
        context = super(DiseaseModel, self).get_context_data(**kwargs)
        context['disease_models'] = OrganModel.objects.filter(
            disease=self.object
        )

        combined = get_user_accessible_studies(self.request.user).filter(
            assaymatrixitem__organ_model_id__in=context['disease_models']
        ).distinct()

        get_queryset_with_organ_model_map(combined)
        get_queryset_with_number_of_data_points(combined)
        get_queryset_with_stakeholder_sign_off(combined)

        context['studies'] = combined
        return context
