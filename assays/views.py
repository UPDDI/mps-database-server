# coding=utf-8
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.http import HttpResponse
# from assays.models import *
from cellsamples.models import CellSample
# TODO TRIM THIS IMPORT
# from assays.admin import *
from assays.forms import *
from django import forms

# TODO REVISE SPAGHETTI CODE
from assays.ajax import get_chip_readout_data_as_csv
from assays.utils import (
    parse_file_and_save,
    modify_qc_status_plate,
    modify_qc_status_chip,
    save_assay_layout,
    TIME_CONVERSIONS,
    CHIP_DATA_PREFETCH,
    REPLACED_DATA_POINT_CODE,
    EXCLUDED_DATA_POINT_CODE
)

from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect
# from django.contrib.auth.models import Group
# from django.core.exceptions import PermissionDenied
# from django.contrib.auth.decorators import login_required
# from django.utils.decorators import method_decorator

from mps.templatetags.custom_filters import (
    ADMIN_SUFFIX,
    VIEWER_SUFFIX,
    filter_groups,
    is_group_editor,
    is_group_admin
)

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test

from mps.mixins import (
    LoginRequiredMixin,
    OneGroupRequiredMixin,
    ObjectGroupRequiredMixin,
    StudyGroupRequiredMixin,
    StudyViewershipMixin,
    # DetailRedirectMixin,
    # AdminRequiredMixin,
    DeletionMixin,
    SuperuserRequiredMixin,
    # CreatorOrAdminRequiredMixin,
    # SpecificGroupRequiredMixin,
    user_is_active,
    PermissionDenied
)

from mps.base.models import save_forms_with_tracking
from django.contrib.auth.models import User
from mps.settings import DEFAULT_FROM_EMAIL

# import ujson as json
import os

from mps.settings import MEDIA_ROOT, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX

from django.template.loader import render_to_string, TemplateDoesNotExist

from datetime import datetime, timedelta
import pytz

# TODO Refactor imports
# TODO REFACTOR CERTAIN WHITTLING TO BE IN FORM AS OPPOSED TO VIEW
# TODO Rename get_absolute_url when the function does not actually return the model's URL
# TODO It is probably more semantic to overwrite get_context_data and form_valid in lieu of post and get for updates
# TODO ^ Update Views should be refactored soon
# NOTE THAT YOU NEED TO MODIFY INLINES HERE, NOT IN FORMS


def add_study_fields_to_form(self, form, add_study=False):
    """Adds study, group, and restricted to a form

    Params:
    self -- the object in question
    form -- the form to be added to
    add_study -- boolean indicating whether to add the study to the model
    """
    study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])

    if add_study:
        form.instance.assay_run_id = study

    form.instance.group = study.group
    form.instance.restricted = study.restricted


# Removed User Index as it caused confusion
# Class-based views for indexes
# class UserIndex(OneGroupRequiredMixin, ListView):
#     """Displays all of the user's studies"""
#     context_object_name = 'user_index'
#     template_name = 'assays/index.html'
#
#     def get_context_data(self, request, **kwargs):
#         self.object_list = AssayRun.objects.filter(created_by=request.user).prefetch_related('created_by', 'group')
#
#         return super(UserIndex, self).get_context_data(**kwargs)
#
#     def get(self, request, **kwargs):
#         context = self.get_context_data(request, **kwargs)
#         self.queryset = self.object_list
#         context['title'] = request.user.first_name + "'s Studies"
#
#         return self.render_to_response(context)


def get_queryset_with_organ_model_map(queryset):
    """Takes a queryset and returns it with a organ model map"""
    setups = AssayChipSetup.objects.filter(
        organ_model__isnull=False
    ).prefetch_related(
        'assay_run_id',
        'device',
        'organ_model',
        # These two are deprecated
        'compound',
        'unit'
    )

    organ_model_map = {}

    for setup in setups:
        organ_model_map.setdefault(
            setup.assay_run_id_id, {}
        ).update(
            {
                setup.organ_model.model_name: True
            }
        )

    for study in queryset:
        study.organ_models = u',\n'.join(
            sorted(organ_model_map.get(study.id, {}).keys())
        )


def get_queryset_with_assay_map(queryset):
    """Takes a queryset and returns it with a assay map"""
    data_points = AssayChipRawData.objects.filter(
        assay_chip_id__in=queryset
    ).exclude(
        quality__contains=REPLACED_DATA_POINT_CODE
    ).prefetch_related(
        *CHIP_DATA_PREFETCH
    )

    assay_map = {}
    caution_flag_map = {}
    quality_map = {}

    for data_point in data_points:
        assay_map.setdefault(
            data_point.assay_chip_id_id, {}
        ).update(
            {
                data_point.assay_instance.target.short_name: True
            }
        )

        for flag in data_point.caution_flag:
            caution_flag_map.setdefault(data_point.assay_chip_id_id, {}
            ).update(
                {
                    flag: True
                }
            )

        if EXCLUDED_DATA_POINT_CODE in data_point.quality:
            quality_map.update(
                {
                    data_point.assay_chip_id_id: quality_map.setdefault(data_point.assay_chip_id_id, 0) + 1
                }
            )

    for readout in queryset:
        readout.assays = u', '.join(
            sorted(assay_map.get(readout.id, {}).keys())
        )
        readout.caution_flag = u''.join(
            sorted(caution_flag_map.get(readout.id, {}).keys())
        )
        readout.quality = quality_map.get(readout.id, '')

    return queryset


# "get" is perhaps a little incorrect here, as this acts more like a setter
def get_compound_instance_and_cell_strings_for_queryset(setups):
    """Modifies a queryset to contain strings for all of the compound instances and cells for each setup

    Params:
    setups - a queryset of AssayChipSetups
    """
    related_compounds = AssayCompoundInstance.objects.filter(
        chip_setup=setups
    ).prefetch_related(
        'compound_instance__compound',
        'compound_instance__supplier',
        'concentration_unit',
        # 'chip_setup'
    ).order_by('addition_time', 'compound_instance__compound__name')
    related_compounds_map = {}

    # NOTE THAT THIS MAKES A LIST OF STRINGS, NOT THE ACTUAL OBJECTS
    for compound in related_compounds:
        related_compounds_map.setdefault(compound.chip_setup_id, []).append(
            unicode(compound)
        )

    for setup in setups:
        setup.related_compounds_as_string = u'\n'.join(
            related_compounds_map.get(setup.id, ['-No Compound Treatments-'])
        )

    related_cells = AssayChipCells.objects.filter(
        # Idiosyncratic field name because schema needs to be revised
        assay_chip=setups
    ).prefetch_related(
        'cell_sample__cell_subtype',
        'cell_sample__cell_type__organ',
        'cell_sample__supplier',
        # 'cellsample_density_unit',
    ).order_by('cell_sample__cell_type__cell_type')
    related_cells_map = {}

    for cell in related_cells:
        related_cells_map.setdefault(cell.assay_chip_id, []).append(
            unicode(cell)
        )

    for setup in setups:
        setup.related_cells_as_string = u'\n'.join(
            related_cells_map.get(setup.id, ['-No Cells-'])
        )


def get_data_uploads(study=None, chip_readout=None, plate_readout=None):
    """Get data uploads for a study"""
    if study:
        data_uploads = AssayDataUpload.objects.filter(
            study=study
        ).prefetch_related(
            'created_by'
        ).distinct().order_by('created_on')

        data_points = AssayChipRawData.objects.filter(
            assay_chip_id__chip_setup__assay_run_id=study
        ).exclude(
            quality__contains=REPLACED_DATA_POINT_CODE
        ).prefetch_related(
            *CHIP_DATA_PREFETCH
        )

    elif chip_readout:
        data_uploads = AssayDataUpload.objects.filter(
            chip_readout=chip_readout
        ).prefetch_related(
            'created_by'
        ).distinct().order_by('created_on')

        data_points = AssayChipRawData.objects.filter(
            assay_chip_id=chip_readout
        ).exclude(
            quality__contains=REPLACED_DATA_POINT_CODE
        ).prefetch_related(
            *CHIP_DATA_PREFETCH
        )

    elif plate_readout:
        data_uploads = AssayDataUpload.objects.filter(
            plate_readout=plate_readout
        ).prefetch_related(
            'created_by'
        ).distinct().order_by('created_on')

        data_points = AssayChipRawData.objects.none()
    else:
        data_uploads = AssayDataUpload.objects.none()
        data_points = AssayChipRawData.objects.none()

    # Edge case for old data
    if data_points.exclude(data_upload=None).count() == 0 or plate_readout:
        for data_upload in data_uploads:
            data_upload.has_data = True

        return data_uploads

    data_upload_map = {}
    for data_point in data_points:
        data_upload_map.setdefault(
            data_point.data_upload_id, True
        )

    for data_upload in data_uploads:
        data_upload.has_data = data_upload_map.get(data_upload.id, '')

    return data_uploads


# IN THE FUTURE I SHOULD JUST HAVE DIRECT LINKS TO THE STUDY TO AVOID STUFF LIKE THIS
def get_queryset_with_number_of_data_points(queryset):
    """Add number of data points to each object in a nAssay Run querysey"""
    data_points = AssayChipRawData.objects.exclude(
        quality__contains=REPLACED_DATA_POINT_CODE
    ).prefetch_related(
        # *CHIP_DATA_PREFETCH
        'assay_chip_id__chip_setup__assay_run_id'
    )

    data_points_map = {}

    for data_point in data_points:
        current_value = data_points_map.setdefault(
            data_point.assay_chip_id.chip_setup.assay_run_id_id, 0
        )
        data_points_map.update({
            data_point.assay_chip_id.chip_setup.assay_run_id_id: current_value + 1
        })

    for study in queryset:
        study.data_points = data_points_map.get(study.id, 0)


def get_queryset_with_stakeholder_sign_off(queryset):
    """Add the stakeholder status to each object in an AssayRun Queryset

    The stakeholder_sign_off is True is there are no stakeholders that need to sign off
    """
    # A stakeholder is needed if the sign off is required and there is no pk for the individual signing off
    required_stakeholders_without_sign_off = AssayRunStakeholder.objects.filter(
        sign_off_required=True,
        signed_off_by_id=None
    )

    required_stakeholder_map = {}

    for stakeholder in required_stakeholders_without_sign_off:
        required_stakeholder_map.update({
            stakeholder.study_id: False
        })

    for study in queryset:
        study.stakeholder_sign_off = required_stakeholder_map.get(study.id, True)


def filter_queryset_for_viewership(self, queryset):
    """Peculiar way of filtering for viewership (Assay data bound to a study only)"""

    user_group_names = [
        group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()
    ]

    data_group_filter = {}
    access_group_filter = {}
    unrestricted_filter = {}
    unsigned_off_filter = {}
    stakeholder_group_filter = {}
    missing_stakeholder_filter = {}

    stakeholder_group_whitelist = list(set(
        AssayRunStakeholder.objects.filter(
            group__name__in=user_group_names
        ).values_list('study_id', flat=True)
    ))

    missing_stakeholder_blacklist = list(set(
        AssayRunStakeholder.objects.filter(
            signed_off_by_id=None,
            sign_off_required=True
        ).values_list('study_id', flat=True)
    ))

    current_type = str(self.model)

    if current_type == "<class 'assays.models.AssayRun'>":
        data_group_filter.update({
            'group__name__in': user_group_names
        })
        access_group_filter.update({
            'access_groups__name__in': user_group_names,
        })
        unrestricted_filter.update({
            'restricted': False
        })
        unsigned_off_filter.update({
            'signed_off_by': None
        })
        stakeholder_group_filter.update({
            'id__in': stakeholder_group_whitelist
        })
        missing_stakeholder_filter.update({
            'id__in': missing_stakeholder_blacklist
        })
    elif current_type == "<class 'assays.models.AssayChipSetup'>":
        data_group_filter.update({
            'assay_run_id__group__name__in': user_group_names
        })
        access_group_filter.update({
            'assay_run_id__access_groups__name__in': user_group_names,
        })
        unrestricted_filter.update({
            'assay_run_id__restricted': False
        })
        unsigned_off_filter.update({
            'assay_run_id__signed_off_by': None
        })
        stakeholder_group_filter.update({
            'assay_run_id_id__in': stakeholder_group_whitelist
        })
        missing_stakeholder_filter.update({
            'assay_run_id_id__in': missing_stakeholder_blacklist
        })
    elif current_type == "<class 'assays.models.AssayPlateSetup'>":
        data_group_filter.update({
            'assay_run_id__group__name__in': user_group_names
        })
        access_group_filter.update({
            'assay_run_id__access_groups__name__in': user_group_names
        })
        unrestricted_filter.update({
            'assay_run_id__restricted': False
        })
        unsigned_off_filter.update({
            'assay_run_id__signed_off_by': None
        })
        stakeholder_group_filter.update({
            'assay_run_id_id__in': stakeholder_group_whitelist
        })
        missing_stakeholder_filter.update({
            'assay_run_id_id__in': missing_stakeholder_blacklist
        })
    elif current_type == "<class 'assays.models.AssayChipReadout'>":
        data_group_filter.update({
            'chip_setup__assay_run_id__group__name__in': user_group_names
        })
        access_group_filter.update({
            'chip_setup__assay_run_id__access_groups__name__in': user_group_names
        })
        unrestricted_filter.update({
            'chip_setup__assay_run_id__restricted': False
        })
        unsigned_off_filter.update({
            'chip_setup__assay_run_id__signed_off_by': None
        })
        stakeholder_group_filter.update({
            'chip_setup__assay_run_id_id__in': stakeholder_group_whitelist
        })
        missing_stakeholder_filter.update({
            'chip_setup__assay_run_id_id__in': missing_stakeholder_blacklist
        })
    elif current_type == "<class 'assays.models.AssayPlateReadout'>":
        data_group_filter.update({
            'setup__assay_run_id__group__name__in': user_group_names
        })
        access_group_filter.update({
            'setup__assay_run_id__access_groups__name__in': user_group_names
        })
        unrestricted_filter.update({
            'setup__assay_run_id__restricted': False
        })
        unsigned_off_filter.update({
            'setup__assay_run_id__signed_off_by': None
        })
        stakeholder_group_filter.update({
            'setup__assay_run_id_id__in': stakeholder_group_whitelist
        })
        missing_stakeholder_filter.update({
            'setup__assay_run_id_id__in': missing_stakeholder_blacklist
        })
    elif current_type == "<class 'assays.models.AssayChipTestResult'>":
        data_group_filter.update({
            'chip_readout__chip_setup__assay_run_id__group__name__in': user_group_names
        })
        access_group_filter.update({
            'chip_readout__chip_setup__assay_run_id__access_groups__name__in': user_group_names
        })
        unrestricted_filter.update({
            'chip_readout__chip_setup__assay_run_id__restricted': False
        })
        unsigned_off_filter.update({
            'chip_readout__chip_setup__assay_run_id__signed_off_by': None
        })
        stakeholder_group_filter.update({
            'chip_readout__chip_setup__assay_run_id_id__in': stakeholder_group_whitelist
        })
        missing_stakeholder_filter.update({
            'chip_readout__chip_setup__assay_run_id_id__in': missing_stakeholder_blacklist
        })
    elif current_type == "<class 'assays.models.AssayPlateTestResult'>":
        data_group_filter.update({
            'readout__setup__assay_run_id__group__name__in': user_group_names
        })
        access_group_filter.update({
            'readout__setup__assay_run_id__access_groups__name__in': user_group_names
        })
        unrestricted_filter.update({
            'readout__setup__assay_run_id__restricted': False
        })
        unsigned_off_filter.update({
            'readout__setup__assay_run_id__signed_off_by': None
        })
        stakeholder_group_filter.update({
            'readout__setup__assay_run_id_id__in': stakeholder_group_whitelist
        })
        missing_stakeholder_filter.update({
            'readout__setup__assay_run_id_id__in': missing_stakeholder_blacklist
        })

    # Show if:
        # 1: Study has group matching user_group_names
        # 2: Study has Stakeholder group matching user_group_name AND is signed off on
        # 3: Study has access group matching user_group_names AND is signed off on AND all Stakeholders have signed off
        # 4: Study is unrestricted AND is signed off on AND all Stakeholders have signed off
    combined = queryset.filter(**data_group_filter) | \
    queryset.filter(**stakeholder_group_filter).exclude(**unsigned_off_filter) | \
    queryset.filter(**access_group_filter).exclude(**unsigned_off_filter).exclude(**missing_stakeholder_filter) | \
    queryset.filter(**unrestricted_filter).exclude(**unsigned_off_filter).exclude(**missing_stakeholder_filter)

    return combined.distinct()


class GroupIndex(OneGroupRequiredMixin, ListView):
    """Displays all of the studies linked to groups that the user is part of"""
    template_name = 'assays/assayrun_list.html'

    def get_queryset(self):
        queryset = AssayRun.objects.prefetch_related(
            'created_by',
            'group',
            'signed_off_by'
        )

        # Display to users with either editor or viewer group or if unrestricted
        group_names = list(set([group.name.replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]))

        # NOTE: Also excludes signed off studies
        queryset = queryset.filter(
            group__name__in=group_names,
            signed_off_by_id=None
        )

        get_queryset_with_organ_model_map(queryset)

        get_queryset_with_number_of_data_points(queryset)

        get_queryset_with_stakeholder_sign_off(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(GroupIndex, self).get_context_data(**kwargs)

        # Adds the word "editable" to the page
        context['editable'] = 'Editable '

        return context


def get_user_status_context(self, context):
    """Takes the view and context, adds user_is_group_admin, editor, and stakeholder editor to the context"""
    user_group_names = {group.name for group in self.request.user.groups.all()}

    context['user_is_group_admin'] = self.object.group.name + ADMIN_SUFFIX in user_group_names
    context['user_is_group_editor'] = self.object.group.name in user_group_names or context['user_is_group_admin']

    stakeholders = AssayRunStakeholder.objects.filter(
        study_id=self.object.id
    ).prefetch_related(
        'group',
        'study'
    )

    context['user_is_stakeholder_admin'] = False
    for stakeholder in stakeholders:
        if stakeholder.group.name + ADMIN_SUFFIX in user_group_names:
            context['user_is_stakeholder_admin'] = True
            break


class StudyIndex(StudyViewershipMixin, DetailView):
    """Show all chip and plate models associated with the given study"""
    model = AssayRun
    context_object_name = 'study_index'
    template_name = 'assays/study_index.html'

    # TODO OPTIMIZE DATABASE HITS
    def get_context_data(self, **kwargs):
        context = super(StudyIndex, self).get_context_data(**kwargs)

        # THIS CODE SHOULD NOT GET REPEATED AS OFTEN AS IT IS
        setups = AssayChipSetup.objects.filter(
            assay_run_id=self.object
        ).prefetch_related(
            'organ_model',
            'device',
            'compound',
            'unit',
            'created_by',
        )

        get_compound_instance_and_cell_strings_for_queryset(setups)

        context['setups'] = setups

        readouts = AssayChipReadout.objects.filter(
            chip_setup=context['setups']
        ).prefetch_related(
            'created_by',
            'chip_setup__compound',
            'chip_setup__unit'
        )

        get_queryset_with_assay_map(readouts)

        context['readouts'] = readouts

        context['results'] = AssayChipResult.objects.prefetch_related(
            'result_function',
            'result_type',
            'test_unit',
            'assay_result__chip_readout__chip_setup__unit',
            'assay_result__chip_readout__chip_setup__compound',
            'assay_result__created_by'
        ).filter(
            assay_result__chip_readout=context['readouts']
        )

        context['number_of_results'] = AssayChipTestResult.objects.filter(chip_readout=context['readouts']).count()

        # PLATES
        # Removed
        # context['plate_setups'] = AssayPlateSetup.objects.filter(
        #     assay_run_id=self.object
        # ).prefetch_related(
        #     'assay_layout',
        #     'created_by'
        # )
        # readouts = AssayPlateReadout.objects.filter(
        #     setup=context['plate_setups']
        # ).prefetch_related(
        #     'setup',
        #     'created_by'
        # )
        #
        # related_assays = AssayPlateReadoutAssay.objects.filter(
        #     readout_id__in=readouts
        # ).prefetch_related(
        #     'readout_id',
        #     'assay_id'
        # ).order_by(
        #     'assay_id__assay_short_name'
        # )
        # related_assays_map = {}
        #
        # for assay in related_assays:
        #     # start appending to a list keyed by the readout ID for all related images
        #     related_assays_map.setdefault(assay.readout_id_id, []).append(assay)
        #
        # for readout in readouts:
        #     # set an attribute on the readout that is the list created above
        #     readout.related_assays = related_assays_map.get(readout.id)
        #
        # context['plate_readouts'] = readouts
        #
        # context['plate_results'] = AssayPlateResult.objects.prefetch_related(
        #     'result_function',
        #     'result_type',
        #     'test_unit',
        #     'assay_result__readout__setup',
        #     'assay_result__created_by'
        # ).filter(
        #     assay_result__readout=context['plate_readouts']
        # )
        #
        # context['number_of_plate_results'] = AssayPlateTestResult.objects.filter(
        #     readout=context['plate_readouts']
        # ).count()

        context['detail'] = True

        # user_group_names = {group.name for group in self.request.user.groups.all()}
        #
        # context['user_is_group_admin'] = self.object.group.name + ADMIN_SUFFIX in user_group_names
        # context['user_is_group_editor'] = self.object.group.name in user_group_names or context['user_is_group_admin']
        #
        # stakeholders = AssayRunStakeholder.objects.filter(
        #     study_id=self.object.id
        # ).prefetch_related(
        #     'group',
        #     'study'
        # )
        #
        # context['user_is_stakeholder_admin'] = False
        # for stakeholder in stakeholders:
        #     if stakeholder.group.name + ADMIN_SUFFIX in user_group_names:
        #         context['user_is_stakeholder_admin'] = True
        #         break

        get_user_status_context(self, context)

        context['ready_for_sign_off_form'] = ReadyForSignOffForm()

        # Stakeholder status
        context['stakeholder_sign_off'] = AssayRunStakeholder.objects.filter(
            study=self.object,
            signed_off_by_id=None,
            sign_off_required=True
        ).count() == 0

        return context


# Class-based views for studies
class AssayRunList(LoginRequiredMixin, ListView):
    """A list of all studies"""
    model = AssayRun

    def get_queryset(self):
        queryset = AssayRun.objects.prefetch_related(
            'created_by',
            'group',
            'signed_off_by'
        )

        queryset = filter_queryset_for_viewership(self, queryset)

        # # Display to users with either editor or viewer group or if unrestricted
        # group_names = [group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]
        #
        # queryset = queryset.filter(
        #     restricted=False
        # ) | queryset.filter(
        #     group__name__in=group_names
        # )

        get_queryset_with_organ_model_map(queryset)

        get_queryset_with_number_of_data_points(queryset)

        get_queryset_with_stakeholder_sign_off(queryset)

        return queryset

StudySupportingDataFormset = inlineformset_factory(
    AssayRun,
    StudySupportingData,
    formset=StudySupportingDataInlineFormset,
    extra=1,
    exclude=[],
    widgets={
        'description': forms.Textarea(attrs={'rows': 3}),
    }
)

AssayInstanceFormset = inlineformset_factory(
    AssayRun,
    AssayInstance,
    formset=AssayInstanceInlineFormset,
    extra=1,
    exclude=[]
)


class AssayRunAdd(OneGroupRequiredMixin, CreateView):
    """Add a study"""
    template_name = 'assays/assayrun_add.html'
    form_class = AssayRunForm

    def get_context_data(self, **kwargs):
        context = super(AssayRunAdd, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['assay_instance_formset'] = AssayInstanceFormset(self.request.POST)
                context['supporting_data_formset'] = StudySupportingDataFormset(self.request.POST, self.request.FILES)
            else:
                context['assay_instance_formset'] = AssayInstanceFormset()
                context['supporting_data_formset'] = StudySupportingDataFormset()

        return context

    def get_form(self, form_class):
        # Get group selection possibilities
        groups = filter_groups(self.request.user)

        # If POST
        if self.request.method == 'POST':
            return form_class(groups, self.request.POST, self.request.FILES)
        # If GET
        else:
            return form_class(groups)

    # Test form validity
    def form_valid(self, form):
        assay_instance_formset = AssayInstanceFormset(
            self.request.POST,
            instance=form.instance
        )
        supporting_data_formset = StudySupportingDataFormset(
            self.request.POST,
            self.request.FILES,
            instance=form.instance
        )
        if form.is_valid() and assay_instance_formset.is_valid() and supporting_data_formset.is_valid():
            if not is_group_admin(self.request.user, form.cleaned_data['group'].name):
                if form.cleaned_data.get('signed_off', ''):
                    del form.cleaned_data['signed_off']
                form.cleaned_data['restricted'] = True

            save_forms_with_tracking(self, form, formset=[assay_instance_formset, supporting_data_formset], update=False)

            # Contact superusers
            # Superusers to contact
            superusers_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)

            # Magic strings are in poor taste, should use a template instead
            superuser_subject = 'Study Created: {0}'.format(self.object)
            superuser_message = render_to_string(
                'assays/email/superuser_study_created_alert.txt',
                {
                    'study': self.object
                }
            )

            for user_to_be_alerted in superusers_to_be_alerted:
                user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)

            return redirect(
                self.object.get_absolute_url()
            )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    assay_instance_formset=assay_instance_formset,
                    supporting_data_formset=supporting_data_formset
                )
            )


# TODO CHANGE
class AssayRunUpdate(ObjectGroupRequiredMixin, UpdateView):
    """Update the fields of a Study"""
    model = AssayRun
    template_name = 'assays/assayrun_add.html'
    form_class = AssayRunForm

    def get_context_data(self, **kwargs):
        context = super(AssayRunUpdate, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['assay_instance_formset'] = AssayInstanceFormset(
                    self.request.POST,
                    instance=self.object
                )
                context['supporting_data_formset'] = StudySupportingDataFormset(
                    self.request.POST,
                    self.request.FILES,
                    instance=self.object
                )
            else:
                context['assay_instance_formset'] = AssayInstanceFormset(instance=self.object)
                context['supporting_data_formset'] = StudySupportingDataFormset(instance=self.object)

        context['update'] = True

        return context

    def get_form(self, form_class):
        # Get group selection possibilities
        groups = filter_groups(self.request.user)

        # If POST
        if self.request.method == 'POST':
            return form_class(groups, self.request.POST, self.request.FILES, instance=self.get_object())
        # If GET
        else:
            return form_class(groups, instance=self.get_object())

    def form_valid(self, form):
        assay_instance_formset = AssayInstanceFormset(
            self.request.POST,
            instance=form.instance
        )
        supporting_data_formset = StudySupportingDataFormset(
            self.request.POST,
            self.request.FILES,
            instance=form.instance
        )

        # Get the original Sign Off data (may be None)
        # original_sign_off_date = self.object.signed_off_date

        if form.is_valid() and assay_instance_formset.is_valid() and supporting_data_formset.is_valid():
            # These shouldn't be in the form to begin with!
            # if not is_group_admin(self.request.user, self.object.group.name):
            #     if form.cleaned_data.get('signed_off', ''):
            #         del form.cleaned_data['signed_off']
            #     form.cleaned_data['restricted'] = self.object.restricted

            # send_alert = not form.instance.signed_off_by and form.cleaned_data.get('signed_off', '')

            save_forms_with_tracking(self, form, formset=[assay_instance_formset, supporting_data_formset], update=True)

            # if send_alert:
            #     # Magic strings are in poor taste, should use a template instead
            #     superuser_subject = 'Study Sign Off Detected: {0}'.format(self.object)
            #     superuser_message = render_to_string(
            #         'assays/email/superuser_initial_sign_off_alert.txt',
            #         {
            #             'study': self.object
            #         }
            #     )
            #
            #     superusers_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)
            #
            #     for user_to_be_alerted in superusers_to_be_alerted:
            #         user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)
            #
            #     viewer_subject = 'Study {0} Now Available for Viewing'.format(self.object)
            #
            #     access_group_names = {group.name: group.id for group in self.object.access_groups.all()}
            #     matching_groups = list(set([
            #         group.id for group in Group.objects.all() if group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, '') in access_group_names
            #     ]))
            #     viewers_to_be_alerted = User.objects.filter(groups__id__in=matching_groups, is_active=True).distinct()
            #
            #     for user_to_be_alerted in viewers_to_be_alerted:
            #         viewer_message = render_to_string(
            #             'assays/email/viewer_alert_email.txt',
            #             {
            #                 'user': user_to_be_alerted,
            #                 'study': self.object
            #             }
            #         )
            #
            #         user_to_be_alerted.email_user(
            #             viewer_subject,
            #             viewer_message,
            #             DEFAULT_FROM_EMAIL
            #         )

            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                assay_instance_formset=assay_instance_formset,
                supporting_data_formset=supporting_data_formset
            ))


# DEPRECATED
class AssayRunUpdateAccess(SuperuserRequiredMixin, UpdateView):
    """Update the fields of a Study"""
    model = AssayRun
    template_name = 'assays/assayrun_access.html'
    form_class = AssayRunAccessForm

    def get_context_data(self, **kwargs):
        context = super(AssayRunUpdateAccess, self).get_context_data(**kwargs)

        context['update'] = True

        return context

    def form_valid(self, form):
        if form.is_valid():
            if self.request.user.is_superuser:
                previous_access_groups = {group.name:group.id for group in form.instance.access_groups.all()}

                save_forms_with_tracking(self, form, update=True)

                if self.object.signed_off_by:
                    viewer_subject = 'Study {0} Now Available for Viewing'.format(self.object)

                    access_group_names = {group.name: group.id for group in self.object.access_groups.all() if group.name not in previous_access_groups}

                    matching_groups = list(set([
                        group.id for group in Group.objects.all() if
                        group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, '') in access_group_names
                    ]))
                    exclude_groups = list(set([
                        group.id for group in Group.objects.all() if
                        group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, '') in previous_access_groups
                    ]))
                    viewers_to_be_alerted = User.objects.filter(
                        groups__id__in=matching_groups,
                        is_active=True
                    ).exclude(
                        groups__id__in=exclude_groups
                    ).distinct()

                    for user_to_be_alerted in viewers_to_be_alerted:
                        viewer_message = render_to_string(
                            'assays/viewer_alert.txt',
                            {
                                'user': user_to_be_alerted,
                                'study': self.object
                            }
                        )

                        user_to_be_alerted.email_user(
                            viewer_subject,
                            viewer_message,
                            DEFAULT_FROM_EMAIL
                        )

            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AssayRunSignOff(UpdateView):
    """Perform Sign Offs as a group adming or stake holder admin"""
    model = AssayRun
    template_name = 'assays/assayrun_sign_off.html'
    form_class = AssayRunSignOffForm

    # Please note the unique dispatch!
    # TODO TODO TODO REVIEW
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        study = self.get_object()
        user_group_names = self.request.user.groups.all().values_list('name', flat=True)

        can_view_sign_off = study.group.name + ADMIN_SUFFIX in user_group_names

        # Check if user is a stakeholder admin ONLY IF SIGNED OFF
        if study.signed_off_by:
            stakeholders = AssayRunStakeholder.objects.filter(
                study=study
            ).prefetch_related(
                'study',
                'group',
                'signed_off_by'
            )
            stakeholder_group_names = {name + ADMIN_SUFFIX: True for name in stakeholders.values_list('group__name', flat=True)}
            for group_name in user_group_names:
                if group_name in stakeholder_group_names:
                    can_view_sign_off = True
                    # Only iterate as many times as is needed
                    break

        if can_view_sign_off:
            return super(AssayRunSignOff, self).dispatch(*args, **kwargs)
        else:
            return PermissionDenied(self.request, 'You must be a qualified group administrator to view this page')

    def get_context_data(self, **kwargs):
        context = super(AssayRunSignOff, self).get_context_data(**kwargs)

        if self.request.POST:
            context.update({
                'stakeholder_formset': assay_run_stakeholder_sign_off_formset_factory(
                    self.request.POST,
                    instance=self.object,
                    user=self.request.user
                )
            })
        else:
            context.update({
                'stakeholder_formset': assay_run_stakeholder_sign_off_formset_factory(
                    instance=self.object,
                    user=self.request.user
                )
            })

        context.update({
            'update': True
        })

        return context

    def form_valid(self, form):
        stakeholder_formset = assay_run_stakeholder_sign_off_formset_factory(
            self.request.POST,
            instance=form.instance,
            user=self.request.user
        )

        if form.is_valid() and stakeholder_formset.is_valid():
            # Local datetime
            tz = pytz.timezone('US/Eastern')
            datetime_now_local = datetime.now(tz)
            thirty_days_from_date = datetime_now_local + timedelta(days=30)

            send_initial_sign_off_alert = False
            initial_number_of_required_sign_offs = AssayRunStakeholder.objects.filter(
                study=self.object,
                signed_off_by_id=None,
                sign_off_required=True
            ).count()

            # Only allow if necessary
            if is_group_admin(self.request.user, self.object.group.name) and not self.object.signed_off_by:
                send_initial_sign_off_alert = not form.instance.signed_off_by and form.cleaned_data.get('signed_off', '')
                save_forms_with_tracking(self, form, update=True)

            # save_forms_with_tracking(self, form, formset=[stakeholder_formset], update=True)

            if stakeholder_formset.has_changed():
                save_forms_with_tracking(self, None, formset=[stakeholder_formset], update=True)

            current_number_of_required_sign_offs = AssayRunStakeholder.objects.filter(
                study=self.object,
                signed_off_by_id=None,
                sign_off_required=True
            ).count()

            send_stakeholder_sign_off_alert = current_number_of_required_sign_offs < initial_number_of_required_sign_offs
            send_viewer_alert = current_number_of_required_sign_offs == 0 and self.object.signed_off_by

            viewer_subject = 'Study {0} Now Available for Viewing'.format(self.object)
            # TODO TODO TODO TODO
            stakeholder_admin_subject = 'Approval for Release Requested: {0}'.format(self.object)

            stakeholder_viewer_groups = {}
            stakeholder_admin_groups = {}

            stakeholder_admins_to_be_alerted = []
            stakeholder_viewers_to_be_alerted = []

            if send_initial_sign_off_alert:
                # TODO TODO TODO TODO ALERT STAKEHOLDER ADMINS
                stakeholder_admin_groups = {
                    group + ADMIN_SUFFIX: True for group in
                    AssayRunStakeholder.objects.filter(
                        study=self.object, sign_off_required=True
                    ).prefetch_related('group').values_list('group__name', flat=True)
                }

                stakeholder_admins_to_be_alerted = User.objects.filter(
                    groups__name__in=stakeholder_admin_groups, is_active=True
                ).distinct()

                for user_to_be_alerted in stakeholder_admins_to_be_alerted:
                    try:
                        stakeholder_admin_message = render_to_string(
                            'assays/email/tctc_stakeholder_email.txt',
                            {
                                'user': user_to_be_alerted,
                                'study': self.object,
                                'thirty_days_from_date': thirty_days_from_date
                            }
                        )
                    except TemplateDoesNotExist:
                        stakeholder_admin_message = render_to_string(
                            'assays/email/stakeholder_sign_off_request.txt',
                            {
                                'user': user_to_be_alerted,
                                'study': self.object
                            }
                        )

                    user_to_be_alerted.email_user(
                        stakeholder_admin_subject,
                        stakeholder_admin_message,
                        DEFAULT_FROM_EMAIL
                    )

                # TODO TODO TODO TODO ALERT STAKEHOLDER VIEWERS
                stakeholder_viewer_groups = {
                    group: True for group in
                    AssayRunStakeholder.objects.filter(
                        study=self.object
                    ).prefetch_related('group').values_list('group__name', flat=True)
                }
                initial_groups = stakeholder_viewer_groups.keys()

                for group in initial_groups:
                    stakeholder_viewer_groups.update({
                        # group + ADMIN_SUFFIX: True,
                        group + VIEWER_SUFFIX: True
                    })

                # BE SURE THIS IS MATCHED BELOW
                stakeholder_viewers_to_be_alerted = User.objects.filter(
                    groups__name__in=stakeholder_viewer_groups, is_active=True
                ).exclude(
                    id__in=stakeholder_admins_to_be_alerted
                ).distinct()

                for user_to_be_alerted in stakeholder_viewers_to_be_alerted:
                    # TODO TODO TODO WHAT DO WE CALL THE PROCESS OF SIGN OFF ACKNOWLEDGEMENT?!
                    viewer_message = render_to_string(
                        'assays/email/viewer_alert.txt',
                        {
                            'user': user_to_be_alerted,
                            'study': self.object
                        }
                    )

                    user_to_be_alerted.email_user(
                        viewer_subject,
                        viewer_message,
                        DEFAULT_FROM_EMAIL
                    )

            if send_viewer_alert:
                access_group_names = {group.name: group.id for group in self.object.access_groups.all()}
                matching_groups = list(set([
                    group.id for group in Group.objects.all() if
                    group.name.replace(ADMIN_SUFFIX, '').replace(VIEWER_SUFFIX, '') in access_group_names
                ]))
                # Just in case, exclude stakeholders to prevent double messages
                viewers_to_be_alerted = User.objects.filter(
                    groups__id__in=matching_groups, is_active=True
                ).exclude(
                    id__in=stakeholder_admins_to_be_alerted
                ).exclude(
                    id__in=stakeholder_viewers_to_be_alerted
                ).distinct()
                # Update viewer groups to include admins
                stakeholder_viewer_groups.update(stakeholder_admin_groups)
                # if stakeholder_viewer_groups or stakeholder_admin_groups:
                #     viewers_to_be_alerted.exclude(
                #         groups__name__in=stakeholder_viewer_groups
                #     ).exclude(
                #         group__name__in=stakeholder_admin_groups
                #     )

                for user_to_be_alerted in viewers_to_be_alerted:
                    viewer_message = render_to_string(
                        'assays/email/viewer_alert.txt',
                        {
                            'user': user_to_be_alerted,
                            'study': self.object
                        }
                    )

                    user_to_be_alerted.email_user(
                        viewer_subject,
                        viewer_message,
                        DEFAULT_FROM_EMAIL
                    )

            # Superusers to contact
            superusers_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)

            if send_initial_sign_off_alert:
                # Magic strings are in poor taste, should use a template instead
                superuser_subject = 'Study Sign Off Detected: {0}'.format(self.object)
                superuser_message = render_to_string(
                    'assays/email/superuser_initial_sign_off_alert.txt',
                    {
                        'study': self.object,
                        'stakeholders': AssayRunStakeholder.objects.filter(study=self.object).order_by('-signed_off_date')
                    }
                )

                for user_to_be_alerted in superusers_to_be_alerted:
                    user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)

            if send_stakeholder_sign_off_alert:
                # Magic strings are in poor taste, should use a template instead
                # superuser_subject = 'Stakeholder Acknowledgement Detected: {0}'.format(self.object)
                superuser_subject = 'Stakeholder Approval Detected: {0}'.format(self.object)
                superuser_message = render_to_string(
                    'assays/email/superuser_stakeholder_alert.txt',
                    {
                        'study': self.object,
                        'stakeholders': AssayRunStakeholder.objects.filter(study=self.object).order_by('-signed_off_date')
                    }
                )

                for user_to_be_alerted in superusers_to_be_alerted:
                    user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)

            if send_viewer_alert:
                # Magic strings are in poor taste, should use a template instead
                superuser_subject = 'Study Released to Next Level: {0}'.format(self.object)
                superuser_message = render_to_string(
                    'assays/email/superuser_viewer_release_alert.txt',
                    {
                        'study': self.object
                    }
                )

                for user_to_be_alerted in superusers_to_be_alerted:
                    user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)

            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                stakeholder_formset=stakeholder_formset
            ))


def compare_cells(current_model, current_filter, setups):
    """Compare cells to discern setups use the same sort and amount of cells"""
    cells = {}

    for setup in setups:
        cells.update(
            {
                setup: sorted(current_model.objects.filter(**{current_filter: setup.id}).values_list(
                    'cell_sample',
                    'cell_biosensor',
                    'cellsample_density',
                    'cellsample_density_unit',
                    'cell_passage'))
            }
        )

    sameness = {setup: {} for setup in setups}
    max_same = 0
    best_setup = setups[0]

    for setup_1 in setups:
        same = 0
        for setup_2 in setups:
            if setup_1 != setup_2:
                if cells.get(setup_1) == cells.get(setup_2):
                    sameness.get(setup_1).update({str(setup_2): True})
                    same += 1
                else:
                    sameness.get(setup_1).update({str(setup_2): False})
        if same > max_same:
            max_same = same
            best_setup = setup_1

    return (best_setup, sameness.get(best_setup))


class AssayRunSummary(StudyViewershipMixin, DetailView):
    """Displays information for a given study

    Currently only shows data for chip readouts and chip/plate setups
    """
    model = AssayRun
    template_name = 'assays/assayrun_summary.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        setups = AssayChipSetup.objects.filter(
            assay_run_id=self.object
        ).prefetch_related(
            'organ_model',
            'device',
            'compound',
            'unit',
            'created_by',
        )

        get_compound_instance_and_cell_strings_for_queryset(setups)

        context['setups'] = setups

        # TODO THIS SAME BUSINESS NEEDS TO BE REFACTORED
        # # For chips
        # indicative = None
        # sameness = {}
        #
        # if len(context['setups']) > 1:
        #     results = compare_cells(AssayChipCells, 'assay_chip', context['setups'])
        #     indicative = results[0]
        #     sameness = results[1]
        # elif len(context['setups']) == 1:
        #     indicative = context['setups'][0]
        #
        # context['sameness'] = sameness
        # context['indicative'] = indicative
        #
        # # For plates
        # context['plate_setups'] = AssayPlateSetup.objects.filter(
        #     assay_run_id=self.object
        # ).prefetch_related(
        #     'assay_run_id',
        #     'assay_layout',
        #     'created_by'
        # )
        #
        # indicative = None
        # sameness = {}
        #
        # if len(context['plate_setups']) > 1:
        #     results = compare_cells(AssayPlateCells, 'assay_plate', context['plate_setups'])
        #     indicative = results[0]
        #     sameness = results[1]
        # elif len(context['plate_setups']) == 1:
        #     indicative = context['plate_setups'][0]
        #
        # context['plate_sameness'] = sameness
        # context['plate_indicative'] = indicative

        # chip_readouts = AssayChipReadout.objects.filter(
        #     chip_setup__assay_run_id=self.object
        # ).prefetch_related('chip_setup')
        # plate_readouts = AssayPlateReadout.objects.filter(
        #     setup__assay_run_id=self.object
        # ).prefetch_related('setup')

        # data_uploads = AssayDataUpload.objects.filter(
        #     study=self.object
        # ).prefetch_related(
        #     'created_by'
        # ).distinct().order_by('created_on')

        context['data_uploads'] = get_data_uploads(study=self.object)

        context['assay_instances'] = AssayInstance.objects.filter(
            study=self.object
        ).prefetch_related(
            'target',
            'method',
            'unit'
        ).order_by(
            'target__name',
            'method__name',
            'unit__unit'
        )

        get_user_status_context(self, context)

        return self.render_to_response(context)


class AssayRunDelete(DeletionMixin, DeleteView):
    """Delete a Setup"""
    model = AssayRun
    template_name = 'assays/assayrun_delete.html'
    success_url = '/assays/editable_studies/'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data()

        context['chip_setups'] = AssayChipSetup.objects.filter(
            assay_run_id=self.object.id
        ).prefetch_related(
            'compound',
            'unit'
        )
        context['chip_readouts'] = AssayChipReadout.objects.filter(chip_setup=context['chip_setups'])
        context['chip_results'] = AssayChipTestResult.objects.filter(chip_readout=context['chip_readouts'])

        context['plate_setups'] = AssayPlateSetup.objects.filter(assay_run_id=self.object)
        context['plate_readouts'] = AssayPlateReadout.objects.filter(setup=context['plate_setups'])
        context['plate_results'] = AssayPlateTestResult.objects.filter(readout=context['plate_readouts'])

        return self.render_to_response(context)


# Class based view for chip setups
class AssayChipSetupList(LoginRequiredMixin, ListView):
    """Displays a list of Chip Setups"""
    model = AssayChipSetup

    def get_queryset(self):
        queryset = AssayChipSetup.objects.prefetch_related(
            'assay_run_id',
            'device',
            'organ_model',
            'compound',
            'unit',
            'created_by',
            'group',
            'signed_off_by'
        )

        queryset = filter_queryset_for_viewership(self, queryset)

        # Display to users with either editor or viewer group or if unrestricted
        # group_names = [group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]
        # queryset = queryset.filter(
        #     restricted=False
        # ) | queryset.filter(
        #     group__name__in=group_names
        # )

        get_compound_instance_and_cell_strings_for_queryset(queryset)

        return queryset


AssayCompoundInstanceFormset = inlineformset_factory(
    AssayChipSetup,
    AssayCompoundInstance,
    formset=AssayCompoundInstanceInlineFormset,
    extra=1,
    exclude=[],
)

AssayChipCellsFormset = inlineformset_factory(
    AssayChipSetup,
    AssayChipCells,
    formset=AssayChipCellsInlineFormset,
    extra=1,
    exclude=[],
    widgets={
        'cellsample_density': forms.NumberInput(attrs={'style': 'width:100px;'}),
        'cell_passage': forms.TextInput(attrs={'size': 5})
    }
)


def get_cell_samples(user, chip_setup=None, plate_setup=None):
    """Returns the cell samples to be listed in setup views

    Params:
    user - the user in the request
    chip_setup - the chip setup in question
    plate_setup - the plate setup in question
    """
    user_groups = user.groups.values_list('id', flat=True)

    # Get cell samples with group
    cellsamples_with_group = CellSample.objects.filter(
        group__in=user_groups
    ).prefetch_related(
        'cell_type__organ',
        'supplier',
        'cell_subtype__cell_type'
    )

    current_cell_samples = CellSample.objects.none()

    if chip_setup:
        # Get the currently used cell samples
        current_cell_samples = CellSample.objects.filter(
            assaychipcells__assay_chip=chip_setup
        ).prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )
    elif plate_setup:
        # Get the currently used cell samples
        current_cell_samples = CellSample.objects.filter(
            assayplatecells__assay_plate=plate_setup
        ).prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

    combined_query = cellsamples_with_group | current_cell_samples
    combined_query = combined_query.order_by('-receipt_date').distinct()

    # Return the combination of the querysets
    return combined_query


# Cloning was recently refactored
class AssayChipSetupAdd(StudyGroupRequiredMixin, CreateView):
    """Add a Chip Setup (with inline for Chip Cells)"""
    model = AssayChipSetup
    template_name = 'assays/assaychipsetup_add.html'
    # May want to define form with initial here
    form_class = AssayChipSetupForm

    # Specify that cloning is permitted
    cloning_permitted = True

    def get_form(self, form_class):
        if self.request.method == 'POST':
            form = form_class(self.request.POST)
        elif self.request.GET.get('clone', ''):
            pk = int(self.request.GET.get('clone', ''))
            clone = get_object_or_404(AssayChipSetup, pk=pk)
            form = form_class(instance=clone)
        else:
            form = form_class()

        add_study_fields_to_form(self, form, add_study=True)

        return form

    def get_context_data(self, **kwargs):
        cellsamples = get_cell_samples(self.request.user)

        context = super(AssayChipSetupAdd, self).get_context_data(**kwargs)

        if 'cell_formset' not in context or 'compound_formset' not in context:
            if self.request.POST:
                context['cell_formset'] = AssayChipCellsFormset(self.request.POST)
                context['compound_formset'] = AssayCompoundInstanceFormset(self.request.POST)
            elif self.request.GET.get('clone', ''):
                pk = int(self.request.GET.get('clone', ''))
                clone = get_object_or_404(AssayChipSetup, pk=pk)
                context['cell_formset'] = AssayChipCellsFormset(instance=clone)
                context['compound_formset'] = AssayCompoundInstanceFormset(instance=clone)
            else:
                context['cell_formset'] = AssayChipCellsFormset()
                context['compound_formset'] = AssayCompoundInstanceFormset()

        # Cellsamples will always be the same
        context['cellsamples'] = cellsamples

        return context

    def form_valid(self, form):
        cell_formset = AssayChipCellsFormset(self.request.POST, instance=form.instance, save_as_new=True)
        compound_formset = AssayCompoundInstanceFormset(self.request.POST, instance=form.instance, save_as_new=True)
        # get user via self.request.user
        if form.is_valid() and cell_formset.is_valid() and compound_formset.is_valid():
            data = form.cleaned_data
            # Note that both formsets are passed
            save_forms_with_tracking(self, form, formset=[cell_formset, compound_formset], update=False)
            if data['another']:
                form = self.form_class(
                    instance=self.object,
                    initial={'success': True}
                )
                return self.render_to_response(self.get_context_data(form=form))
            else:
                return redirect(self.object.get_post_submission_url())
        else:
            # Note that both formsets are passed
            return self.render_to_response(self.get_context_data(
                form=form,
                cell_formset=cell_formset,
                compound_formset=compound_formset
            ))


class AssayChipSetupDetail(StudyGroupRequiredMixin, DetailView):
    """Details for a Chip Setup"""
    model = AssayChipSetup
    detail = True

    def get_context_data(self, **kwargs):
        context = super(AssayChipSetupDetail, self).get_context_data(**kwargs)

        compounds = AssayCompoundInstance.objects.filter(
            chip_setup=self.object
        ).prefetch_related(
            'compound_instance__compound',
            'concentration_unit',
            'compound_instance__supplier'
        ).order_by('addition_time', 'compound_instance__compound__name')

        # for compound in compounds:
        #     split_addition_time = get_split_times(compound.addition_time)
        #     split_duration = get_split_times(compound.duration)
        #
        #     for unit in TIME_CONVERSIONS.keys():
        #         compound.__dict__.update({
        #             'addition_time_' + unit: split_addition_time.get(unit),
        #             'duration_' + unit: split_duration.get(unit)
        #         })

        context['compounds'] = compounds

        return context


# TODO IMPROVE METHOD FOR CLONING
class AssayChipSetupUpdate(StudyGroupRequiredMixin, UpdateView):
    """Update a Chip Setup and Chip Cells inline"""
    model = AssayChipSetup
    template_name = 'assays/assaychipsetup_add.html'
    form_class = AssayChipSetupForm

    def get_context_data(self, **kwargs):
        cellsamples = get_cell_samples(self.request.user, chip_setup=self.object)

        context = super(AssayChipSetupUpdate, self).get_context_data(**kwargs)

        if 'cell_formset' not in context or 'compound_formset' not in context:
            if self.request.POST:
                context['cell_formset'] = AssayChipCellsFormset(self.request.POST, instance=self.object)
                context['compound_formset'] = AssayCompoundInstanceFormset(self.request.POST, instance=self.object)
            else:
                context['cell_formset'] = AssayChipCellsFormset(instance=self.object)
                context['compound_formset'] = AssayCompoundInstanceFormset(instance=self.object)

        context['cellsamples'] = cellsamples
        context['update'] = True

        return context

    def form_valid(self, form):
        cell_formset = AssayChipCellsFormset(self.request.POST, instance=form.instance)
        compound_formset = AssayCompoundInstanceFormset(self.request.POST, instance=form.instance)

        if form.is_valid() and cell_formset.is_valid() and compound_formset.is_valid():
            # Notice that both formsets are added
            save_forms_with_tracking(self, form, formset=[cell_formset, compound_formset], update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                cell_formset=cell_formset,
                compound_formset=compound_formset
            ))


class AssayChipSetupDelete(DeletionMixin, DeleteView):
    """Delete a Chip Setup and Chip Cells"""
    model = AssayChipSetup
    template_name = 'assays/assaychipsetup_delete.html'

    def get_success_url(self):
        return '/assays/' + str(self.object.assay_run_id_id)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data()

        context['readouts'] = AssayChipReadout.objects.filter(chip_setup=self.object)
        context['results'] = AssayChipTestResult.objects.filter(chip_readout=context['readouts'])

        return self.render_to_response(context)


# Class based views for readouts
class AssayChipReadoutList(LoginRequiredMixin, ListView):
    """Displays a list of Chip Readouts"""
    model = AssayChipReadout

    def get_queryset(self):
        queryset = AssayChipReadout.objects.prefetch_related(
            'chip_setup__assay_run_id',
            'chip_setup__compound',
            'chip_setup__unit',
            'created_by',
            'group',
            'signed_off_by'
        )

        queryset = filter_queryset_for_viewership(self, queryset)

        # Display to users with either editor or viewer group or if unrestricted
        # group_names = [group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]
        # queryset = queryset.filter(
        #     restricted=False
        # ) | queryset.filter(
        #     group__name__in=group_names
        # )

        get_queryset_with_assay_map(queryset)

        return queryset


ACRAFormSet = inlineformset_factory(
    AssayChipReadout,
    AssayChipReadoutAssay,
    formset=AssayChipReadoutInlineFormset,
    extra=1,
    exclude=[],
)


class AssayChipReadoutAdd(StudyGroupRequiredMixin, CreateView):
    """Add a Chip Readout with inline for Assay Chip Readout Assays"""
    template_name = 'assays/assaychipreadout_add.html'
    form_class = AssayChipReadoutForm
    model = AssayChipReadout

    # Specify that cloning is permitted
    cloning_permitted = True

    def get_form(self, form_class):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        current = None
        if self.request.method == 'POST':
            form = form_class(study, current, self.request.POST, self.request.FILES, request=self.request)
        elif self.request.GET.get('clone', ''):
            pk = int(self.request.GET.get('clone', ''))
            clone = get_object_or_404(AssayChipReadout, pk=pk)
            form = form_class(
                study,
                current,
                instance=clone,
                initial={'file': None}
            )
        else:
            form = form_class(study, current)

        add_study_fields_to_form(self, form)

        return form

    def get_context_data(self, **kwargs):
        context = super(AssayChipReadoutAdd, self).get_context_data(**kwargs)
        # if 'formset' not in context:
        #     if self.request.POST:
        #         context['formset'] = ACRAFormSet(self.request.POST)
        #     elif self.request.GET.get('clone', ''):
        #         pk = int(self.request.GET.get('clone', ''))
        #         clone = get_object_or_404(AssayChipReadout, pk=pk)
        #         context['formset'] = ACRAFormSet(instance=clone)
        #     else:
        #         context['formset'] = ACRAFormSet()

        context['study'] = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])

        return context

    def form_valid(self, form):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        # formset = ACRAFormSet(self.request.POST, instance=form.instance, save_as_new=True)
        # get user via self.request.user
        # if form.is_valid() and formset.is_valid():
        if form.is_valid():
            data = form.cleaned_data
            # Get headers
            # headers = int(data.get('headers'))
            overwrite_option = data.get('overwrite_option')

            # save_forms_with_tracking(self, form, formset=formset, update=False)
            save_forms_with_tracking(self, form, update=False)

            if self.request.FILES:
                study_id = str(self.kwargs['study_id'])
                parse_file_and_save(
                    self.object.file, self.object.modified_by, study_id, overwrite_option, 'Chip', form=form, readout=self.object
                )
                # DEPRECATED
                # parse_chip_csv(self.object, current_file, headers, overwrite_option, form)
            if data['another']:
                form = self.form_class(
                    study,
                    None,
                    instance=self.object,
                    initial={'file': None, 'success': True}
                )
                return self.render_to_response(self.get_context_data(form=form))
            else:
                return redirect(self.object.get_post_submission_url())
        else:
            # return self.render_to_response(self.get_context_data(form=form, formset=formset))
            return self.render_to_response(self.get_context_data(form=form))

    # Redirect when there are no available setups
    def render_to_response(self, context):
        # TODO REFACTOR
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        exclude_list = AssayChipReadout.objects.filter(chip_setup__isnull=False).values_list('chip_setup', flat=True)
        setups = AssayChipSetup.objects.filter(
            assay_run_id=study
        ).prefetch_related(
            'assay_run_id',
            'device',
            'compound',
            'unit',
            'created_by'
        ).exclude(
            id__in=list(set(exclude_list))
        )
        if not setups:
            return redirect('/assays/' + str(study.id))

        return super(AssayChipReadoutAdd, self).render_to_response(context)


class AssayChipReadoutDetail(StudyGroupRequiredMixin, DetailView):
    """Detail for Chip Readout"""
    model = AssayChipReadout
    detail = True

    def get_context_data(self, **kwargs):
        context = super(AssayChipReadoutDetail, self).get_context_data(**kwargs)

        # data_uploads = AssayDataUpload.objects.filter(
        #     chip_readout=self.object
        # ).prefetch_related(
        #     'created_by'
        # ).distinct().order_by('created_on')

        context['data_uploads'] = get_data_uploads(chip_readout=self.object)

        return context


class AssayChipReadoutUpdate(StudyGroupRequiredMixin, UpdateView):
    """Update Assay Chip Readout and Assay Chip Readout Assays"""
    model = AssayChipReadout
    template_name = 'assays/assaychipreadout_add.html'
    form_class = AssayChipReadoutForm

    def get_form(self, form_class):
        study = self.object.chip_setup.assay_run_id
        current = self.object.chip_setup_id

        # If POST
        if self.request.method == 'POST':
            return form_class(study, current, self.request.POST, self.request.FILES, request=self.request, instance=self.get_object())
        # If GET
        else:
            return form_class(study, current, instance=self.get_object())

    def get_context_data(self, **kwargs):
        context = super(AssayChipReadoutUpdate, self).get_context_data(**kwargs)
        # if 'formset' not in context:
        #     if self.request.POST:
        #         context['formset'] = ACRAFormSet(self.request.POST, instance=self.object)
        #     else:
        #         context['formset'] = ACRAFormSet(instance=self.object)

        # data_uploads = AssayDataUpload.objects.filter(
        #     chip_readout=self.object
        # ).prefetch_related(
        #     'created_by'
        # ).distinct().order_by('created_on')

        context['data_uploads'] = get_data_uploads(chip_readout=self.object)

        context['study'] = self.object.chip_setup.assay_run_id

        context['update'] = True

        return context

    def form_valid(self, form):
        # formset = ACRAFormSet(self.request.POST, instance=form.instance)

        # if form.is_valid() and formset.is_valid():
        if form.is_valid():
            data = form.cleaned_data
            # Get headers
            # headers = int(data.get('headers'))
            overwrite_option = data.get('overwrite_option')

            # save_forms_with_tracking(self, form, formset=formset, update=True)
            save_forms_with_tracking(self, form, update=True)

            # Clear data if clear is checked
            if self.request.POST.get('file-clear', ''):
                AssayChipRawData.objects.filter(assay_chip_id=self.object).delete()
            # Save file if it exists
            elif self.request.FILES:
                study_id = str(self.object.chip_setup.assay_run_id.id)
                parse_file_and_save(
                    self.object.file, self.object.modified_by, study_id, overwrite_option, 'Chip', form=form, readout=self.object
                )
                # Deprecated
                # parse_chip_csv(self.object, file, headers, overwrite_option, form)
            # If no file, try to update the qc_status
            else:
                modify_qc_status_chip(self.object, form)
            # Otherwise do nothing (the file remained the same)
            return redirect(self.object.get_post_submission_url())
        else:
            # return self.render_to_response(self.get_context_data(form=form, formset=formset))
            return self.render_to_response(self.get_context_data(form=form))


class AssayChipReadoutDelete(DeletionMixin, DeleteView):
    """Delete Assay Chip Readout"""
    model = AssayChipReadout
    template_name = 'assays/assaychipreadout_delete.html'

    def get_success_url(self):
        return '/assays/' + str(self.object.chip_setup.assay_run_id_id)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data()

        context['results'] = AssayChipTestResult.objects.filter(chip_readout=self.object)

        return self.render_to_response(context)


# Class-based views for test results
class AssayChipTestResultList(LoginRequiredMixin, ListView):
    """Displays a list of Chip Test Results"""
    # model = AssayChipTestResult
    template_name = 'assays/assaychiptestresult_list.html'

    def get_queryset(self):
        queryset = AssayChipResult.objects.prefetch_related(
            'assay_result__chip_readout__chip_setup',
            'assay_result__chip_readout__chip_setup__compound',
            'assay_result__chip_readout__chip_setup__unit',
            'assay_result__chip_readout__chip_setup__assay_run_id',
            'assay_result__created_by',
            'assay_result__group',
            'assay_result__signed_off_by',
            'result_function',
            'result_type',
            'test_unit'
        )

        queryset = filter_queryset_for_viewership(self, queryset)

        # Display to users with either editor or viewer group or if unrestricted
        # group_names = [group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]
        return queryset


ChipTestResultFormSet = inlineformset_factory(
    AssayChipTestResult,
    AssayChipResult,
    formset=ChipTestResultInlineFormset,
    extra=1,
    exclude=[],
    widgets={'value': forms.NumberInput(attrs={'style': 'width:100px;', })}
)


class AssayChipTestResultAdd(StudyGroupRequiredMixin, CreateView):
    """Add a Chip Test Result with inline for individual results"""
    template_name = 'assays/assaychiptestresult_add.html'
    form_class = AssayChipResultForm

    def get_form(self, form_class):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        current = None

        if self.request.method == 'POST':
            form = form_class(study, current, self.request.POST)
        else:
            form = form_class(study, current)

        add_study_fields_to_form(self, form)

        return form

    def get_context_data(self, **kwargs):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        context = super(AssayChipTestResultAdd, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = ChipTestResultFormSet(self.request.POST, study=study)
            else:
                context['formset'] = ChipTestResultFormSet(study=study)

        context['study'] = study

        return context

    def form_valid(self, form):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        formset = ChipTestResultFormSet(self.request.POST, instance=form.instance, study=study)
        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

    # Redirect when there are no available setups
    # TODO REFACTOR
    def render_to_response(self, context):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        exclude_list = AssayChipTestResult.objects.filter(
            chip_readout__isnull=False
        ).values_list(
            'chip_readout',
            flat=True
        )
        readouts = AssayChipReadout.objects.filter(
            chip_setup__assay_run_id=study
        ).exclude(
            id__in=list(set(exclude_list))
        )

        if not readouts:
            return redirect('/assays/' + str(study.id))

        return super(AssayChipTestResultAdd, self).render_to_response(context)


class AssayChipTestResultDetail(StudyGroupRequiredMixin, DetailView):
    """Display details for Chip Test Result"""
    model = AssayChipTestResult
    detail = True


class AssayChipTestResultUpdate(StudyGroupRequiredMixin, UpdateView):
    """Update a Chip Test Result and inline of individual results"""
    model = AssayChipTestResult
    template_name = 'assays/assaychiptestresult_add.html'
    form_class = AssayChipResultForm

    def get_form(self, form_class):
        study = self.object.chip_readout.chip_setup.assay_run_id
        current = self.object.chip_readout_id

        # If POST
        if self.request.method == 'POST':
            return form_class(study, current, self.request.POST, instance=self.get_object())
        # If GET
        else:
            return form_class(study, current, instance=self.get_object())

    def get_context_data(self, **kwargs):
        study = self.object.chip_readout.chip_setup.assay_run_id
        context = super(AssayChipTestResultUpdate, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = ChipTestResultFormSet(self.request.POST, instance=self.object, study=study)
            else:
                context['formset'] = ChipTestResultFormSet(instance=self.object, study=study)

        context['study'] = study

        context['update'] = True

        return context

    def form_valid(self, form):
        study = self.object.chip_readout.chip_setup.assay_run_id
        formset = ChipTestResultFormSet(self.request.POST, instance=self.object, study=study)

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayChipTestResultDelete(DeletionMixin, DeleteView):
    """Delete a Chip Test Result"""
    model = AssayChipTestResult
    template_name = 'assays/assaychiptestresult_delete.html'

    def get_success_url(self):
        return '/assays/' + str(self.object.chip_readout.chip_setup.assay_run_id_id)


# Class-based views for study configuration
class StudyConfigurationList(LoginRequiredMixin, ListView):
    """Display a list of Study Configurations"""
    model = StudyConfiguration
    template_name = 'assays/studyconfiguration_list.html'


# FormSet for Study Models
StudyModelFormSet = inlineformset_factory(
    StudyConfiguration,
    StudyModel,
    extra=1,
    exclude=[],
    widgets={
        'label': forms.TextInput(attrs={'size': 2}),
        'sequence_number': forms.TextInput(attrs={'size': 2})
    }
)


class StudyConfigurationAdd(OneGroupRequiredMixin, CreateView):
    """Add a Study Configuration with inline for Associtated Models"""
    template_name = 'assays/studyconfiguration_add.html'
    form_class = StudyConfigurationForm

    def get_context_data(self, **kwargs):
        context = super(StudyConfigurationAdd, self).get_context_data(**kwargs)

        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = StudyModelFormSet(self.request.POST)
            else:
                context['formset'] = StudyModelFormSet()

        return context

    def form_valid(self, form):
        formset = StudyModelFormSet(self.request.POST, instance=form.instance)

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class StudyConfigurationUpdate(OneGroupRequiredMixin, UpdateView):
    """Update a Study Configuration with inline for Associtated Models"""
    model = StudyConfiguration
    template_name = 'assays/studyconfiguration_add.html'
    form_class = StudyConfigurationForm

    def get_context_data(self, **kwargs):
        context = super(StudyConfigurationUpdate, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = StudyModelFormSet(self.request.POST, instance=self.object)
            else:
                context['formset'] = StudyModelFormSet(instance=self.object)

        context['update'] = True

        return context

    def form_valid(self, form):
        formset = StudyModelFormSet(self.request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


# Class-based views for LAYOUTS
class AssayLayoutList(LoginRequiredMixin, ListView):
    """Display a list of Assay Layouts"""
    model = AssayLayout

    def get_queryset(self):
        # Not bothering with restricted at the moment
        # return AssayLayout.objects.filter(
        # restricted=False
        # ).prefetch_related(
        # 'created_by',
        # 'group',
        # 'device'
        # ) | AssayLayout.objects.filter(
        #     group__in=self.request.user.groups.all()
        # ).prefetch_related('created_by',
        # 'group',
        # 'device'
        # )

        # Assay Layouts do not currently have a detail page, so only allow editors to see
        return AssayLayout.objects.filter(
            group__in=self.request.user.groups.all()
        ).prefetch_related(
            'created_by',
            'group',
            'device',
            'signed_off_by'
        )


class AssayLayoutAdd(OneGroupRequiredMixin, CreateView):
    """Add an Assay Layout"""
    model = AssayLayout
    form_class = AssayLayoutForm
    template_name = 'assays/assaylayout_add.html'

    def get_form(self, form_class):
        # Get group selection possibilities
        groups = filter_groups(self.request.user)

        # If POST
        if self.request.method == 'POST':
            return form_class(groups, self.request.POST)
        # If GET
        else:
            return form_class(groups)

    # Test form validity
    def form_valid(self, form):
        if form.is_valid():
            save_forms_with_tracking(self, form, formset=None, update=False)
            # Save assay layout
            save_assay_layout(self.request, self.object, form, False)
            return redirect(self.object.get_post_submission_url())

        else:
            return self.render_to_response(self.get_context_data(form=form))


# TODO Assay Layout Detail does not currently exist (deemed lower priority)
# class AssayLayoutDetail(DetailRedirectMixin, DetailView):
#     model = AssayLayout


class AssayLayoutUpdate(ObjectGroupRequiredMixin, UpdateView):
    """Update an Assay Layout"""
    model = AssayLayout
    form_class = AssayLayoutForm
    template_name = 'assays/assaylayout_add.html'

    def get_form(self, form_class):
        # Get group selection possibilities
        groups = filter_groups(self.request.user)

        # If POST
        if self.request.method == 'POST':
            return form_class(groups, self.request.POST, instance=self.get_object())
        # If GET
        else:
            return form_class(groups, instance=self.get_object())

    def get_context_data(self, **kwargs):
        context = super(AssayLayoutUpdate, self).get_context_data(**kwargs)
        context['update'] = True

        return context

    def form_valid(self, form):
        if form.is_valid():
            save_forms_with_tracking(self, form, formset=None, update=True)
            # Save assay layout
            save_assay_layout(self.request, self.object, form, True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AssayLayoutDelete(DeletionMixin, DeleteView):
    """Delete an Assay Layout"""
    model = AssayLayout
    template_name = 'assays/assaylayout_delete.html'

    def get_success_url(self):
        return '/assays/assaylayout/'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data()

        context['setups'] = AssayPlateSetup.objects.filter(assay_layout=self.object)
        context['readouts'] = AssayPlateReadout.objects.filter(setup=context['setups'])
        context['results'] = AssayPlateTestResult.objects.filter(readout=context['readouts'])

        return self.render_to_response(context)


# Class-based views for LAYOUTS
class AssayPlateSetupList(LoginRequiredMixin, ListView):
    """List all Plate Setups"""
    model = AssayPlateSetup

    def get_queryset(self):
        queryset = AssayPlateSetup.objects.prefetch_related(
            'created_by',
            'group',
            'assay_run_id',
            'assay_layout',
            'signed_off_by'
        )

        queryset = filter_queryset_for_viewership(self, queryset)

        # Display to users with either editor or viewer group or if unrestricted
        # group_names = [group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]
        return queryset


# Formset for plate cells
AssayPlateCellsFormset = inlineformset_factory(
    AssayPlateSetup,
    AssayPlateCells,
    formset=AssayPlateCellsInlineFormset,
    extra=1,
    exclude=[],
    widgets={
        'cellsample_density': forms.NumberInput(attrs={'style': 'width:100px;', }),
        'cell_passage': forms.TextInput(attrs={'size': 5})
    }
)


# VIEWS FOR ASSAY PLATE (DEVICE) SETUP
class AssayPlateSetupAdd(StudyGroupRequiredMixin, CreateView):
    """Add a Plate Setup with inline for Plate Cells"""
    model = AssayPlateSetup
    form_class = AssayPlateSetupForm
    template_name = 'assays/assayplatesetup_add.html'

    # Specify that cloning is permitted
    cloning_permitted = True

    def get_form(self, form_class):
        if self.request.method == 'POST':
            form = form_class(self.request.POST)
        elif self.request.GET.get('clone', ''):
            pk = int(self.request.GET.get('clone', ''))
            clone = get_object_or_404(AssayPlateSetup, pk=pk)
            form = form_class(instance=clone)
        else:
            form = form_class()

        add_study_fields_to_form(self, form, add_study=True)

        return form

    def get_context_data(self, **kwargs):
        cellsamples = get_cell_samples(self.request.user)

        context = super(AssayPlateSetupAdd, self).get_context_data(**kwargs)

        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = AssayPlateCellsFormset(self.request.POST)
            elif self.request.GET.get('clone', ''):
                pk = int(self.request.GET.get('clone', ''))
                clone = get_object_or_404(AssayPlateSetup, pk=pk)
                context['formset'] = AssayPlateCellsFormset(instance=clone)
            else:
                context['formset'] = AssayPlateCellsFormset()

        # Cellsamples will always be the same
        context['cellsamples'] = cellsamples

        return context

    def form_valid(self, form):
        formset = AssayPlateCellsFormset(self.request.POST, instance=form.instance, save_as_new=True)
        # get user via self.request.user
        if form.is_valid() and formset.is_valid():
            data = form.cleaned_data

            save_forms_with_tracking(self, form, formset=formset, update=False)

            if data['another']:
                form = self.form_class(
                    instance=self.object,
                    initial={'success': True}
                )
                return self.render_to_response(self.get_context_data(form=form))
            else:
                return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


# TODO Assay Layout Detail does not currently exist (deemed lower priority)
class AssayPlateSetupDetail(StudyGroupRequiredMixin, DetailView):
    """Details for a Plate Setup"""
    model = AssayPlateSetup
    detail = True


class AssayPlateSetupUpdate(StudyGroupRequiredMixin, UpdateView):
    """Update a Plate Setup with inline for Plate Cells"""
    model = AssayPlateSetup
    form_class = AssayPlateSetupForm
    template_name = 'assays/assayplatesetup_add.html'

    def get_context_data(self, **kwargs):
        cellsamples = get_cell_samples(self.request.user, plate_setup=self.object)

        context = super(AssayPlateSetupUpdate, self).get_context_data(**kwargs)

        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = AssayPlateCellsFormset(self.request.POST, instance=self.object)
            else:
                context['formset'] = AssayPlateCellsFormset(instance=self.object)

        # Cellsamples will always be the same
        context['cellsamples'] = cellsamples
        # Mark as update
        context['update'] = True

        return context

    def form_valid(self, form):
        formset = AssayPlateCellsFormset(self.request.POST, instance=form.instance)
        # get user via self.request.user
        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayPlateSetupDelete(DeletionMixin, DeleteView):
    """Delete a Plate Setup"""
    model = AssayPlateSetup
    template_name = 'assays/assayplatesetup_delete.html'

    def get_success_url(self):
        return '/assays/' + str(self.object.assay_run_id_id)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data()

        context['readouts'] = AssayPlateReadout.objects.filter(setup=self.object)
        context['results'] = AssayPlateTestResult.objects.filter(readout=context['readouts'])

        return self.render_to_response(context)


# Class based views for readouts
class AssayPlateReadoutList(LoginRequiredMixin, ListView):
    """Display a list of Plate Readouts"""
    model = AssayPlateReadout

    def get_queryset(self):
        queryset = AssayPlateReadout.objects.prefetch_related(
            'created_by',
            'group',
            'setup__assay_run_id',
            'signed_off_by'
        )

        # Display to users with either editor or viewer group or if unrestricted
        # group_names = [group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]
        queryset = filter_queryset_for_viewership(self, queryset)

        # Map assays
        related_assays = AssayPlateReadoutAssay.objects.filter(
            readout_id__in=queryset
        ).prefetch_related(
            'readout_id',
            'assay_id'
        ).order_by(
            'assay_id__assay_short_name'
        )
        related_assays_map = {}

        for assay in related_assays:
            # start appending to a list keyed by the readout ID for all related images
            related_assays_map.setdefault(assay.readout_id_id, []).append(assay)

        for readout in queryset:
            # set an attribute on the readout that is the list created above
            readout.related_assays = related_assays_map.get(readout.id)

        return queryset

APRAFormSet = inlineformset_factory(
    AssayPlateReadout,
    AssayPlateReadoutAssay,
    formset=AssayPlateReadoutInlineFormset,
    extra=1,
    exclude=[],
)


# TODO MODIFY PLATES TO USE UNIFIED FUNCTIONS FOR PROCESSING DATA
class AssayPlateReadoutAdd(StudyGroupRequiredMixin, CreateView):
    """Add a Plate Readout with inline for Assay Plate Readout Assays"""
    template_name = 'assays/assayplatereadout_add.html'
    form_class = AssayPlateReadoutForm
    model = AssayPlateReadout

    # Specify that cloning is permitted
    cloning_permitted = True

    def get_form(self, form_class):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        current = None
        if self.request.method == 'POST':
            form = form_class(study, current, self.request.POST, self.request.FILES)
        elif self.request.GET.get('clone', ''):
            pk = int(self.request.GET.get('clone', ''))
            clone = get_object_or_404(AssayPlateReadout, pk=pk)
            form = form_class(
                study,
                current,
                instance=clone,
                initial={'file': None}
            )
            # We do not want to keep the file (setup automatically excluded))
        else:
            form = form_class(study, current)

        add_study_fields_to_form(self, form)

        return form

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReadoutAdd, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = APRAFormSet(self.request.POST, self.request.FILES)
            elif self.request.GET.get('clone', ''):
                pk = int(self.request.GET.get('clone', ''))
                clone = get_object_or_404(AssayPlateReadout, pk=pk)
                context['formset'] = APRAFormSet(instance=clone)
            else:
                context['formset'] = APRAFormSet()

        context['study'] = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])

        return context

    def form_valid(self, form):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        formset = APRAFormSet(self.request.POST, self.request.FILES, instance=form.instance, save_as_new=True)
        # get user via self.request.user
        if form.is_valid() and formset.is_valid():
            data = form.cleaned_data

            # Get upload_type
            # upload_type = data.get('upload_type')
            overwrite_option = data.get('overwrite_option')

            save_forms_with_tracking(self, form, formset=formset, update=False)

            if formset.files.get('file', ''):
                study_id = self.kwargs['study_id']
                parse_file_and_save(
                    self.object.file, self.object.modified_by, study_id, overwrite_option, 'Plate', form=form, readout=self.object
                )
                # parse_readout_csv(self.object, current_file, upload_type)
                # Check QC
                # modify_qc_status_plate(self.object, form)
            if data['another']:
                form = self.form_class(
                    study,
                    None,
                    instance=self.object,
                    initial={'file': None, 'success': True}
                )
                return self.render_to_response(self.get_context_data(form=form))
            else:
                return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

    # Redirect when there are no available setups
    # TODO REFACTOR
    def render_to_response(self, context):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        exclude_list = AssayPlateReadout.objects.filter(setup__isnull=False).values_list('setup', flat=True)
        setups = AssayPlateSetup.objects.filter(
            assay_run_id=study
        ).prefetch_related(
            'assay_run_id',
            'assay_layout',
            'created_by'
        ).exclude(
            id__in=list(set(exclude_list))
        )

        if not setups:
            return redirect('/assays/' + str(study.id))

        return super(AssayPlateReadoutAdd, self).render_to_response(context)


# TODO NEED TO ADD TEMPLATE
class AssayPlateReadoutDetail(StudyGroupRequiredMixin, DetailView):
    """Details for a Plate Readout"""
    model = AssayPlateReadout
    detail = True

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReadoutDetail, self).get_context_data(**kwargs)

        # data_uploads = AssayDataUpload.objects.filter(
        #     plate_readout=self.object
        # ).prefetch_related(
        #     'created_by'
        # ).distinct().order_by('created_on')

        context['data_uploads'] = get_data_uploads(plate_readout=self.object)

        return context

class AssayPlateReadoutUpdate(StudyGroupRequiredMixin, UpdateView):
    """Update a Plate Readout with inline for Assay Plate Readout Assays"""
    model = AssayPlateReadout
    template_name = 'assays/assayplatereadout_add.html'
    form_class = AssayPlateReadoutForm

    def get_form(self, form_class):
        study = self.object.setup.assay_run_id
        current = self.object.setup_id
        if self.request.method == 'POST':
            return form_class(study, current, self.request.POST, self.request.FILES, instance=self.object)
        else:
            return form_class(study, current, instance=self.object)

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReadoutUpdate, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = APRAFormSet(self.request.POST, self.request.FILES, instance=self.object)
            else:
                context['formset'] = APRAFormSet(instance=self.object)

        # data_uploads = AssayDataUpload.objects.filter(
        #     plate_readout=self.object
        # ).prefetch_related(
        #     'created_by'
        # ).distinct().order_by('created_on')

        context['data_uploads'] = get_data_uploads(plate_readout=self.object)

        context['study'] = self.object.setup.assay_run_id

        context['update'] = True

        return context

    def form_valid(self, form):
        formset = APRAFormSet(self.request.POST, self.request.FILES, instance=form.instance)
        # get user via self.request.user
        if form.is_valid() and formset.is_valid():
            data = form.cleaned_data
            # Get upload_type
            # upload_type = data.get('upload_type')
            overwrite_option = data.get('overwrite_option')

            save_forms_with_tracking(self, form, formset=formset, update=True)

            # Clear data if clear is checked
            if self.request.POST.get('file-clear', ''):
                # remove_existing_readout(self.object)
                AssayReadout.objects.filter(assay_device_readout=self.object).delete()
            # Save file if it exists
            elif formset.files.get('file', ''):
                # current_file = formset.files.get('file', '')
                study_id = str(self.object.setup.assay_run_id.id)
                parse_file_and_save(
                    self.object.file, self.object.modified_by, study_id, overwrite_option, 'Plate', readout=self.object, form=form
                )
                # parse_readout_csv(self.object, current_file, upload_type)
            else:
                # Check QC
                modify_qc_status_plate(self.object, form)
            # Otherwise do nothing (the file remained the same)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


# TODO ADD CONTEXT
class AssayPlateReadoutDelete(DeletionMixin, DeleteView):
    """Delete an Assay Plate Readout"""
    model = AssayPlateReadout
    template_name = 'assays/assayplatereadout_delete.html'

    def get_success_url(self):
        return '/assays/' + str(self.object.setup.assay_run_id_id)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data()

        context['results'] = AssayPlateTestResult.objects.filter(readout=self.object)

        return self.render_to_response(context)


# Class-based views for PLATE test results
class AssayPlateTestResultList(LoginRequiredMixin, ListView):
    """Display individual Assa Plate Results"""
    # model = AssayChipTestResult
    template_name = 'assays/assayplatetestresult_list.html'

    def get_queryset(self):
        queryset = AssayPlateResult.objects.prefetch_related(
            'result_function',
            'result_type',
            'test_unit',
            'assay_result__readout__setup__assay_run_id',
            'assay_result__created_by',
            'assay_result__group',
            'assay_result__signed_off_by'
        )

        queryset = filter_queryset_for_viewership(self, queryset)

        # Display to users with either editor or viewer group or if unrestricted
        # group_names = [group.name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]
        return queryset


PlateTestResultFormSet = inlineformset_factory(
    AssayPlateTestResult,
    AssayPlateResult,
    formset=PlateTestResultInlineFormset,
    extra=1,
    exclude=[],
    widgets={'value': forms.NumberInput(attrs={'style': 'width:100px;', })}
)


class AssayPlateTestResultAdd(StudyGroupRequiredMixin, CreateView):
    """Add Plate Test Result with inline for individual Plate Results"""
    template_name = 'assays/assayplatetestresult_add.html'
    form_class = AssayPlateResultForm

    def get_form(self, form_class):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        current = None

        if self.request.method == 'POST':
            form = form_class(study, current, self.request.POST)
        else:
            form = form_class(study, current)

        add_study_fields_to_form(self, form)

        return form

    def get_context_data(self, **kwargs):
        context = super(AssayPlateTestResultAdd, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = PlateTestResultFormSet(self.request.POST)
            else:
                context['formset'] = PlateTestResultFormSet()

        context['study'] = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])

        return context

    def form_valid(self, form):
        formset = PlateTestResultFormSet(self.request.POST, instance=form.instance)
        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

    # Redirect when there are no available setups
    # TODO REFACTOR
    def render_to_response(self, context):
        study = get_object_or_404(AssayRun, pk=self.kwargs['study_id'])
        exclude_list = AssayPlateTestResult.objects.filter(readout__isnull=False).values_list('readout', flat=True)
        readouts = AssayPlateReadout.objects.filter(setup__assay_run_id=study).exclude(id__in=list(set(exclude_list)))

        if not readouts:
            return redirect('/assays/' + str(study.id))

        return super(AssayPlateTestResultAdd, self).render_to_response(context)


class AssayPlateTestResultDetail(StudyGroupRequiredMixin, DetailView):
    """Details for Plate Test Results"""
    model = AssayPlateTestResult
    detail = True


class AssayPlateTestResultUpdate(StudyGroupRequiredMixin, UpdateView):
    """Update a Plate Test Result with inline for individual Plate Results"""
    model = AssayPlateTestResult
    template_name = 'assays/assayplatetestresult_add.html'
    form_class = AssayPlateResultForm

    def get_form(self, form_class):
        study = self.object.readout.setup.assay_run_id
        current = self.object.readout_id

        if self.request.method == 'POST':
            return form_class(study, current, self.request.POST, instance=self.object)
        else:
            return form_class(study, current, instance=self.object)

    def get_context_data(self, **kwargs):
        context = super(AssayPlateTestResultUpdate, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = PlateTestResultFormSet(self.request.POST, instance=self.object)
            else:
                context['formset'] = PlateTestResultFormSet(instance=self.object)

        context['study'] = self.object.readout.setup.assay_run_id

        context['update'] = True

        return context

    def form_valid(self, form):
        formset = PlateTestResultFormSet(self.request.POST, instance=self.object)
        # get user via self.request.user
        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayPlateTestResultDelete(DeletionMixin, DeleteView):
    """Delete a Plate Test Result"""
    model = AssayPlateTestResult
    template_name = 'assays/assayplatetestresult_delete.html'

    def get_success_url(self):
        return '/assays/' + str(self.object.readout.setup.assay_run_id_id)


class ReadoutBulkUpload(ObjectGroupRequiredMixin, UpdateView):
    """Upload an Excel Sheet for storing multiple sets of Readout data at one"""
    model = AssayRun
    template_name = 'assays/readoutbulkupload.html'
    form_class = ReadoutBulkUploadForm

    def get_form(self, form_class):
        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, request=self.request, instance=self.get_object())
        # If GET
        else:
            return form_class(instance=self.get_object())

    def get_context_data(self, **kwargs):
        context = super(ReadoutBulkUpload, self).get_context_data(**kwargs)

        chip_readouts = AssayChipReadout.objects.filter(
            chip_setup__assay_run_id=self.object
        ).prefetch_related('chip_setup')
        plate_readouts = AssayPlateReadout.objects.filter(
            setup__assay_run_id=self.object
        ).prefetch_related('setup')

        data_points = AssayChipRawData.objects.filter(
            assay_chip_id__chip_setup__assay_run_id=self.object
        ).exclude(
            quality__contains=REPLACED_DATA_POINT_CODE
        ).prefetch_related(
            *CHIP_DATA_PREFETCH
        )

        # TODO Could use a refactor
        # Should use mapping similar to data_upload, methinks
        chip_has_data = {}
        for readout in chip_readouts:
            if data_points.filter(assay_chip_id=readout):
                chip_has_data.update({readout: True})
        plate_has_data = {}
        for readout in plate_readouts:
            if AssayReadout.objects.filter(assay_device_readout=readout):
                plate_has_data.update({readout: True})

        # data_uploads = AssayDataUpload.objects.filter(
        #     study=self.object
        # ).prefetch_related(
        #     'created_by'
        # ).distinct().order_by('created_on')
        #
        # data_upload_map = {}
        #
        # for data_point in data_points:
        #     data_upload_map.setdefault(
        #         data_point.data_upload_id, True
        #     )
        #
        # for data_upload in data_uploads:
        #     data_upload.has_data = data_upload_map.get(data_upload.id, '')

        context['data_uploads'] = get_data_uploads(study=self.object)

        context['chip_readouts'] = chip_readouts
        context['plate_readouts'] = plate_readouts

        context['chip_has_data'] = chip_has_data
        context['plate_has_data'] = plate_has_data

        context['version'] = len(os.listdir(MEDIA_ROOT + '/excel_templates/')) / 3

        return context

    def form_valid(self, form):
        if form.is_valid():
            data = form.cleaned_data
            overwrite_option = data.get('overwrite_option')

            # For the moment, just have headers be equal to two?
            # headers = 1
            study_id = str(self.object.id)

            # Add user to Study's modified by
            # TODO
            if self.request and self.request.FILES:
                self.object.bulk_file = data.get('bulk_file')
                self.object.modified_by = self.request.user
                self.object.save()

                parse_file_and_save(self.object.bulk_file, self.object.modified_by, study_id, overwrite_option, 'Bulk', form=None)

            # Only check if user is qualified editor
            if is_group_editor(self.request.user, self.object.group.name):
                # Contrived method for marking data
                for key, value in form.data.iteritems():
                    if key.startswith('data_upload_'):
                        current_id = key.replace('data_upload_', '', 1)
                        current_value = value

                        if current_value == 'false':
                            current_value = False

                        if current_value:
                            data_upload = AssayDataUpload.objects.filter(study=self.object, id=current_id)
                            if data_upload:
                                data_points_to_replace = AssayChipRawData.objects.filter(data_upload=data_upload).exclude(quality__contains=REPLACED_DATA_POINT_CODE)
                                for data_point in data_points_to_replace:
                                    data_point.quality = data_point.quality + REPLACED_DATA_POINT_CODE
                                    data_point.save()

            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ReturnStudyData(StudyViewershipMixin, DetailView):
    """Returns a combined file for all data in a study"""
    model = AssayRun

    def render_to_response(self, context, **response_kwargs):
        # Make sure that the study exists, then continue
        if self.object:
            # Set response to binary
            # For xlsx
            # response = HttpResponse(mimetype="application/ms-excel")
            # response['Content-Disposition'] = 'attachment; filename=%s' % self.object.assay_run_id
            #
            # workbook = xlsxwriter.Workbook(self.object.assay_run_id + '.xlsx')

            # If chip data
            chip_readouts = AssayChipReadout.objects.filter(
                chip_setup__assay_run_id_id=self.object
            ).prefetch_related(
                'chip_setup__assay_run_id'
            )

            include_all = self.request.GET.get('include_all', False)

            chip_data = get_chip_readout_data_as_csv(chip_readouts, include_header=True, include_all=include_all)

            # For specifically text
            response = HttpResponse(chip_data, content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename=' + self.object.assay_run_id + '.csv'

            return response
        # Return nothing otherwise
        else:
            return HttpResponse('', content_type='text/plain')


class AssayRunReproducibility(StudyViewershipMixin, DetailView):
    """Returns a form and processed statistical information. """

    model = AssayRun
    template_name = 'assays/reproducibility.html'
