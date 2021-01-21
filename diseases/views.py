# from django.views.generic import ListView, DetailView  # , CreateView
from mps.mixins import ListHandlerView, DetailHandlerView
from .models import Disease
from assays.models import AssayDataPoint, AssayStudy, AssayGroup
from microdevices.models import OrganModel, OrganModelProtocol
from drugtrials.models import FindingResult
from assays.utils import get_user_accessible_studies
from assays.views import (
    get_queryset_with_organ_model_map,
    get_queryset_with_number_of_data_points,
    get_queryset_with_stakeholder_sign_off
)
from mps.templatetags.custom_filters import (
    ADMIN_SUFFIX,
    VIEWER_SUFFIX,
)


class DiseaseList(ListHandlerView):
    model = Disease
    template_name = 'diseases/disease_list.html'

    # Messy querysets
    def get_queryset(self):
        queryset = Disease.objects.all()

        user_accessible_studies_ids = list(get_user_accessible_studies(
            self.request.user,
        ).filter(
            diseases__isnull=False
        ).values_list('id', flat=True))

        for disease in queryset:
            disease.trials = FindingResult.objects.filter(
                drug_trial__disease=disease
            )

            # TODO TODO TODO MUST REVISE
            # Disease is no longer attached to a particular model, but instead the version
            # disease.models = OrganModel.objects.filter(disease=disease)

            # disease_versions = OrganModelProtocol.objects.filter(disease=disease)

            # disease.models = OrganModel.objects.filter(id__in=disease_versions.values_list('organ_model_id', flat=True))

            # disease.studies = AssayStudy.objects.filter(
            #     id__in=user_accessible_studies_ids,
            #     assaygroup__organ_model_protocol__in=disease_versions
            # ).distinct().values_list('id', flat=True)

            # Instead we are going to find the studies first and then the models?
            disease.studies = AssayStudy.objects.filter(
                id__in=user_accessible_studies_ids,
                diseases=disease
            ).distinct()

            # Get the models from the groups in the study
            # Kind of a rough query, perhaps
            organ_model_ids = list(set(AssayGroup.objects.filter(study__in=disease.studies).values_list('organ_model_id', flat=True)))

            disease.models = OrganModel.objects.filter(
                id__in=organ_model_ids
            )

            if disease.studies:
                disease.datapoints = AssayDataPoint.objects.filter(
                    study_id__in=disease.studies
                ).count()
            else:
                disease.datapoints = 0

        return queryset


class DiseaseOverview(DetailHandlerView):
    model = Disease
    template_name = 'diseases/disease_overview.html'


class DiseaseBiology(DetailHandlerView):
    model = Disease
    template_name = 'diseases/disease_biology.html'


class DiseaseClinicalData(DetailHandlerView):
    model = Disease
    template_name = 'diseases/disease_clinicaldata.html'

    def get_context_data(self, **kwargs):
        context = super(DiseaseClinicalData, self).get_context_data(**kwargs)
        context['trial_findings'] = FindingResult.objects.filter(
            drug_trial__disease=self.object
        )
        return context


class DiseaseModel(DetailHandlerView):
    model = Disease
    template_name = 'diseases/disease_model.html'

    def get_context_data(self, **kwargs):
        context = super(DiseaseModel, self).get_context_data(**kwargs)

        # We now go in the opposite direction
        # SWAP TO VERSION (disease is no longer bound to models, but instead the version)
        # disease_models = OrganModelProtocol.objects.filter(disease=self.object).prefetch_related(
        #     'organ_model__organ',
        #     'organ_model__center__groups',
        #     'organ_model__device',
        #     'organ_model__base_model',
        # )

        # user_group_names = {
        #     user_group.name.replace(ADMIN_SUFFIX, ''): True for user_group in self.request.user.groups.all()
        # }

        # for version in disease_models:
        #     version.is_editable = version.organ_model.user_is_in_center(user_group_names)

        # context['disease_models'] = disease_models

        # combined = get_user_accessible_studies(self.request.user).filter(
        #     assaygroup__organ_model_protocol_id__in=context['disease_models']
        # ).distinct()

        # # NEEDS TO BE REVISED ALONG WITH OTHER SIMILAR KLUDGES
        # get_queryset_with_organ_model_map(combined)
        # get_queryset_with_number_of_data_points(combined)
        # get_queryset_with_stakeholder_sign_off(combined)

        # context['studies'] = combined

        studies = get_user_accessible_studies(self.request.user).filter(
            diseases=self.object
        ).distinct()

        # # NEEDS TO BE REVISED ALONG WITH OTHER SIMILAR KLUDGES
        get_queryset_with_organ_model_map(studies)
        get_queryset_with_number_of_data_points(studies)
        get_queryset_with_stakeholder_sign_off(studies)

        # Get the models from the groups in the study
        # Kind of a rough query, perhaps
        organ_model_ids = list(set(AssayGroup.objects.filter(
            study__in=studies
        ).values_list(
            'organ_model_id', flat=True
        )))

        disease_models = OrganModel.objects.filter(
            id__in=organ_model_ids
        ).prefetch_related(
            'organ',
            'center__groups',
            'device',
            'base_model',
        )

        context.update({
            'disease_models': disease_models,
            'studies': studies
        })

        return context
