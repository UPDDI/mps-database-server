#import datetime
from haystack import indexes
from .models import *


class AssayStudyConfigurationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)

    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return AssayStudyConfiguration


class AssayStudyIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.NgramField(document=True, use_template=True)

    permissions = indexes.NgramField(use_template=True, indexed=False)

    rendered = indexes.CharField(use_template=True, indexed=False)

    def get_model(self):
        return AssayStudy

    def index_queryset(self, using=None):
        queryset = self.get_model().objects.all().prefetch_related(
            'assaystudystakeholder_set__group',
            'assaystudyassay_set__target',
            'assaystudyassay_set__method',
            'assaystudyassay_set__unit',
            'assaystudyassay_set__unit',
            'assaymatrixitem_set__assaysetupsetting_set__setting',
            'assaymatrixitem_set__assaysetupcell_set__cell_sample',
            'assaymatrixitem_set__assaysetupcell_set__density_unit',
            'assaymatrixitem_set__assaysetupcell_set__cell_sample__cell_type__organ',
            'assaymatrixitem_set__assaysetupcompound_set__compound_instance__compound',
            'assaymatrixitem_set__assaysetupcompound_set__concentration_unit',
            'assaymatrixitem_set__device',
            'assaymatrixitem_set__organ_model',
        )

        stakeholders = AssayStudyStakeholder.objects.filter(
            sign_off_required=False,
            signed_off_by_id=None
        )

        stakeholder_map = {}

        for stakeholder in stakeholders:
            stakeholder_map.update({
                stakeholder.study_id: True
            })

        for object in queryset:
            if object.id in stakeholder_map:
                object.stakeholder_approval = False
            else:
                object.stakeholder_approval = True

        return queryset
