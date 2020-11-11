# coding=utf-8
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    TemplateView,
    DeleteView,
)
from django.http import HttpResponse, JsonResponse
from cellsamples.models import CellSample
from assays.models import (
    AssayStudyConfiguration,
    AssayStudyModel,
    AssayStudy,
    AssayMatrix,
    AssayMatrixItem,
    AssayTarget,
    AssayMethod,
    PhysicalUnits,
    AssaySampleLocation,
    AssayImage,
    AssayImageSetting,
    AssayStudyAssay,
    AssaySetupCompound,
    AssaySetupCell,
    AssaySetupSetting,
    AssayStudyStakeholder,
    AssayDataFileUpload,
    AssayDataPoint,
    AssayStudySupportingData,
    AssayStudySet,
    AssayReference,
    AssayTarget,
    AssayMeasurementType,
    AssaySampleLocation,
    AssaySetting,
    AssaySupplier,
    AssayPlateReaderMap,
    AssayPlateReaderMapItem,
    AssayPlateReaderMapItemValue,
    AssayPlateReaderMapDataFile,
    AssayPlateReaderMapDataFileBlock,
    assay_plate_reader_map_info_shape_col_dict,
    assay_plate_reader_map_info_shape_row_dict,
    assay_plate_reader_map_info_plate_size_choices,
    assay_plate_reader_map_info_plate_size_choices_list,
    upload_file_location,
    AssayOmicDataFileUpload,
    AssayOmicDataPoint,
    AssayGroup,
)
from assays.forms import (
    AssayStudyConfigurationForm,
    ReadyForSignOffForm,
    AssayStudyForm,
    AssayStudyDetailForm,
    AssayStudyGroupForm,
    AssayStudyChipForm,
    AssayStudyPlateForm,
    AssayStudyAssaysForm,
    AssayStudySupportingDataFormSetFactory,
    AssayStudyAssayFormSetFactory,
    AssayStudyReferenceFormSetFactory,
    AssayStudyDeleteForm,
    AssayMatrixForm,
    AssayMatrixItemFullForm,
    AssayMatrixItemFormSetFactory,
    AssaySetupCompoundFormSetFactory,
    AssaySetupCellFormSetFactory,
    AssaySetupSettingFormSetFactory,
    AssaySetupCompoundInlineFormSetFactory,
    AssaySetupCellInlineFormSetFactory,
    AssaySetupSettingInlineFormSetFactory,
    AssayStudySignOffForm,
    AssayStudyStakeholderFormSetFactory,
    AssayStudyDataUploadForm,
    AssayStudyModelFormSet,
    AssayStudySetForm,
    AssayReferenceForm,
    AssayStudySetReferenceFormSetFactory,
    AssayMatrixFormNew,
    AssayTargetForm,
    AssayTargetRestrictedForm,
    AssayMethodForm,
    AssayMethodRestrictedForm,
    AssayMeasurementTypeForm,
    AssaySettingForm,
    PhysicalUnitsForm,
    AssaySampleLocationForm,
    AssaySupplierForm,
    AssayPlateReaderMapForm,
    AssayPlateReaderMapItemFormSetFactory,
    # AssayPlateReaderMapItemValueFormSetFactory,
    AssayPlateReadMapAdditionalInfoForm,
    AssayPlateReaderMapDataFileAddForm,
    AssayPlateReaderMapDataFileForm,
    AssayPlateReaderMapDataFileBlockFormSetFactory,
    AbstractClassAssayStudyAssay,
    AssayOmicDataFileUploadForm,
    AssayMatrixItemForm,
)

from microdevices.models import MicrophysiologyCenter
from django import forms

# TODO REVISE SPAGHETTI CODE
from assays.ajax import get_data_as_csv, fetch_data_points_from_filters, get_filtered_omics_data_as_csv
from assays.utils import (
    AssayFileProcessor,
    get_user_accessible_studies,
    # modify_templates,
    DEFAULT_CSV_HEADER,
    add_update_plate_reader_data_map_item_values_from_file,
    plate_reader_data_file_process_data,
)

from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect

from mps.templatetags.custom_filters import (
    ADMIN_SUFFIX,
    VIEWER_SUFFIX,
    filter_groups,
    is_group_editor,
    is_group_admin
)

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from mps.mixins import (
    LoginRequiredMixin,
    OneGroupRequiredMixin,
    ObjectGroupRequiredMixin,
    StudyDeletionMixin,
    user_is_active,
    PermissionDenied,
    StudyGroupMixin,
    StudyViewerMixin,
    CreatorOrSuperuserRequiredMixin,
    FormHandlerMixin,
    ListHandlerMixin,
    CreatorAndNotInUseMixin,
    HistoryMixin
)

from mps.base.models import save_forms_with_tracking
from django.contrib.auth.models import User, Group
from mps.settings import DEFAULT_FROM_EMAIL

import ujson as json
import os
import csv
import re

from mps.settings import MEDIA_ROOT, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX

from django.template.loader import render_to_string, TemplateDoesNotExist

from django.db.models import Count
from datetime import datetime, timedelta
import xlrd
import pytz

from django.apps import apps

import io

from django.db import connection

# File writing
# ???
from io import BytesIO
import xlsxwriter
from assays.utils import DEFAULT_CSV_HEADER
from mps.settings import TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX

# TODO Refactor imports
# TODO REFACTOR CERTAIN WHITTLING TO BE IN FORM AS OPPOSED TO VIEW
# TODO Rename get_absolute_url when the function does not actually return the model's URL
# TODO It is probably more semantic to overwrite get_context_data and form_valid in lieu of post and get for updates
# TODO ^ Update Views should be refactored soon
# NOTE THAT YOU NEED TO MODIFY INLINES HERE, NOT IN FORMS

# TODO TODO TODO render_to_response is DEPRECATED: USE render INSTEAD


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


def get_data_file_uploads(study=None, matrix_item=None):
    """Get data uploads for a study"""
    valid_files = []

    if study:
        data_file_uploads = AssayDataFileUpload.objects.filter(
            study_id=study
        ).distinct().order_by('created_on')

        data_points = AssayDataPoint.objects.filter(
            study_id=study
        ).exclude(
            replaced=True
        )
    elif matrix_item:
        data_file_uploads = AssayDataFileUpload.objects.filter(
            study_id=matrix_item.study
        ).prefetch_related(
            'created_by'
        ).distinct().order_by('created_on')

        data_points = AssayDataPoint.objects.filter(
            study_id=study
        ).exclude(
            replaced=True
        )
    else:
        data_file_uploads = AssayDataUpload.objects.none()
        data_points = AssayDataPoint.objects.none()

    # Edge case for old data
    if data_points and data_points.exclude(data_file_upload=None).count() == 0:
        return data_file_uploads

    data_file_upload_map = {}
    for data_point in data_points:
        data_file_upload_map.setdefault(
            data_point.data_file_upload_id, True
        )

    for data_file_upload in data_file_uploads:
        if data_file_upload_map.get(data_file_upload.id, ''):
            valid_files.append(data_file_upload)

    return valid_files


def get_queryset_with_stakeholder_sign_off(queryset):
    """Add the stakeholder status to each object in an AssayStudy Queryset

    The stakeholder_sign_off is True is there are no stakeholders that need to sign off
    """
    # A stakeholder is needed if the sign off is required and there is no pk for the individual signing off
    required_stakeholders_without_sign_off = AssayStudyStakeholder.objects.filter(
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


def get_user_status_context(self, context):
    """Takes the view and context, adds user_is_group_admin, editor, and stakeholder editor to the context"""
    user_group_names = {group.name for group in self.request.user.groups.all()}

    context['user_is_group_admin'] = self.object.group.name + ADMIN_SUFFIX in user_group_names
    context['user_is_group_editor'] = self.object.group.name in user_group_names or context['user_is_group_admin']

    stakeholders = AssayStudyStakeholder.objects.filter(
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


def get_queryset_with_group_center_dictionary(queryset):
    """Takes the queryset, adds a dictionary 'group_center_map' mapping each group to its center"""
    group_center_map = {}

    centers = MicrophysiologyCenter.objects.all().prefetch_related(
        'groups'
    )

    for center in centers:
        for group in center.groups.all():
            group_center_map[group.id] = center

    for study in queryset:
        study.center = group_center_map.get(study.group_id, '')


# Deprecated anyway
class AssayStudyConfigurationMixin(FormHandlerMixin):
    model = AssayStudyConfiguration
    template_name = 'assays/studyconfiguration_add.html'
    form_class = AssayStudyConfigurationForm

    formsets = (
        ('formset', AssayStudyModelFormSet),
    )


class AssayStudyConfigurationAdd(OneGroupRequiredMixin, AssayStudyConfigurationMixin, CreateView):
    pass


class AssayStudyConfigurationUpdate(OneGroupRequiredMixin, AssayStudyConfigurationMixin, UpdateView):
    pass

# Class-based views for study configuration
class AssayStudyConfigurationList(LoginRequiredMixin, ListView):
    """Display a list of Study Configurations"""
    model = AssayStudyConfiguration
    template_name = 'assays/studyconfiguration_list.html'


# class AssayStudyConfigurationAdd(OneGroupRequiredMixin, CreateView):
#     """Add a Study Configuration with inline for Associtated Models"""
#     template_name = 'assays/studyconfiguration_add.html'
#     form_class = AssayStudyConfigurationForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayStudyConfigurationAdd, self).get_context_data(**kwargs)
#
#         if 'formset' not in context:
#             if self.request.POST:
#                 context['formset'] = AssayStudyModelFormSet(self.request.POST)
#             else:
#                 context['formset'] = AssayStudyModelFormSet()
#
#         return context
#
#     def form_valid(self, form):
#         formset = AssayStudyModelFormSet(self.request.POST, instance=form.instance)
#
#         if form.is_valid() and formset.is_valid():
#             save_forms_with_tracking(self, form, formset=formset, update=False)
#             return redirect(self.object.get_post_submission_url())
#         else:
#             return self.render_to_response(self.get_context_data(form=form, formset=formset))
#
#
# class AssayStudyConfigurationUpdate(OneGroupRequiredMixin, UpdateView):
#     """Update a Study Configuration with inline for Associtated Models"""
#     model = AssayStudyConfiguration
#     template_name = 'assays/studyconfiguration_add.html'
#     form_class = AssayStudyConfigurationForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayStudyConfigurationUpdate, self).get_context_data(**kwargs)
#         if 'formset' not in context:
#             if self.request.POST:
#                 context['formset'] = AssayStudyModelFormSet(self.request.POST, instance=self.object)
#             else:
#                 context['formset'] = AssayStudyModelFormSet(instance=self.object)
#
#         context['update'] = True
#
#         return context
#
#     def form_valid(self, form):
#         formset = AssayStudyModelFormSet(self.request.POST, instance=self.object)
#
#         if form.is_valid() and formset.is_valid():
#             save_forms_with_tracking(self, form, formset=formset, update=True)
#             return redirect(self.object.get_post_submission_url())
#         else:
#             return self.render_to_response(self.get_context_data(form=form, formset=formset))


# BEGIN NEW
def get_queryset_with_organ_model_map(queryset):
    """Takes a queryset and returns it with a organ model map"""
    # Not DRY
    study_ids = list(queryset.values_list('id', flat=True))

    setups = AssayMatrixItem.objects.filter(
        organ_model__isnull=False,
        study_id__in=study_ids
    ).prefetch_related(
        # 'matrix__study',
        # 'device',
        'organ_model',
        # 'organ_model_protocol'
    ).only(
        'id',
        'study_id',
        'organ_model'
    )

    organ_model_map = {}

    for setup in setups:
        organ_model_map.setdefault(
            setup.study_id, {}
        ).update(
            {
                setup.organ_model.name: True
            }
        )

    for study in queryset:
        study.organ_models = ',\n'.join(
            sorted(organ_model_map.get(study.id, {}).keys())
        )


def get_queryset_with_number_of_data_points(queryset):
    """Add number of data points to each object in an Assay Study querysey"""
    study_ids = list(queryset.values_list('id', flat=True))

    data_points = AssayDataPoint.objects.filter(
        replaced=False,
        study_id__in=study_ids
    ).only('id', 'study_id')

    data_points_map = {}

    for data_point in data_points:
        current_value = data_points_map.setdefault(
            data_point.study_id, 0
        )
        data_points_map.update({
            data_point.study_id: current_value + 1
        })

    plate_maps = AssayPlateReaderMap.objects.filter(
        study_id__in=study_ids
    ).only('id', 'study_id')

    plate_reader_files = AssayPlateReaderMapDataFile.objects.filter(
        study_id__in=study_ids
    ).only('id', 'study_id')

    plate_maps_map = {}
    plate_reader_files_map = {}

    for plate_map in plate_maps:
        current_value = plate_maps_map.setdefault(
            plate_map.study_id, 0
        )
        plate_maps_map.update({
            plate_map.study_id: current_value + 1
        })

    for plate_reader_file in plate_reader_files:
        current_value = plate_reader_files_map.setdefault(
            plate_reader_file.study_id, 0
        )
        plate_reader_files_map.update({
            plate_reader_file.study_id: current_value + 1
        })

    images = AssayImage.objects.filter(
        setting__study_id__in=study_ids
    ).prefetch_related(
        'setting'
    ).only('id', 'setting__study_id', 'setting', 'file_name')

    video_formats = {x: True for x in [
        'webm',
        'avi',
        'ogv',
        'mov',
        'wmv',
        'mp4',
        '3gp',
    ]}

    images_map = {}
    videos_map = {}

    for image in images:
        is_video = image.file_name.split('.')[-1].lower() in video_formats

        if is_video:
            current_value = videos_map.setdefault(
                image.setting.study_id, 0
            )
            videos_map.update({
                image.setting.study_id: current_value + 1
            })
        else:
            current_value = images_map.setdefault(
                image.setting.study_id, 0
            )
            images_map.update({
                image.setting.study_id: current_value + 1
            })

    supporting_data = AssayStudySupportingData.objects.filter(
        study_id__in=study_ids
    ).only('id', 'study_id')

    supporting_data_map = {}

    for supporting in supporting_data:
        current_value = supporting_data_map.setdefault(
            supporting.study_id, 0
        )
        supporting_data_map.update({
            supporting.study_id: current_value + 1
        })

    for study in queryset:
        study.data_points = data_points_map.get(study.id, 0)
        study.images = images_map.get(study.id, 0)
        study.videos = videos_map.get(study.id, 0)
        study.supporting_data = supporting_data_map.get(study.id, 0)
        study.plate_maps = plate_maps_map.get(study.id, 0)
        study.plate_reader_files = plate_reader_files_map.get(study.id, 0)


# TODO GET NUMBER OF DATA POINTS
# TODO REVIEW PERMISSIONS
# Class-based views for studies
class AssayStudyEditableList(OneGroupRequiredMixin, ListView):
    """Displays all of the studies linked to groups that the user is part of"""
    template_name = 'assays/assaystudy_list.html'

    def get_queryset(self):
        queryset = AssayStudy.objects.prefetch_related(
            'created_by',
            'group',
            'signed_off_by',
            # 'study_types'
        )

        # Display to users with either editor or viewer group or if unrestricted
        group_names = [group.name.replace(ADMIN_SUFFIX, '') for group in self.request.user.groups.all()]

        # Exclude signed off studies
        queryset = queryset.filter(group__name__in=group_names, signed_off_by_id=None)

        get_queryset_with_organ_model_map(queryset)
        get_queryset_with_number_of_data_points(queryset)
        get_queryset_with_group_center_dictionary(queryset)
        # DOESN'T MATTER, ANYTHING THAT IS SIGNED OFF CAN'T BE EDITED
        # get_queryset_with_stakeholder_sign_off(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(AssayStudyEditableList, self).get_context_data(**kwargs)

        # Adds the word "editable" to the page
        context['editable'] = 'Editable '

        return context


class AssayStudyList(ListView):
    """A list of all studies"""
    template_name = 'assays/assaystudy_list.html'
    model = AssayStudy

    def get_queryset(self):
        combined = get_user_accessible_studies(self.request.user)

        get_queryset_with_organ_model_map(combined)
        get_queryset_with_number_of_data_points(combined)
        get_queryset_with_stakeholder_sign_off(combined)
        get_queryset_with_group_center_dictionary(combined)

        return combined


class AssayStudyMixin(FormHandlerMixin):
    model = AssayStudy
    # Study is now split into many pages, probably best to list them explicitly
    # template_name = 'assays/assaystudy_add.html'
    # form_class = AssayStudyForm

    # formsets = (
    #     ('study_assay_formset', AssayStudyAssayFormSetFactory),
    #     ('supporting_data_formset', AssayStudySupportingDataFormSetFactory),
    #     ('reference_formset', AssayStudyReferenceFormSetFactory),
    # )

    # def get_context_data(self, **kwargs):
    #     context = super(AssayStudyMixin, self).get_context_data(**kwargs)

    #     # TODO SLATED FOR REMOVAL
    #     context.update({
    #         'reference_queryset': AssayReference.objects.all()
    #     })

    #     return context

    def get_context_data(self, **kwargs):
        context = super(AssayStudyMixin, self).get_context_data(**kwargs)

        has_chips = False
        has_plates = False

        # CRUDE: NEEDS REVISION
        if self.object:
            study_groups = AssayGroup.objects.filter(
                study_id=self.object.id,
            ).prefetch_related('organ_model__device')

            has_chips = study_groups.filter(
                organ_model__device__device_type='chip'
            ).count() > 0

            has_plates = study_groups.filter(
                organ_model__device__device_type='plate'
            ).count() > 0

        # TODO: Check whether this Study has Chips or Plates
        # Contrived at the moment
        context.update({
            'has_chips': has_chips,
            'has_plates': has_plates,
            'has_next_button': True,
            'has_previous_button': True,
            'cellsamples' : CellSample.objects.all().prefetch_related(
                'cell_type__organ',
                'supplier',
                'cell_subtype__cell_type'
            )
        })

        return context


class AssayStudyDetailsMixin(AssayStudyMixin):
    template_name = 'assays/assaystudy_details.html'
    form_class = AssayStudyDetailForm

    # Do we want references here?
    formsets = (
        ('reference_formset', AssayStudyReferenceFormSetFactory),
    )

    def get_context_data(self, **kwargs):
        context = super(AssayStudyDetailsMixin, self).get_context_data(**kwargs)

        # TODO SLATED FOR REMOVAL
        context.update({
            'reference_queryset': AssayReference.objects.all(),
            'has_next_button': True,
            'has_previous_button': False
        })

        return context


class AssayStudyAdd(OneGroupRequiredMixin, AssayStudyDetailsMixin, CreateView):
    # Special handling for handling next button
    def extra_form_processing(self, form):
        # Contact superusers
        # Superusers to contact
        superusers_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)

        # Magic strings are in poor taste, should use a template instead
        superuser_subject = 'Study Created: {0}'.format(form.instance)
        superuser_message = render_to_string(
            'assays/email/superuser_study_created_alert.txt',
            {
                'study': form.instance
            }
        )

        for user_to_be_alerted in superusers_to_be_alerted:
            user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)

        if self.request.POST.get('post_submission_url_override') == '#':
            self.post_submission_url_override = reverse('assays-assaystudy-update-groups', args=[form.instance.pk])
        return super(AssayStudyAdd, self).extra_form_processing(form)


# TO BE DEPRECATED
# Update is not sufficiently descriptive of any of the pages
class AssayStudyUpdate(ObjectGroupRequiredMixin, AssayStudyMixin, UpdateView):
    template_name = 'assays/assaystudy_add.html'
    form_class = AssayStudyForm

    formsets = (
        ('study_assay_formset', AssayStudyAssayFormSetFactory),
        ('supporting_data_formset', AssayStudySupportingDataFormSetFactory),
        ('reference_formset', AssayStudyReferenceFormSetFactory),
    )

    def get_context_data(self, **kwargs):
        context = super(AssayStudyMixin, self).get_context_data(**kwargs)

        # TODO SLATED FOR REMOVAL
        context.update({
            'reference_queryset': AssayReference.objects.all()
        })

        return context


class AssayStudyDetails(ObjectGroupRequiredMixin, AssayStudyDetailsMixin, UpdateView):
    pass


class AssayStudyGroups(ObjectGroupRequiredMixin, AssayStudyMixin, UpdateView):
    template_name = 'assays/assaystudy_groups.html'
    form_class = AssayStudyGroupForm

    # Oh no! We actually need to have special handling for the "next" button
    # TODO
    # Special handling for handling next button
    def extra_form_processing(self, form):
        # If the user submitted with "next"
        if self.request.POST.get('post_submission_url_override') == reverse('assays-assaystudy-update-assays', args=[form.instance.pk]):
            # CRUDE: NOT DRY
            study_groups = AssayGroup.objects.filter(
                study_id=self.object.id,
            ).prefetch_related('organ_model__device')

            has_chips = study_groups.filter(
                organ_model__device__device_type='chip'
            ).count() > 0

            has_plates = study_groups.filter(
                organ_model__device__device_type='plate'
            ).count() > 0

            # If there are chip groups, go to chips
            if has_chips:
                self.post_submission_url_override = reverse('assays-assaystudy-update-chips', args=[form.instance.pk])

            # If there are plate groups, go to plates
            elif has_plates:
                self.post_submission_url_override = reverse('assays-assaystudy-update-plates', args=[form.instance.pk])

        # Otherwise it will just go to assays, like usual
        return super(AssayStudyGroups, self).extra_form_processing(form)

class AssayStudyChips(ObjectGroupRequiredMixin, AssayStudyMixin, UpdateView):
    template_name = 'assays/assaystudy_chips.html'
    # Might end up being a formset?
    form_class = AssayStudyChipForm

    def get_context_data(self, **kwargs):
        context = super(AssayStudyChips, self).get_context_data(**kwargs)

        # TODO SLATED FOR REMOVAL
        context.update({
            'update': True,
            # TODO REVISE
            'chips': AssayMatrixItem.objects.filter(
                device__device_type='chip',
                study_id=self.object.id
            )
        })

        return context


# This is now really just a list page
class AssayStudyPlates(ObjectGroupRequiredMixin, AssayStudyMixin, DetailView):
    template_name = 'assays/assaystudy_plates.html'
    form_class = AssayStudyPlateForm

    # Contrived
    def get_context_data(self, **kwargs):
        context = super(AssayStudyPlates, self).get_context_data(**kwargs)

        # TODO SLATED FOR REMOVAL
        context.update({
            'update': True,
            # TODO REVISE
            'plates': AssayMatrix.objects.filter(
                # OLD
                # device__isnull=False,
                organ_model__isnull=False,
                study_id=self.object.id
            )
        })

        return context


class AssayStudyPlateMixin(FormHandlerMixin):
    model = AssayMatrix
    template_name = 'assays/assaystudy_plate_add.html'
    # Might actually be a formset or something?
    form_class = AssayStudyPlateForm

    def get_context_data(self, **kwargs):
        context = super(AssayStudyPlateMixin, self).get_context_data(**kwargs)

        # TODO: Check whether this Study has Chips or Plates
        # Contrived at the moment
        context.update({
            # TODO
            'has_chips': True,
            # Necessarily True!
            'has_plates': True,
            'specific_plate': True,
            'cellsamples' : CellSample.objects.all().prefetch_related(
                'cell_type__organ',
                'supplier',
                'cell_subtype__cell_type'
            ),
            'has_next_button': True,
            'has_previous_button': True
        })

        return context


class AssayStudyPlateAdd(StudyGroupMixin, AssayStudyPlateMixin, CreateView):
    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # Get the study
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, study=study, user=self.request.user)
        # If GET
        else:
            return form_class(study=study, user=self.request.user)


class AssayStudyPlateUpdate(StudyGroupMixin, AssayStudyPlateMixin, UpdateView):
    pass


class AssayStudyAssays(ObjectGroupRequiredMixin, AssayStudyMixin, UpdateView):
    template_name = 'assays/assaystudy_assays.html'
    # This will probably just be a contrived empty form
    form_class = AssayStudyAssaysForm

    formsets = (
        ('study_assay_formset', AssayStudyAssayFormSetFactory),
    )


# class AssayStudyAdd(OneGroupRequiredMixin, CreateView):
#     """Add a study"""
#     template_name = 'assays/assaystudy_add.html'
#     form_class = AssayStudyForm
#
#     def get_form(self, form_class=None):
#         form_class = self.get_form_class()
#         # Get group selection possibilities
#         groups = filter_groups(self.request.user)
#
#         # If POST
#         if self.request.method == 'POST':
#             return form_class(self.request.POST, self.request.FILES, groups=groups)
#         # If GET
#         else:
#             return form_class(groups=groups)
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayStudyAdd, self).get_context_data(**kwargs)
#         if self.request.POST:
#             if 'study_assay_formset' not in context:
#                 context['study_assay_formset'] = AssayStudyAssayFormSetFactory(self.request.POST)
#             if 'supporting_data_formset' not in context:
#                 context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(self.request.POST, self.request.FILES)
#             if 'reference_formset' not in context:
#                 context['reference_formset'] = AssayStudyReferenceFormSetFactory(self.request.POST)
#         else:
#             context['study_assay_formset'] = AssayStudyAssayFormSetFactory()
#             context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory()
#             context['reference_formset'] = AssayStudyReferenceFormSetFactory()
#
#         context['reference_queryset'] = AssayReference.objects.all()
#
#         return context
#
#     def form_valid(self, form):
#         study_assay_formset = AssayStudyAssayFormSetFactory(
#             self.request.POST,
#             instance=form.instance
#         )
#         supporting_data_formset = AssayStudySupportingDataFormSetFactory(
#             self.request.POST,
#             self.request.FILES,
#             instance=form.instance
#         )
#         reference_formset = AssayStudyReferenceFormSetFactory(
#             self.request.POST,
#             instance=form.instance
#         )
#         if form.is_valid() and study_assay_formset.is_valid() and supporting_data_formset.is_valid() and reference_formset.is_valid():
#             save_forms_with_tracking(self, form, formset=[study_assay_formset, supporting_data_formset, reference_formset], update=False)
#             return redirect(
#                 self.object.get_absolute_url()
#             )
#         else:
#             return self.render_to_response(
#                 self.get_context_data(
#                     form=form,
#                     study_assay_formset=study_assay_formset,
#                     supporting_data_formset=supporting_data_formset,
#                     reference_formset=reference_formset
#                 )
#             )
#
#
# # TODO CHANGE
# class AssayStudyUpdate(ObjectGroupRequiredMixin, UpdateView):
#     """Update the fields of a Study"""
#     model = AssayStudy
#     template_name = 'assays/assaystudy_add.html'
#     form_class = AssayStudyForm
#
#     def get_form(self, form_class=None):
#         form_class = self.get_form_class()
#         # Get group selection possibilities
#         groups = filter_groups(self.request.user)
#
#         # If POST
#         if self.request.method == 'POST':
#             return form_class(self.request.POST, self.request.FILES, instance=self.object, groups=groups)
#         # If GET
#         else:
#             return form_class(instance=self.object, groups=groups)
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayStudyUpdate, self).get_context_data(**kwargs)
#         if self.request.POST:
#             if 'study_assay_formset' not in context:
#                 context['study_assay_formset'] = AssayStudyAssayFormSetFactory(self.request.POST, instance=self.object)
#             if 'supporting_data_formset' not in context:
#                 context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(self.request.POST, self.request.FILES, instance=self.object)
#             if 'reference_formset' not in context:
#                 context['reference_formset'] = AssayStudyReferenceFormSetFactory(self.request.POST, instance=self.object)
#         else:
#             context['study_assay_formset'] = AssayStudyAssayFormSetFactory(instance=self.object)
#             context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(instance=self.object)
#             context['reference_formset'] = AssayStudyReferenceFormSetFactory(instance=self.object)
#
#         context['reference_queryset'] = AssayReference.objects.all()
#         context['update'] = True
#
#         return context
#
#     def form_valid(self, form):
#         study_assay_formset = AssayStudyAssayFormSetFactory(
#             self.request.POST,
#             instance=form.instance
#         )
#         supporting_data_formset = AssayStudySupportingDataFormSetFactory(
#             self.request.POST,
#             self.request.FILES,
#             instance=form.instance
#         )
#         reference_formset = AssayStudyReferenceFormSetFactory(
#             self.request.POST,
#             instance=form.instance
#         )
#         # TODO TODO TODO TODO
#         if form.is_valid() and study_assay_formset.is_valid() and supporting_data_formset.is_valid() and reference_formset.is_valid():
#             save_forms_with_tracking(self, form, formset=[study_assay_formset, supporting_data_formset, reference_formset], update=True)
#
#             return redirect(
#                 self.object.get_absolute_url()
#             )
#         else:
#             return self.render_to_response(
#                 self.get_context_data(
#                     form=form,
#                     study_assay_formset=study_assay_formset,
#                     supporting_data_formset=supporting_data_formset,
#                     reference_formset=reference_formset
#                 )
#             )


# TODO: TO BE REVISED
class AssayStudyIndex(StudyViewerMixin, DetailView):
    """Show all chip and plate models associated with the given study"""
    model = AssayStudy
    context_object_name = 'study_index'
    template_name = 'assays/assaystudy_index.html'

    # For permission mixin NOT AS USELESS AS IT SEEMS
    def get_object(self, queryset=None):
        self.study = super(AssayStudyIndex, self).get_object()
        return self.study

    # NOTE: bracket assignations are against PEP, one should use .update
    def get_context_data(self, **kwargs):
        context = super(AssayStudyIndex, self).get_context_data(**kwargs)

        # matrices = AssayMatrix.objects.filter(
        #     study_id=self.object.id
        # ).prefetch_related(
        #     'assaymatrixitem_set',
        #     'created_by',
        # )

        items = AssayMatrixItem.objects.filter(
            # matrix_id__in=matrices
            study_id=self.object.id
        ).prefetch_related(
            # Implicit in group
            'device',
            'created_by',
            # 'matrix',
            # Implicit in group
            'organ_model',

            # Stupid way to acquire group values, but expedient I guess

            'group__assaygroupcompound_set__compound_instance__compound',
            'group__assaygroupcompound_set__concentration_unit',
            'group__assaygroupcompound_set__addition_location',
            'group__assaygroupcell_set__cell_sample__cell_type__organ',
            'group__assaygroupcell_set__cell_sample__cell_subtype',
            'group__assaygroupcell_set__cell_sample__supplier',
            'group__assaygroupcell_set__addition_location',
            'group__assaygroupcell_set__density_unit',
            'group__assaygroupsetting_set__setting',
            'group__assaygroupsetting_set__unit',
            'group__assaygroupsetting_set__addition_location',

            # 'assaysetupcompound_set__compound_instance__compound',
            # 'assaysetupcompound_set__concentration_unit',
            # 'assaysetupcompound_set__addition_location',
            # 'assaysetupcell_set__cell_sample__cell_type__organ',
            # 'assaysetupcell_set__cell_sample__cell_subtype',
            # 'assaysetupcell_set__cell_sample__supplier',
            # 'assaysetupcell_set__addition_location',
            # 'assaysetupcell_set__density_unit',
            # 'assaysetupsetting_set__setting',
            # 'assaysetupsetting_set__unit',
            # 'assaysetupsetting_set__addition_location',
        )

        # Cellsamples will always be the same
        # context['matrices'] = matrices
        context['items'] = items

        get_user_status_context(self, context)

        context['ready_for_sign_off_form'] = ReadyForSignOffForm()

        # Stakeholder status
        context['stakeholder_sign_off'] = AssayStudyStakeholder.objects.filter(
            study_id=self.object.id,
            signed_off_by_id=None,
            sign_off_required=True
        ).count() == 0

        context['detail'] = True

        # We will get the number of chips, plates, and groups of either categories
        chip_groups = AssayGroup.objects.filter(
            study_id=self.object.id,
            # Messy way to ascertain plate v chip
            # We might benefit from a field in this regard?
            # Perhaps we ought to redundantly link the device afterall?
            organ_model__device__device_type='chip'
        ).prefetch_related('organ_model__device')
        plate_groups = AssayGroup.objects.filter(
            study_id=self.object.id,
            # See above
            organ_model__device__device_type='plate'
        ).prefetch_related('organ_model__device')

        # We could indicate something like the number of chips
        number_of_chips = AssayMatrixItem.objects.filter(
            # Theoretically, chips bound to said group are in the study
            group_id__in=chip_groups
        ).count()

        # We assume that matrices with devices are plates
        plates = AssayMatrix.objects.filter(
            # WHOOPS
            # device__isnull=False,
            organ_model__isnull=False,
            study_id=self.object.id
        )

        context.update({
            'chip_groups': chip_groups,
            'plate_groups': plate_groups,
            'number_of_chips': number_of_chips,
            'plates': plates,
        })

        return context


class AssayStudySummary(StudyViewerMixin, TemplateView):
    """Displays information for a given study

    Currently only shows data for chip readouts and chip/plate setups
    """
    model = AssayStudy
    template_name = 'assays/assaystudy_summary.html'

    # TODO TODO TODO
    def get_context_data(self, **kwargs):
        context = super(AssayStudySummary, self).get_context_data(**kwargs)

        # Get the study
        study = get_object_or_404(AssayStudy, pk=self.kwargs['pk'])

        # This gets a little odd, I make what would be the get_object call here so I can prefetch some things
        current_study = AssayStudy.objects.filter(id=study.id).prefetch_related(
            'assaystudyassay_set__target',
            'assaystudyassay_set__method',
            'assaystudyassay_set__unit',
            'group__microphysiologycenter_set'
        )[0]

        context.update({
            'object': current_study,
            'data_file_uploads': get_data_file_uploads(study=current_study),
            'detail': True
        })

        self.object = current_study

        # TODO TODO TODO TODO TODO PERMISSIONS
        get_user_status_context(self, context)

        return context


class AssayStudyData(StudyViewerMixin, DetailView):
    """Returns a combined file for all data in a study"""
    model = AssayStudy

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
            items = AssayMatrixItem.objects.filter(
                study_id=self.object.id
            )

            include_all = self.request.GET.get('include_all', False)

            data = get_data_as_csv(items, include_header=True, include_all=include_all)

            # For specifically text
            response = HttpResponse(data, content_type='text/csv', charset='utf-8')
            response['Content-Disposition'] = 'attachment;filename="' + str(self.object) + '.csv"'

            return response
        # Return nothing otherwise
        else:
            return HttpResponse('', content_type='text/plain')


# TODO TODO TODO FIX
# TODO TODO TODO
class AssayStudySignOff(HistoryMixin, UpdateView):
    """Perform Sign Offs as a group adming or stake holder admin"""
    model = AssayStudy
    template_name = 'assays/assaystudy_sign_off.html'
    form_class = AssayStudySignOffForm

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
            stakeholders = AssayStudyStakeholder.objects.filter(
                study_id=study.id
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
            return super(AssayStudySignOff, self).dispatch(*args, **kwargs)
        else:
            return PermissionDenied(self.request, 'You must be a qualified group administrator to view this page')

    def get_context_data(self, **kwargs):
        context = super(AssayStudySignOff, self).get_context_data(**kwargs)

        if self.request.POST:
            context.update({
                'stakeholder_formset': AssayStudyStakeholderFormSetFactory(
                    self.request.POST,
                    instance=self.object,
                    user=self.request.user
                )
            })
        else:
            context.update({
                'stakeholder_formset': AssayStudyStakeholderFormSetFactory(
                    instance=self.object,
                    user=self.request.user
                )
            })

        context.update({
            'update': True
        })

        return context

    def form_valid(self, form):
        # Sloppy addition of logging
        change_message = 'Modified Sign Off/Approval'
        self.log_change(self.request, self.object, change_message)

        stakeholder_formset = AssayStudyStakeholderFormSetFactory(
            self.request.POST,
            instance=form.instance,
            user=self.request.user
        )

        if form.is_valid() and stakeholder_formset.is_valid():
            tz = pytz.timezone('US/Eastern')
            datetime_now_local = datetime.now(tz)
            fourteen_days_from_date = datetime_now_local + timedelta(days=14)

            send_initial_sign_off_alert = False
            initial_number_of_required_sign_offs = AssayStudyStakeholder.objects.filter(
                study_id=self.object.id,
                signed_off_by_id=None,
                sign_off_required=True
            ).count()

            # Only allow if necessary
            if is_group_admin(self.request.user, self.object.group.name) and not self.object.signed_off_by:
                send_initial_sign_off_alert = not form.instance.signed_off_by and form.cleaned_data.get('signed_off', '')
                # TODO DO NOT USE FUNCTIONS LIKE THIS
                save_forms_with_tracking(self, form, update=True)

            # save_forms_with_tracking(self, form, formset=[stakeholder_formset], update=True)

            if stakeholder_formset.has_changed():
                # TODO DO NOT USE FUNCTIONS LIKE THIS
                save_forms_with_tracking(self, None, formset=[stakeholder_formset], update=True)

            current_number_of_required_sign_offs = AssayStudyStakeholder.objects.filter(
                study_id=self.object.id,
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
                    AssayStudyStakeholder.objects.filter(
                        study_id=self.object.id, sign_off_required=True
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
                                'fourteen_days_from_date': fourteen_days_from_date
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
                    AssayStudyStakeholder.objects.filter(
                        study_id=self.object.id
                    ).prefetch_related('group').values_list('group__name', flat=True)
                }
                initial_groups = list(stakeholder_viewer_groups.keys())

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
                        'stakeholders': AssayStudyStakeholder.objects.filter(study_id=self.object.id).order_by('-signed_off_date')
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
                        'stakeholders': AssayStudyStakeholder.objects.filter(study_id=self.object.id).order_by('-signed_off_date')
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


class AssayStudyDataUpload(AssayStudyMixin, ObjectGroupRequiredMixin, UpdateView):
    """Upload an Excel Sheet for storing multiple sets of Readout data at one"""
    template_name = 'assays/assaystudy_upload.html'
    form_class = AssayStudyDataUploadForm

    # TODO: STRANGE
    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, request=self.request, instance=self.get_object())
        # If GET
        else:
            return form_class(instance=self.get_object())

    def get_context_data(self, **kwargs):
        context = super(AssayStudyDataUpload, self).get_context_data(**kwargs)

        # TODO TODO TODO
        # context['version'] = len(os.listdir(MEDIA_ROOT + '/excel_templates/'))

        # context['data_file_uploads'] = get_data_file_uploads(study=self.object)

        if self.request.POST:
            if 'supporting_data_formset' not in context:
                context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(instance=self.object)

        # context['update'] = True

        context.update({
            'data_file_uploads': get_data_file_uploads(study=self.object),
            'update': True,
            'has_next_button': False
        })

        return context

    def form_valid(self, form):
        supporting_data_formset = AssayStudySupportingDataFormSetFactory(
            self.request.POST,
            self.request.FILES,
            instance=self.object
        )

        if form.is_valid() and supporting_data_formset.is_valid():
            data = form.cleaned_data
            overwrite_option = data.get('overwrite_option')

            study_id = str(self.object.id)

            # Add user to Study's modified by
            # TODO
            if self.request and self.request.FILES and data.get('bulk_file', ''):
                # Be positive it is not just processing the same file again
                if not self.object.bulk_file or self.object.bulk_file != data.get('bulk_file'):
                    self.object.bulk_file = data.get('bulk_file')
                    self.object.modified_by = self.request.user
                    self.object.save()

                    file_processor = AssayFileProcessor(self.object.bulk_file, self.object, self.request.user, save=True)
                    # Process the file
                    file_processor.process_file()
                    # parse_file_and_save(self.object.bulk_file, self.object.modified_by, study_id, overwrite_option, 'Bulk', form=None)

            # Only check if user is qualified editor
            if is_group_editor(self.request.user, self.object.group.name):
                # Contrived save for supporting data
                save_forms_with_tracking(
                    self,
                    None,
                    formset=[supporting_data_formset],
                    update=True
                )

                # Sloppy addition of logging
                change_message = 'Modified Upload'
                self.log_change(self.request, self.object, change_message)

                # Contrived method for marking data
                for key, value in list(form.data.items()):
                    if key.startswith('data_upload_'):
                        current_id = key.replace('data_upload_', '', 1)
                        current_value = value

                        if current_value == 'false':
                            current_value = False

                        if current_value:
                            data_file_upload = AssayDataFileUpload.objects.filter(study_id=self.object.id, id=current_id)
                            if data_file_upload:
                                data_points_to_replace = AssayDataPoint.objects.filter(data_file_upload__in=data_file_upload).exclude(replaced=True)
                                data_points_to_replace.update(replaced=True)

            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AssayStudyDelete(StudyDeletionMixin, UpdateView):
    """Soft Delete a Study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_delete.html'
    success_url = '/assays/assaystudy/'
    form_class = AssayStudyDeleteForm

    # Shouldn't trigger emails
    def form_valid(self, form):
        # Check permissions again
        if is_group_editor(self.request.user, self.object.group.name):
            # Change the group
            # CONTRIVED
            self.object.modified_by = self.request.user
            # Change group to hide
            self.object.group_id = Group.objects.filter(name='DELETED')[0].id
            # Remove sign off
            self.object.signed_off_by = None
            # Restrict
            self.object.restricted = True
            # REMOVE COLLABORATOR GROUPS
            self.object.collaborator_groups.clear()

            tz = pytz.timezone('US/Eastern')

            # Note deletion in study (crude)
            self.object.description = 'Deleted by {} on {}\n{}'.format(
                self.request.user,
                datetime.now(tz),
                self.object.description
            )

            self.object.name = 'DELETED-{}'.format(self.object.name)
            self.object.flagged = True

            self.object.save()

        return redirect(self.success_url)


class AssayStudyTemplate(ObjectGroupRequiredMixin, DetailView):
    model = AssayStudy

    def render_to_response(self, context, **response_kwargs):
        # The workbook is just in memory
        current_output = BytesIO()
        current_template = xlsxwriter.Workbook(current_output)

        for assay_index, current_assay in enumerate(self.object.assaystudyassay_set.all()):
            current_sheet = current_template.add_worksheet('Assay {}'.format(assay_index + 1))

            # Set up formats
            chip_red = current_template.add_format()
            chip_red.set_bg_color('#ff6f69')
            chip_green = current_template.add_format()
            chip_green.set_bg_color('#96ceb4')

            # Write the base files
            # Some danger here, must change this and other template
            initial = [
                DEFAULT_CSV_HEADER,
                [
                    # Chip ID
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    # Target
                    str(current_assay.target.name),
                    None,
                    # Method
                    str(current_assay.method.name),
                    # Sample
                    None,
                    None,
                    # Value Unit
                    str(current_assay.unit.unit),
                    None,
                    None,
                    None,
                    None
                ]
            ]

            # Set the initial values

            initial_format = [
                [chip_red] * 17,
                [
                    chip_green,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    chip_green,
                    None,
                    chip_green,
                    chip_green,
                    None,
                    chip_green,
                    None,
                    None,
                    None,
                    None
                ]
            ]

            # Write out initial
            for row_index, row in enumerate(initial):
                for column_index, column in enumerate(row):
                    cell_format = initial_format[row_index][column_index]
                    current_sheet.write(row_index, column_index, column, cell_format)

            # Set column widths
            # Chip
            current_sheet.set_column('A:A', 20)
            current_sheet.set_column('B:B', 20)
            current_sheet.set_column('C:C', 20)
            current_sheet.set_column('D:D', 15)
            current_sheet.set_column('E:E', 10)
            current_sheet.set_column('F:F', 10)
            current_sheet.set_column('G:G', 10)
            current_sheet.set_column('H:H', 20)
            current_sheet.set_column('I:I', 10)
            current_sheet.set_column('J:J', 20)
            current_sheet.set_column('K:K', 15)
            current_sheet.set_column('L:L', 10)
            current_sheet.set_column('M:M', 10)
            current_sheet.set_column('N:N', 10)
            current_sheet.set_column('O:O', 10)
            current_sheet.set_column('P:P', 10)
            current_sheet.set_column('Q:Q', 100)
            # chip_sheet.set_column('I:I', 20)
            # chip_sheet.set_column('J:J', 15)
            # chip_sheet.set_column('K:K', 10)
            # chip_sheet.set_column('L:L', 10)
            # chip_sheet.set_column('M:M', 10)
            # chip_sheet.set_column('N:N', 10)
            # chip_sheet.set_column('O:O', 10)
            # chip_sheet.set_column('P:P', 100)

            current_sheet.set_column('BA:BD', 30)

            # Get list of chip IDS for this study
            chips = AssayMatrixItem.objects.filter(
                study_id=self.object.id
            ).order_by('name').values_list('name', flat=True)

            # Get list of value units  (TODO CHANGE ORDER_BY)
            value_units = PhysicalUnits.objects.all().order_by(
                'base_unit__unit',
                'scale_factor'
            ).values_list('unit', flat=True)

            # List of targets
            targets = AssayTarget.objects.all().order_by(
                'name'
            ).values_list('name', flat=True)

            # List of methods
            methods = AssayMethod.objects.all().order_by(
                'name'
            ).values_list('name', flat=True)

            # List of sample locations
            sample_locations = AssaySampleLocation.objects.all().order_by(
                'name'
            ).values_list('name', flat=True)

            for index, value in enumerate(chips):
                current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX + 4, value)

            for index, value in enumerate(sample_locations):
                current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX + 3, value)

            for index, value in enumerate(methods):
                current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX + 2, value)

            for index, value in enumerate(value_units):
                current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX + 1, value)

            for index, value in enumerate(targets):
                current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX, value)

            chips_range = '=$BE$1:$BE$' + str(len(chips))

            value_units_range = '=$BB$1:$BB$' + str(len(value_units))

            targets_range = '=$BA$1:$BA$' + str(len(targets))
            methods_range = '=$BC$1:$BC$' + str(len(methods))
            sample_locations_range = '=$BD$1:$BD$' + str(len(sample_locations))


            current_sheet.data_validation('A2', {'validate': 'list',
                                       'source': chips_range})
            current_sheet.data_validation('H2', {'validate': 'list',
                                              'source': targets_range})
            current_sheet.data_validation('J2', {'validate': 'list',
                                       'source': methods_range})
            current_sheet.data_validation('K2', {'validate': 'list',
                                       'source': sample_locations_range})
            current_sheet.data_validation('M2', {'validate': 'list',
                                       'source': value_units_range})

        current_template.close()

        # Return
        # Set response to binary
        # For xlsx
        response = HttpResponse(current_output.getvalue(), content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment;filename="' + str(self.object) + '.xlsx"'

        return response


def get_cell_samples_for_selection(user, setups=None):
    """Returns the cell samples to be listed in setup views

    Params:
    user - the user in the request
    setups - the setups in question
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

    if setups:
        # Get the currently used cell samples
        current_cell_samples = CellSample.objects.filter(
            assaysetupcell__setup__in=setups
        ).prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

    combined_query = cellsamples_with_group | current_cell_samples
    combined_query = combined_query.order_by('-receipt_date').distinct()

    # Return the combination of the querysets
    return combined_query


# TODO REFACTOR
class AssayMatrixAdd(StudyGroupMixin, CreateView):
    """Add a matrix"""
    model = AssayMatrix
    template_name = 'assays/assaymatrix_add.html'
    form_class = AssayMatrixForm

    # A little extreme, but should work
    def post(self, request, **kwargs):
        request.POST = request.POST.copy()

        if request.POST.get('device', None):
            # NOTE BE CAREFUL WITH PREFIX HERE
            for item_index in range(int(request.POST.get('item-TOTAL_FORMS', '0'))):
                request.POST.update({
                    'item-{}-device'.format(item_index): request.POST.get('device')
                })

        return super(AssayMatrixAdd, self).post(request, **kwargs)

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # Get the study
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, study=study, user=self.request.user)
        # If GET
        else:
            return form_class(study=study, user=self.request.user)

    def get_context_data(self, **kwargs):
        # Get the study
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        context = super(AssayMatrixAdd, self).get_context_data(**kwargs)

        # Cellsamples will always be the same
        context['cellsamples'] = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        # Start blank
        # DON'T EVEN BOTHER WITH THE OTHER FORMSETS YET
        if self.request.POST:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                self.request.POST,
                prefix='matrix_item',
                study=study,
                user=self.request.user
            )
        else:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                prefix='matrix_item',
                study=study,
                user=self.request.user
            )

        context['adding'] = True

        return context

    def form_valid(self, form):
        # Get the study
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        # Build the formset from POST
        formset = AssayMatrixItemFormSetFactory(
            self.request.POST,
            instance=form.instance,
            prefix='matrix_item',
            study=study,
            user=self.request.user
        )

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=[formset])
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


# TODO NOT THE RIGHT PERMISSION MIXIN
class AssayMatrixUpdate(HistoryMixin, StudyGroupMixin, UpdateView):
    model = AssayMatrix
    template_name = 'assays/assaymatrix_add.html'
    form_class = AssayMatrixForm

    # A little extreme, but should work
    def post(self, request, **kwargs):
        request.POST = request.POST.copy()

        if request.POST.get('device', None):
            # NOTE BE CAREFUL WITH PREFIX HERE
            for item_index in range(int(request.POST.get('item-TOTAL_FORMS', '0'))):
                request.POST.update({
                    'item-{}-device'.format(item_index): request.POST.get('device')
                })

        return super(AssayMatrixUpdate, self).post(request, **kwargs)

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # Get the study
        study = self.object.study

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, instance=self.object, study=study, user=self.request.user)
        # If GET
        else:
            return form_class(instance=self.object, study=study, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(AssayMatrixUpdate, self).get_context_data(**kwargs)

        # Cellsamples will always be the same
        context['cellsamples'] = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        # context['formset'] = AssayMatrixItemFormSetFactory(instance=self.object)

        matrix_item_queryset = AssayMatrixItem.objects.filter(
            matrix_id=self.object.id
        ).order_by(
            'row_index',
            'column_index'
        ).prefetch_related(
            'device'
        )

        # TODO SORTING CAN MAKE SURE THAT THE FORMS APPEAR IN THE RIGHT ORDER, BUT DECREASE PERFORMANCE
        compound_queryset = AssaySetupCompound.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        cell_queryset = AssaySetupCell.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        setting_queryset = AssaySetupSetting.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        if self.request.POST:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                self.request.POST,
                instance=self.object,
                queryset=matrix_item_queryset,
                prefix='matrix_item',
                user=self.request.user
            )
            context['compound_formset'] = AssaySetupCompoundFormSetFactory(
                self.request.POST,
                queryset=compound_queryset,
                matrix=self.object,
                prefix='compound'
            )
            context['cell_formset'] = AssaySetupCellFormSetFactory(
                self.request.POST,
                queryset=cell_queryset,
                matrix=self.object,
                prefix='cell'
            )
            context['setting_formset'] = AssaySetupSettingFormSetFactory(
                self.request.POST,
                queryset=setting_queryset,
                matrix=self.object,
                prefix='setting'
            )
        else:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                instance=self.object,
                queryset=matrix_item_queryset,
                prefix='matrix_item',
                user=self.request.user
            )
            context['compound_formset'] = AssaySetupCompoundFormSetFactory(
                queryset=compound_queryset,
                matrix=self.object,
                prefix='compound'
            )
            context['cell_formset'] = AssaySetupCellFormSetFactory(
                queryset=cell_queryset,
                matrix=self.object,
                prefix='cell'
            )
            context['setting_formset'] = AssaySetupSettingFormSetFactory(
                queryset=setting_queryset,
                matrix=self.object,
                prefix='setting'
            )

        context['update'] = True

        return context

    def form_valid(self, form):
        # formset = AssayMatrixItemFormSetFactory(self.request.POST, instance=self.object)
        matrix_item_queryset = AssayMatrixItem.objects.filter(matrix=self.object).order_by('row_index', 'column_index')

        item_formset = AssayMatrixItemFormSetFactory(
            self.request.POST,
            instance=self.object,
            queryset=matrix_item_queryset,
            prefix='matrix_item',
            user=self.request.user
        )
        # Order no longer matters really
        compound_formset = AssaySetupCompoundFormSetFactory(
            self.request.POST,
            queryset=AssaySetupCompound.objects.filter(
                matrix_item__in=matrix_item_queryset
            ),
            matrix=self.object,
            prefix='compound'
        )
        cell_formset = AssaySetupCellFormSetFactory(
            self.request.POST,
            queryset=AssaySetupCell.objects.filter(
                matrix_item__in=matrix_item_queryset
            ),
            matrix=self.object,
            prefix='cell'
        )
        setting_formset = AssaySetupSettingFormSetFactory(
            self.request.POST,
            queryset=AssaySetupSetting.objects.filter(
                matrix_item__in=matrix_item_queryset
            ),
            matrix=self.object,
            prefix='setting'
        )

        formsets = [
            item_formset,
            compound_formset,
            cell_formset,
            setting_formset
        ]

        formsets_are_valid = True

        for formset in formsets:
            if not formset.is_valid():
                formsets_are_valid = False

        if form.is_valid() and formsets_are_valid:
            save_forms_with_tracking(self, form, formset=formsets, update=True)

            # Sloppy addition of logging
            change_message = 'Modified'
            self.log_change(self.request, self.object, change_message)

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AssayMatrixDetail(StudyGroupMixin, DetailView):
    """Details for a Matrix"""
    template_name = 'assays/assaymatrix_add.html'
    model = AssayMatrix
    detail = True

    def get_context_data(self, **kwargs):
        context = super(AssayMatrixDetail, self).get_context_data(**kwargs)

        # Cellsamples will always be the same
        context['cellsamples'] = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        # TODO TODO TODO
        # Contrived
        matrix_item_queryset = AssayMatrixItem.objects.filter(
            matrix=self.object
        ).order_by(
            'row_index',
            'column_index'
        ).prefetch_related(
            'device'
        )

        # TODO SORTING CAN MAKE SURE THAT THE FORMS APPEAR IN THE RIGHT ORDER, BUT DECREASE PERFORMANCE
        compound_queryset = AssaySetupCompound.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        cell_queryset = AssaySetupCell.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        setting_queryset = AssaySetupSetting.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        context['item_formset'] = AssayMatrixItemFormSetFactory(
            instance=self.object,
            queryset=matrix_item_queryset,
            prefix='matrix_item'
        )
        context['compound_formset'] = AssaySetupCompoundFormSetFactory(
            queryset=compound_queryset,
            matrix=self.object,
            prefix='compound'
        )
        context['cell_formset'] = AssaySetupCellFormSetFactory(
            queryset=cell_queryset,
            matrix=self.object,
            prefix='cell'
        )
        context['setting_formset'] = AssaySetupSettingFormSetFactory(
            queryset=setting_queryset,
            matrix=self.object,
            prefix='setting'
        )

        context['form'] = AssayMatrixForm(instance=self.object)

        context['detail'] = True

        return context


class AssayMatrixDelete(StudyDeletionMixin, DeleteView):
    """Delete a Setup"""
    model = AssayMatrix
    template_name = 'assays/assaymatrix_delete.html'

    def get_success_url(self):
        return self.object.study.get_absolute_url()


# TODO NEEDS TO BE REVISED
class AssayMatrixItemUpdate(FormHandlerMixin, StudyGroupMixin, UpdateView):
    model = AssayMatrixItem
    template_name = 'assays/assaymatrixitem_add.html'
    # NO, NOT THE FULL FORM
    # form_class = AssayMatrixItemFullForm
    form_class = AssayMatrixItemForm

    def get_context_data(self, **kwargs):
        context = super(AssayMatrixItemUpdate, self).get_context_data(**kwargs)

        # Unfortunate, there ought to be a better way
        context.update({
            'cellsamples' : CellSample.objects.all().prefetch_related(
                'cell_type__organ',
                'supplier',
                'cell_subtype__cell_type'
            )
        })

        return context

    # Extra form processing for exclusions
    # Really, this should be in the form itself?
    def extra_form_processing(self, form):
        try:
            data_point_ids_to_update_raw = json.loads(form.data.get('dynamic_exclusion', '{}'))
            data_point_ids_to_mark_excluded = [
                int(id) for id, value in list(data_point_ids_to_update_raw.items()) if value
            ]
            data_point_ids_to_mark_included = [
                int(id) for id, value in list(data_point_ids_to_update_raw.items()) if not value
            ]
            if data_point_ids_to_mark_excluded:
                AssayDataPoint.objects.filter(
                    matrix_item=form.instance,
                    id__in=data_point_ids_to_mark_excluded
                ).update(excluded=True)
            if data_point_ids_to_mark_included:
                AssayDataPoint.objects.filter(
                    matrix_item=form.instance,
                    id__in=data_point_ids_to_mark_included
                ).update(excluded=False)
        # EVIL EXCEPTION PLEASE REVISE
        except:
            pass

    # Trash from previous iteration
    # def get_context_data(self, **kwargs):
    #     context = super(AssayMatrixItemUpdate, self).get_context_data(**kwargs)

    #     # Junk: We don't need any blasted inlines
    #     # if self.request.POST:
    #     #     context['compound_formset'] = AssaySetupCompoundInlineFormSetFactory(
    #     #         self.request.POST,
    #     #         instance=self.object,
    #     #         # matrix=self.object.matrix
    #     #     )
    #     #     context['cell_formset'] = AssaySetupCellInlineFormSetFactory(
    #     #         self.request.POST,
    #     #         instance=self.object,
    #     #         # matrix=self.object
    #     #     )
    #     #     context['setting_formset'] = AssaySetupSettingInlineFormSetFactory(
    #     #         self.request.POST,
    #     #         instance=self.object,
    #     #         # matrix=self.object
    #     #     )
    #     # else:
    #     #     context['compound_formset'] = AssaySetupCompoundInlineFormSetFactory(
    #     #         instance=self.object,
    #     #         # matrix=self.object.matrix
    #     #     )
    #     #     context['cell_formset'] = AssaySetupCellInlineFormSetFactory(
    #     #         instance=self.object,
    #     #         # matrix=self.object
    #     #     )
    #     #     context['setting_formset'] = AssaySetupSettingInlineFormSetFactory(
    #     #         instance=self.object,
    #     #         # matrix=self.object
    #     #     )

    #     # cellsamples = get_cell_samples_for_selection(self.request.user)

    #     # Cellsamples will always be the same
    #     # context['cellsamples'] = CellSample.objects.all().prefetch_related(
    #     #     'cell_type__organ',
    #     #     'supplier',
    #     #     'cell_subtype__cell_type'
    #     # )

    #     context['update'] = True

    #     return context

    # def form_valid(self, form):
    #     compound_formset = AssaySetupCompoundInlineFormSetFactory(
    #         self.request.POST,
    #         instance=self.object,
    #         # matrix=self.object.matrix
    #     )
    #     cell_formset = AssaySetupCellInlineFormSetFactory(
    #         self.request.POST,
    #         instance=self.object,
    #         # matrix=self.object
    #     )
    #     setting_formset = AssaySetupSettingInlineFormSetFactory(
    #         self.request.POST,
    #         instance=self.object,
    #         # matrix=self.object
    #     )

    #     all_formsets = [
    #         compound_formset,
    #         cell_formset,
    #         setting_formset,
    #     ]

    #     all_formsets_valid =  True

    #     for current_formset in all_formsets:
    #         if not current_formset.is_valid():
    #             all_formsets_valid = False

    #     if form.is_valid() and all_formsets_valid:
    #         save_forms_with_tracking(self, form, update=True, formset=all_formsets)

    #         # Sloppy addition of logging
    #         change_message = self.construct_change_message(form, [], False)
    #         self.log_change(self.request, self.object, change_message)

    #         try:
    #             data_point_ids_to_update_raw = json.loads(form.data.get('dynamic_exclusion', '{}'))
    #             data_point_ids_to_mark_excluded = [
    #                 int(id) for id, value in list(data_point_ids_to_update_raw.items()) if value
    #             ]
    #             data_point_ids_to_mark_included = [
    #                 int(id) for id, value in list(data_point_ids_to_update_raw.items()) if not value
    #             ]
    #             if data_point_ids_to_mark_excluded:
    #                 AssayDataPoint.objects.filter(
    #                     matrix_item=form.instance,
    #                     id__in=data_point_ids_to_mark_excluded
    #                 ).update(excluded=True)
    #             if data_point_ids_to_mark_included:
    #                 AssayDataPoint.objects.filter(
    #                     matrix_item=form.instance,
    #                     id__in=data_point_ids_to_mark_included
    #                 ).update(excluded=False)
    #         # EVIL EXCEPTION PLEASE REVISE
    #         except:
    #             pass

    #         return redirect(self.object.get_post_submission_url())
    #     else:
    #         return self.render_to_response(self.get_context_data(
    #             form=form
    #         ))


class AssayMatrixItemDetail(StudyGroupMixin, DetailView):
    """Details for a Chip Setup"""
    template_name = 'assays/assaymatrixitem_detail.html'
    model = AssayMatrixItem
    detail = True


class AssayMatrixItemDelete(StudyDeletionMixin, DeleteView):
    """Delete a Setup"""
    model = AssayMatrixItem
    template_name = 'assays/assaymatrixitem_delete.html'

    def get_success_url(self):
        return self.object.study.get_absolute_url()


class AssayStudyReproducibility(StudyViewerMixin, DetailView):
    """Returns a form and processed statistical information. """
    model = AssayStudy
    template_name = 'assays/assaystudy_reproducibility.html'


class AssayStudyImages(StudyViewerMixin, DetailView):
    """Displays all of the images linked to the current study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_images.html'

    def get_context_data(self, **kwargs):
        context = super(AssayStudyImages, self).get_context_data(**kwargs)

        study_image_settings = AssayImageSetting.objects.filter(
            study_id=self.object.id
        )
        study_images = AssayImage.objects.filter(
            setting_id__in=study_image_settings
        ).prefetch_related(
            'matrix_item',
            'method',
            'target',
            'sample_location',
            'subtarget',
            'setting__study'
        )

        ordered_study_images = list(
            AssayImage.objects.filter(
                setting_id__in=study_image_settings
            ).order_by(
                'time',
                'file_name'
            ).values_list(
                'id',
                flat=True
            )
        )

        metadata = {}
        tableCols = []
        tableRows = []
        tableData = {}

        for image in study_images:
            metadata[image.id] = image.get_metadata()
            tableData[image.id] = ["".join("".join(image.matrix_item.name.split(" ")).split(",")), "".join("".join(image.setting.color_mapping.upper().split(" ")).split(","))]
            if image.matrix_item.name not in tableRows:
                tableRows.append(image.matrix_item.name)
                metadata[image.matrix_item.name] = image.matrix_item_id
            if image.setting.color_mapping.upper() not in tableCols:
                tableCols.append(image.setting.color_mapping.upper())

        if "PHASE CONTRAST" in tableCols:
            tableCols.insert(0, tableCols.pop(tableCols.index("PHASE CONTRAST")))
        if "BRIGHTFIELD COLOR" in tableCols:
            tableCols.insert(0, tableCols.pop(tableCols.index("BRIGHTFIELD COLOR")))
        if "FAR RED" in tableCols:
            tableCols.insert(0, tableCols.pop(tableCols.index("FAR RED")))
        if "RED" in tableCols:
            tableCols.insert(0, tableCols.pop(tableCols.index("RED")))
        if "GREEN" in tableCols:
            tableCols.insert(0, tableCols.pop(tableCols.index("GREEN")))
        if "BLUE" in tableCols:
            tableCols.insert(0, tableCols.pop(tableCols.index("BLUE")))

        context['metadata'] = json.dumps(metadata)
        context['tableRows'] = json.dumps(tableRows)
        context['tableCols'] = json.dumps(tableCols)
        context['tableData'] = json.dumps(tableData)
        context['orderedStudyImages'] = json.dumps(ordered_study_images)

        # Maybe useful later
        # get_user_status_context(self, context)

        return context


class GraphingReproducibilityFilterView(TemplateView):
    template_name = 'assays/assay_filter.html'


class AssayInterStudyReproducibility(TemplateView):
    template_name = 'assays/assay_interstudy_reproducibility.html'


class AssayStudyDataPlots(TemplateView):
    template_name = 'assays/assaystudy_data_plots.html'


# Inappropriate use of CBV
class AssayDataFromFilters(TemplateView):
    """Returns a combined file for all data for given filters"""
    template_name = 'assays/assay_filter.html'

    def render_to_response(self, context, **response_kwargs):
        pre_filter = {}
        data = None

        # TODO TODO TODO NOT DRY
        if self.request.GET.get('f', None):
            filter_params = self.request.GET.get('f', '    ')

            # PLEASE NOTE THAT + GETS INTERPRETED AS A SPACE (' ')
            current_filters = filter_params.split(' ')

            accessible_studies = get_user_accessible_studies(self.request.user)

            # Notice exclusion of missing organ model
            matrix_items = AssayMatrixItem.objects.filter(
                study_id__in=accessible_studies
            ).exclude(
                organ_model_id=None
            ).prefetch_related(
                'organ_model',
                # 'assaysetupcompound_set__compound_instance',
                # 'assaydatapoint_set__study_assay__target'
            )

            if len(current_filters) and current_filters[0]:
                organ_model_ids = [int(id) for id in current_filters[0].split(',') if id]

                matrix_items = matrix_items.filter(
                    organ_model_id__in=organ_model_ids
                )
            # Default to empty
            else:
                matrix_items = AssayMatrixItem.objects.none()

            accessible_studies = accessible_studies.filter(
                id__in=list(matrix_items.values_list('study_id', flat=True))
            )

            matrix_items.prefetch_related(
                'assaysetupcompound_set__compound_instance',
                'assaydatapoint_set__study_assay__target'
            )

            if len(current_filters) > 1 and current_filters[1]:
                group_ids = [int(id) for id in current_filters[1].split(',') if id]
                accessible_studies = accessible_studies.filter(group_id__in=group_ids)

                matrix_items = matrix_items.filter(
                    study_id__in=accessible_studies
                )
            else:
                matrix_items = AssayMatrixItem.objects.none()

            if len(current_filters) > 2 and current_filters[2]:
                compound_ids = [int(id) for id in current_filters[2].split(',') if id]

                # See whether to include no compounds
                if 0 in compound_ids:
                    matrix_items = matrix_items.filter(
                        assaysetupcompound__compound_instance__compound_id__in=compound_ids
                    ) | matrix_items.filter(assaysetupcompound__isnull=True)
                else:
                    matrix_items = matrix_items.filter(
                        assaysetupcompound__compound_instance__compound_id__in=compound_ids
                    )

            else:
                matrix_items = AssayMatrixItem.objects.none()

            if len(current_filters) > 3 and current_filters[3]:
                target_ids = [int(id) for id in current_filters[3].split(',') if id]

                matrix_items = matrix_items.filter(
                    assaydatapoint__study_assay__target_id__in=target_ids
                ).distinct()

                pre_filter.update({
                    'study_assay__target_id__in': target_ids
                })
            else:
                matrix_items = AssayMatrixItem.objects.none()

            pre_filter.update({
                'matrix_item_id__in': matrix_items.filter(assaydatapoint__isnull=False).distinct()
            })

            # Not particularly DRY
            data_points = AssayDataPoint.objects.filter(
                **pre_filter
            ).prefetch_related(
                # TODO
                'study__group__microphysiologycenter_set',
                'matrix_item__assaysetupsetting_set__setting',
                'matrix_item__assaysetupcell_set__cell_sample',
                'matrix_item__assaysetupcell_set__density_unit',
                'matrix_item__assaysetupcell_set__cell_sample__cell_type__organ',
                'matrix_item__assaysetupcompound_set__compound_instance__compound',
                'matrix_item__assaysetupcompound_set__concentration_unit',
                'matrix_item__device',
                'matrix_item__organ_model',
                'matrix_item__matrix',
                'study_assay__target',
                'study_assay__method',
                'study_assay__unit',
                'sample_location',
                # 'data_file_upload',
                # Will use eventually, maybe
                'subtarget'
            ).filter(
                replaced=False,
                excluded=False,
                value__isnull=False
            ).order_by(
                'matrix_item__name',
                'study_assay__target__name',
                'study_assay__method__name',
                'time',
                'sample_location__name',
                'excluded',
                'update_number'
            )

            data = get_data_as_csv(matrix_items, data_points=data_points, include_header=True)

        if data:
            # Should do eventually
            # include_all = self.request.GET.get('include_all', False)

            # For specifically text
            response = HttpResponse(data, content_type='text/csv', charset='utf-8')
            response['Content-Disposition'] = 'attachment;filename=MPS_Download.csv'

            return response
        # Return nothing otherwise
        else:
            return HttpResponse('', content_type='text/plain')


# TODO acquire and send all data like IntraRepro
# TODO REFACTOR
class AssayStudySetMixin(FormHandlerMixin):
    model = AssayStudySet
    template_name = 'assays/assaystudyset_add.html'
    form_class = AssayStudySetForm

    formsets = (
        ('reference_formset', AssayStudySetReferenceFormSetFactory),
    )

    def get_context_data(self, **kwargs):
        context = super(AssayStudySetMixin, self).get_context_data(**kwargs)

        # FILTER OUT STUDIES WITH NO ASSAYS
        # PLEASE NOTE FILTER HERE
        combined = get_user_accessible_studies(self.request.user).filter(
            assaystudyassay__isnull=False
        )

        get_queryset_with_organ_model_map(combined)
        get_queryset_with_number_of_data_points(combined)
        get_queryset_with_stakeholder_sign_off(combined)
        get_queryset_with_group_center_dictionary(combined)

        context['object_list'] = combined

        context['reference_queryset'] = AssayReference.objects.all()

        return context

    def extra_form_processing(self, form):
        # Save the many-to-many fields
        form.save_m2m()


class AssayStudySetAdd(OneGroupRequiredMixin, AssayStudySetMixin, CreateView):
    pass


class AssayStudySetUpdate(CreatorOrSuperuserRequiredMixin, AssayStudySetMixin, UpdateView):
    pass


# class AssayStudySetAdd(OneGroupRequiredMixin, CreateView):
#     model = AssayStudySet
#     template_name = 'assays/assaystudyset_add.html'
#     form_class = AssayStudySetForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayStudySetAdd, self).get_context_data(**kwargs)
#
#         # FILTER OUT STUDIES WITH NO ASSAYS
#         # PLEASE NOTE FILTER HERE
#         combined = get_user_accessible_studies(self.request.user).filter(
#             assaystudyassay__isnull=False
#         )
#
#         get_queryset_with_organ_model_map(combined)
#         get_queryset_with_number_of_data_points(combined)
#         get_queryset_with_stakeholder_sign_off(combined)
#         get_queryset_with_group_center_dictionary(combined)
#
#         context['object_list'] = combined
#
#         if self.request.method == 'POST':
#             if 'reference_formset' not in context:
#                 context['reference_formset'] = AssayStudySetReferenceFormSetFactory(self.request.POST)
#         else:
#             context['reference_formset'] = AssayStudySetReferenceFormSetFactory()
#
#         context['reference_queryset'] = AssayReference.objects.all()
#
#         return context
#
#     def get_form(self, form_class=None):
#         form_class = self.get_form_class()
#
#         # If POST
#         if self.request.method == 'POST':
#             return form_class(self.request.POST, request=self.request)
#         # If GET
#         else:
#             return form_class(request=self.request)
#
#     def form_valid(self, form):
#         reference_formset = AssayStudySetReferenceFormSetFactory(
#             self.request.POST,
#             instance=form.instance
#         )
#
#         if form.is_valid() and reference_formset.is_valid():
#             save_forms_with_tracking(self, form, update=False, formset=[reference_formset])
#             form.save_m2m()
#             return redirect(
#                 self.object.get_absolute_url()
#             )
#         else:
#             return self.render_to_response(
#                 self.get_context_data(
#                     form=form
#                 )
#             )
#
#
# # TODO REFACTOR
# class AssayStudySetUpdate(CreatorAndNotInUseMixin, UpdateView):
#     model = AssayStudySet
#     template_name = 'assays/assaystudyset_add.html'
#     form_class = AssayStudySetForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayStudySetUpdate, self).get_context_data(**kwargs)
#
#         combined = get_user_accessible_studies(self.request.user)
#
#         get_queryset_with_organ_model_map(combined)
#         get_queryset_with_number_of_data_points(combined)
#         get_queryset_with_stakeholder_sign_off(combined)
#         get_queryset_with_group_center_dictionary(combined)
#
#         context['object_list'] = combined;
#
#         context['update'] = True
#
#         if self.request.method == 'POST':
#             if 'reference_formset' not in context:
#                 context['reference_formset'] = AssayStudySetReferenceFormSetFactory(self.request.POST, instance=self.object)
#         else:
#             context['reference_formset'] = AssayStudySetReferenceFormSetFactory(instance=self.object)
#
#         context['reference_queryset'] = AssayReference.objects.all()
#
#         return context
#
#     def get_form(self, form_class=None):
#         form_class = self.get_form_class()
#
#         # If POST
#         if self.request.method == 'POST':
#             return form_class(self.request.POST, instance=self.object, request=self.request)
#         # If GET
#         else:
#             return form_class(instance=self.object, request=self.request)
#
#     def form_valid(self, form):
#         reference_formset = AssayStudySetReferenceFormSetFactory(
#             self.request.POST,
#             instance=form.instance
#         )
#
#         if form.is_valid() and reference_formset.is_valid():
#             save_forms_with_tracking(self, form, formset=[reference_formset], update=True)
#             form.save_m2m()
#             return redirect(
#                 self.object.get_absolute_url()
#             )
#         else:
#             return self.render_to_response(
#                 self.get_context_data(
#                     form=form
#                 )
#             )


# TODO TO BE DEPRECATED
class AssayStudyAddNew(OneGroupRequiredMixin, AssayStudyMixin, CreateView):
    template_name = 'assays/assaystudy_add_new.html'
    form_class = AssayStudyForm

    template_name = 'assays/assaystudy_add.html'
    form_class = AssayStudyForm

    formsets = (
        ('study_assay_formset', AssayStudyAssayFormSetFactory),
        ('supporting_data_formset', AssayStudySupportingDataFormSetFactory),
        ('reference_formset', AssayStudyReferenceFormSetFactory),
    )

    # TODO TO BE REMOVED
    def get_context_data(self, **kwargs):
        context = super(AssayStudyAddNew, self).get_context_data(**kwargs)

        # Cellsamples will always be the same
        current_cellsamples = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        # TODO SLATED FOR REMOVAL
        context.update({
            'cellsamples': current_cellsamples,
            'reference_queryset': AssayReference.objects.all()
        })

        return context


    # Special handling for emailing on creation
    def extra_form_processing(self, form):
        # Contact superusers
        # Superusers to contact
        superusers_to_be_alerted = User.objects.filter(is_superuser=True, is_active=True)

        # Magic strings are in poor taste, should use a template instead
        superuser_subject = 'Study Created: {0}'.format(form.instance)
        superuser_message = render_to_string(
            'assays/email/superuser_study_created_alert.txt',
            {
                'study': form.instance
            }
        )

        for user_to_be_alerted in superusers_to_be_alerted:
            user_to_be_alerted.email_user(superuser_subject, superuser_message, DEFAULT_FROM_EMAIL)

        return super(AssayStudyAddNew, self).extra_form_processing(form)


# class AssayStudyAddNew(OneGroupRequiredMixin, CreateView):
#     """Add a study"""
#     template_name = 'assays/assaystudy_add_new.html'
#     form_class = AssayStudyFormNew
#
#     def get_form(self, form_class=None):
#         form_class = self.get_form_class()
#         # Get group selection possibilities
#         groups = filter_groups(self.request.user)
#
#         # If POST
#         if self.request.method == 'POST':
#             return form_class(
#                 self.request.POST,
#                 self.request.FILES,
#                 groups=groups,
#                 request=self.request
#             )
#         # If GET
#         else:
#             return form_class(groups=groups, request=self.request)
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayStudyAddNew, self).get_context_data(**kwargs)
#         if self.request.POST:
#             # Make the assumption that if one is missing, all are
#             if 'study_assay_formset' not in context:
#                 context['study_assay_formset'] = AssayStudyAssayFormSetFactory(self.request.POST)
#                 # context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(self.request.POST, self.request.FILES)
#         else:
#             context['study_assay_formset'] = AssayStudyAssayFormSetFactory()
#             # context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory()
#
#         # Cellsamples will always be the same
#         context['cellsamples'] = CellSample.objects.all().prefetch_related(
#             'cell_type__organ',
#             'supplier',
#             'cell_subtype__cell_type'
#         )
#
#         return context
#
#     def form_valid(self, form):
#         study_assay_formset = AssayStudyAssayFormSetFactory(
#             self.request.POST,
#             instance=form.instance
#         )
#         # supporting_data_formset = AssayStudySupportingDataFormSetFactory(
#         #     self.request.POST,
#         #     self.request.FILES,
#         #     instance=form.instance
#         # )
#         if form.is_valid() and study_assay_formset.is_valid():
#         # if form.is_valid() and study_assay_formset.is_valid() and supporting_data_formset.is_valid():
#             # save_forms_with_tracking(self, form, formset=[study_assay_formset, supporting_data_formset], update=False)
#             save_forms_with_tracking(self, form, formset=[study_assay_formset], update=False)
#             return redirect(
#                 self.object.get_absolute_url()
#             )
#         else:
#             return self.render_to_response(
#                 self.get_context_data(
#                     form=form,
#                     study_assay_formset=study_assay_formset,
#                     # supporting_data_formset=supporting_data_formset
#                 )
#             )


def user_is_valid_study_set_viewer(user_accessible_studies_dic, study_set):
    """Test whether a user can access a study set. The user must be able to access ALL groups in the study set.

    user_accessible_studies_dic: dic matching study_id to True if accessible by user
    study_set: The study set to test for the user
    """
    for study in study_set.studies.all():
        if study.id not in user_accessible_studies_dic:
            return False

    return True


# NOTE: TECHNICALLY SHOULD BE in MIXINS
class StudySetViewerMixin(object):
    """This mixin determines whether a user can view the study set and its data"""

    # @method_decorator(login_required)
    # @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        # Get the study
        study_set = get_object_or_404(AssayStudySet, pk=self.kwargs['pk'])

        user_accessible_studies = get_user_accessible_studies(self.request.user)

        user_accessible_studies_dic = {study.id: True for study in user_accessible_studies}

        valid_viewer = user_is_valid_study_set_viewer(user_accessible_studies_dic, study_set)
        # Deny permission
        if not valid_viewer:
            return PermissionDenied(self.request, 'You are missing the necessary credentials to view this Study Set.')
        # Otherwise return the view
        return super(StudySetViewerMixin, self).dispatch(*args, **kwargs)


class AssayStudySetDataPlots(StudySetViewerMixin, DetailView):
    model = AssayStudySet
    template_name = 'assays/assaystudyset_data_plots.html'


class AssayStudySetReproducibility(StudySetViewerMixin, DetailView):
    model = AssayStudySet
    template_name = 'assays/assaystudyset_reproducibility.html'


# The queryset for this will be somewhat complicated...
# TODO REVISE THE QUERYSET
class AssayStudySetList(ListView):
    model = AssayStudySet
    template_name = 'assays/assaystudyset_list.html'

    # NOTE CUSTOM QUERYSET
    def get_queryset(self):
        queryset = AssayStudySet.objects.prefetch_related(
            'created_by',
            'signed_off_by',
        )

        user_accessible_studies = get_user_accessible_studies(self.request.user)

        user_accessible_studies_dic = {study.id: True for study in user_accessible_studies}

        valid_study_set_ids = []

        # TODO TODO TODO RETRICT TO ONLY VALID ITERATIVELY
        for study_set in queryset:
            if user_is_valid_study_set_viewer(user_accessible_studies_dic, study_set):
                valid_study_set_ids.append(study_set.id)

        queryset = queryset.filter(id__in=valid_study_set_ids)

        return queryset


# TODO CONSIDER DISPATCH
class AssayStudySetData(DetailView):
    """Returns a combined file for all data in a study set"""
    model = AssayStudySet

    def render_to_response(self, context, **response_kwargs):
        # Make sure that the study exists, then continue
        if self.object:
            # TODO TODO TODO
            studies = get_user_accessible_studies(self.request.user).filter(id__in=self.object.studies.all())
            assays = self.object.assays.all()

            matrix_items = AssayMatrixItem.objects.filter(study_id__in=studies)

            matrix_items = matrix_items.filter(
                assaydatapoint__study_assay_id__in=assays
            ).distinct()

            # If chip data
            # Not particularly DRY
            data_points = AssayDataPoint.objects.filter(
                study_id__in=studies,
                study_assay_id__in=assays
            ).prefetch_related(
                # TODO
                'study__group__microphysiologycenter_set',
                'matrix_item__assaysetupsetting_set__setting',
                'matrix_item__assaysetupcell_set__cell_sample',
                'matrix_item__assaysetupcell_set__density_unit',
                'matrix_item__assaysetupcell_set__cell_sample__cell_type__organ',
                'matrix_item__assaysetupcompound_set__compound_instance__compound',
                'matrix_item__assaysetupcompound_set__concentration_unit',
                'matrix_item__device',
                'matrix_item__organ_model',
                'matrix_item__matrix',
                'study_assay__target',
                'study_assay__method',
                'study_assay__unit',
                'sample_location',
                # 'data_file_upload',
                # Will use eventually, maybe
                'subtarget'
            ).filter(
                replaced=False,
                excluded=False,
                value__isnull=False
            ).order_by(
                'matrix_item__name',
                'study_assay__target__name',
                'study_assay__method__name',
                'time',
                'sample_location__name',
                'excluded',
                'update_number'
            )

            data = get_data_as_csv(matrix_items, data_points=data_points, include_header=True)

            # For specifically text
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename=' + str(self.object) + '.csv'

            return response
        # Return nothing otherwise
        else:
            return HttpResponse('', content_type='text/plain')


class AssayReferenceList(ListView):
    model = AssayReference
    template_name = 'assays/assayreference_list.html'


class AssayReferenceMixin(FormHandlerMixin):
    model = AssayReference
    template_name = 'assays/assayreference_add.html'
    form_class = AssayReferenceForm


class AssayReferenceAdd(OneGroupRequiredMixin, AssayReferenceMixin, CreateView):
    pass


class AssayReferenceUpdate(CreatorOrSuperuserRequiredMixin, AssayReferenceMixin, UpdateView):
    pass

# class AssayReferenceAdd(OneGroupRequiredMixin, CreateView):
#     model = AssayReference
#     template_name = 'assays/assayreference_add.html'
#     form_class = AssayReferenceForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayReferenceAdd, self).get_context_data(**kwargs)
#         context['update'] = False
#         return context
#
#     def form_valid(self, form):
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=[], update=False)
#             return redirect(self.object.get_post_submission_url())
#         else:
#             return self.render_to_response(self.get_context_data(form=form))


class AssayReferenceDetail(DetailView):
    model = AssayReference
    template_name = 'assays/assayreference_detail.html'


# class AssayReferenceUpdate(CreatorAndNotInUseMixin, UpdateView):
#     model = AssayReference
#     template_name = 'assays/assayreference_add.html'
#     form_class = AssayReferenceForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayReferenceUpdate, self).get_context_data(**kwargs)
#         context['update'] = True
#         return context
#
#     def form_valid(self, form):
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=[], update=True)
#             return redirect(self.object.get_post_submission_url())
#         else:
#             return self.render_to_response(self.get_context_data(form=form))


class AssayReferenceDelete(CreatorAndNotInUseMixin, DeleteView):
    """Delete a Reference"""
    model = AssayReference
    template_name = 'assays/assayreference_delete.html'
    success_url = '/assays/assayreference/'


class AssayStudyPowerAnalysisStudy(StudyViewerMixin, DetailView):
    """Displays the power analysis interface for the current study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_power_analysis_study.html'


class AssayMatrixNew(HistoryMixin, StudyGroupMixin, UpdateView):
    """Show all chip and plate models associated with the given study"""
    model = AssayMatrix
    template_name = 'assays/assaymatrix_update.html'
    form_class = AssayMatrixFormNew

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # Get the study
        study = self.object.study

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, instance=self.object, user=self.request.user)
        # If GET
        else:
            return form_class(instance=self.object, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(AssayMatrixNew, self).get_context_data(**kwargs)

        # Cellsamples will always be the same
        context['cellsamples'] = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        # context['formset'] = AssayMatrixItemFormSetFactory(instance=self.object)

        matrix_item_queryset = AssayMatrixItem.objects.filter(
            matrix_id=self.object.id
        ).order_by(
            'row_index',
            'column_index'
        )
        # ).prefetch_related(
        #     'device'
        # )

        # TODO SORTING CAN MAKE SURE THAT THE FORMS APPEAR IN THE RIGHT ORDER, BUT DECREASE PERFORMANCE
        compound_queryset = AssaySetupCompound.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        cell_queryset = AssaySetupCell.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        setting_queryset = AssaySetupSetting.objects.filter(
            matrix_item__in=matrix_item_queryset
        )

        if self.request.POST:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                self.request.POST,
                instance=self.object,
                queryset=matrix_item_queryset,
                prefix='matrix_item',
                user=self.request.user
            )
            context['compound_formset'] = AssaySetupCompoundFormSetFactory(
                self.request.POST,
                queryset=compound_queryset,
                matrix=self.object,
                prefix='compound'
            )
            context['cell_formset'] = AssaySetupCellFormSetFactory(
                self.request.POST,
                queryset=cell_queryset,
                matrix=self.object,
                prefix='cell'
            )
            context['setting_formset'] = AssaySetupSettingFormSetFactory(
                self.request.POST,
                queryset=setting_queryset,
                matrix=self.object,
                prefix='setting'
            )
        else:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                instance=self.object,
                queryset=matrix_item_queryset,
                prefix='matrix_item',
                user=self.request.user
            )
            context['compound_formset'] = AssaySetupCompoundFormSetFactory(
                queryset=compound_queryset,
                matrix=self.object,
                prefix='compound'
            )
            context['cell_formset'] = AssaySetupCellFormSetFactory(
                queryset=cell_queryset,
                matrix=self.object,
                prefix='cell'
            )
            context['setting_formset'] = AssaySetupSettingFormSetFactory(
                queryset=setting_queryset,
                matrix=self.object,
                prefix='setting'
            )

        context['update'] = True

        return context

    def form_valid(self, form):
        # formset = AssayMatrixItemFormSetFactory(self.request.POST, instance=self.object)
        matrix_item_queryset = AssayMatrixItem.objects.filter(matrix=self.object).order_by('row_index', 'column_index')

        item_formset = AssayMatrixItemFormSetFactory(
            self.request.POST,
            instance=self.object,
            queryset=matrix_item_queryset,
            prefix='matrix_item',
            user=self.request.user
        )
        # Order no longer matters really
        compound_formset = AssaySetupCompoundFormSetFactory(
            self.request.POST,
            queryset=AssaySetupCompound.objects.filter(
                matrix_item__in=matrix_item_queryset
            ),
            matrix=self.object,
            prefix='compound'
        )
        cell_formset = AssaySetupCellFormSetFactory(
            self.request.POST,
            queryset=AssaySetupCell.objects.filter(
                matrix_item__in=matrix_item_queryset
            ),
            matrix=self.object,
            prefix='cell'
        )
        setting_formset = AssaySetupSettingFormSetFactory(
            self.request.POST,
            queryset=AssaySetupSetting.objects.filter(
                matrix_item__in=matrix_item_queryset
            ),
            matrix=self.object,
            prefix='setting'
        )

        formsets = [
            item_formset,
            compound_formset,
            cell_formset,
            setting_formset
        ]

        formsets_are_valid = True

        for formset in formsets:
            if not formset.is_valid():
                formsets_are_valid = False

        if form.is_valid() and formsets_are_valid:
            save_forms_with_tracking(self, form, formset=formsets, update=True)

            # Sloppy addition of logging
            change_message = 'Modified'
            self.log_change(self.request, self.object, change_message)

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class CreatorAndNotInUseOrRestrictedMixin(object):
    """This mixin redirects to a divergent edit page for restricted edits when possible"""

    restricted_string_append = 'restricted/'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        # Superusers always have access
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return super(CreatorAndNotInUseOrRestrictedMixin, self).dispatch(*args, **kwargs)

        # The user needs at least one group
        # This should be handled after the redirect
        # valid_groups = filter_groups(self.request.user)
        # if not valid_groups:
        #     return PermissionDenied(self.request, 'You must be a member of at least one group')

        self.object = self.get_object()

        use_restricted_mode = False

        # Check if this is the creator
        if self.request.user.id != self.object.created_by_id:
            use_restricted_mode = True

        # relations_to_check = {
        #     "<class 'django.db.models.fields.reverse_related.ManyToOneRel'>": True,
        #     "<class 'django.db.models.fields.reverse_related.ManyToOneRel'>": True,
        # }

        if not use_restricted_mode:
            for current_field in self.object._meta.get_fields():
                # TODO MODIFY TO CHECK M2M MANAGERS IN THE FUTURE
                # TODO REVISE
                # if str(type(current_field)) in relations_to_check:
                if str(type(current_field)) == "<class 'django.db.models.fields.reverse_related.ManyToOneRel'>":
                    manager = getattr(self.object, current_field.name + '_set', '')
                    if manager:
                        count = manager.count()
                        if count > 0:
                            use_restricted_mode = True
                            break

        # TODO TODO HOW DO WE DO THE REDIRECT?
        if use_restricted_mode:
            return redirect(
                # Contrived, add restricted/ to perform the redirect
                # REALLY: this should be a reverse
                '{}{}'.format(self.request.path, self.restricted_string_append)
            )

        return super(CreatorAndNotInUseOrRestrictedMixin, self).dispatch(*args, **kwargs)


# REVIEW PERMISSIONS
class AssayTargetMixin(FormHandlerMixin):
    model = AssayTarget
    form_class = AssayTargetForm

    # templates_need_to_be_modified = False

    # def pre_save_processing(self, form):
    #     """For dealing with new targets/changing names"""
    #     # Modify templates immediately if new
    #     if not self.object or not self.object.id:
    #         self.templates_need_to_be_modified = True
    #     elif self.object.name != form.cleaned_data.get('name', ''):
    #         self.templates_need_to_be_modified = True
    #     elif self.object.short_name != form.cleaned_data.get('short_name', ''):
    #         self.templates_need_to_be_modified = True

    # def extra_form_processing(self):
    #     if self.templates_need_to_be_modified:
    #         modify_templates()

class AssayTargetAdd(OneGroupRequiredMixin, AssayTargetMixin, CreateView):
    pass


class AssayTargetUpdate(CreatorAndNotInUseOrRestrictedMixin, AssayTargetMixin, UpdateView):
    pass


class AssayTargetUpdateRestricted(OneGroupRequiredMixin, AssayTargetMixin, UpdateView):
    # Use the restricted form instead
    form_class = AssayTargetRestrictedForm


class AssayTargetList(ListView):
    model = AssayTarget
    template_name = 'assays/assaytarget_list.html'


class AssayTargetDetail(DetailView):
    model = AssayTarget
    template_name = 'assays/assaytarget_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AssayTargetDetail, self).get_context_data(**kwargs)
        context['assays'] = AssayStudyAssay.objects.filter(
            target__name__icontains=self.object.name
        ).values_list("method__name", "method_id", "method__description").distinct()
        context['images'] = AssayImage.objects.filter(
            target__name__icontains=self.object.name
        ).values_list("method__name", "method_id", "method__description").distinct()
        context['studies'] = get_user_accessible_studies(
            self.request.user
        ).filter(
            assaystudyassay__target__name=self.object.name
        ).distinct() | get_user_accessible_studies(
            self.request.user
        ).filter(
            assayimagesetting__assayimage__target__name=self.object.name
        ).distinct()

        return context


class AssayMethodMixin(FormHandlerMixin):
    model = AssayMethod
    form_class = AssayMethodForm

    # templates_need_to_be_modified = False

    # def pre_save_processing(self, form):
    #     """For dealing with new targets/changing names"""
    #     # Modify templates immediately if new
    #     if not self.object or not self.object.id:
    #         self.templates_need_to_be_modified = True
    #     elif self.object.name != form.cleaned_data.get('name', ''):
    #         self.templates_need_to_be_modified = True

    # def extra_form_processing(self):
    #     if self.templates_need_to_be_modified:
    #         modify_templates()


class AssayMethodAdd(OneGroupRequiredMixin, AssayMethodMixin, CreateView):
    pass


class AssayMethodUpdate(CreatorAndNotInUseOrRestrictedMixin, AssayMethodMixin, UpdateView):
    pass


class AssayMethodUpdateRestricted(OneGroupRequiredMixin, AssayMethodMixin, UpdateView):
    # Use the restricted form instead
    form_class = AssayMethodRestrictedForm


class AssayMethodList(ListView):
    model = AssayMethod
    template_name = 'assays/assaymethod_list.html'

    def get_queryset(self):
        queryset = AssayMethod.objects.all().prefetch_related(
            'supplier',
            'measurement_type'
        )

        return queryset


class AssayMethodDetail(DetailView):
    model = AssayMethod
    template_name = 'assays/assaymethod_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AssayMethodDetail, self).get_context_data(**kwargs)
        context['assays'] = AssayStudyAssay.objects.filter(
            method__name__icontains=self.object.name
        ).values_list("target__name", "target_id", "target__description", "target__short_name").distinct()
        context['images'] = AssayImage.objects.filter(
            method__name__icontains=self.object.name
        ).values_list("target__name", "target_id", "target__description", "target__short_name").distinct()
        context['studies'] = get_user_accessible_studies(
            self.request.user
        ).filter(
            assaystudyassay__method__name=self.object.name
        ).distinct() | get_user_accessible_studies(
            self.request.user
        ).filter(
            assayimagesetting__assayimage__method__name=self.object.name
        ).distinct()
        return context


# class UnitTypeMixin(FormHandlerMixin):
#     model = UnitType
#     form_class = UnitTypeForm
#
#
# class UnitTypeAdd(OneGroupRequiredMixin, UnitTypeMixin, CreateView):
#     pass
#
#
# class UnitTypeUpdate(OneGroupRequiredMixin, UnitTypeMixin, UpdateView):
#     pass


# Unpleasant name
class PhysicalUnitsMixin(FormHandlerMixin):
    model = PhysicalUnits
    form_class = PhysicalUnitsForm

    # templates_need_to_be_modified = False

    # def pre_save_processing(self, form):
    #     """For dealing with new targets/changing names"""
    #     # Modify templates immediately if new
    #     if not self.object or not self.object.id:
    #         self.templates_need_to_be_modified = True
    #     # NOTE THIS DOES NOT USE NAME
    #     # elif self.object.name != form.cleaned_data.get('name', ''):
    #     elif self.object.unit != form.cleaned_data.get('unit', ''):
    #         self.templates_need_to_be_modified = True

    # def extra_form_processing(self):
    #     if self.templates_need_to_be_modified:
    #         modify_templates()


class PhysicalUnitsAdd(OneGroupRequiredMixin, PhysicalUnitsMixin, CreateView):
    pass


class PhysicalUnitsUpdate(CreatorAndNotInUseMixin, PhysicalUnitsMixin, UpdateView):
    pass


class PhysicalUnitsDetail(DetailView):
    pass


class PhysicalUnitsList(ListView):
    model = PhysicalUnits
    template_name = 'assays/assayunit_list.html'

    def get_queryset(self):
        queryset = PhysicalUnits.objects.all().prefetch_related(
            'unit_type',
            'base_unit'
        )

        return queryset


class AssayMeasurementTypeMixin(FormHandlerMixin):
    model = AssayMeasurementType
    form_class = AssayMeasurementTypeForm


class AssayMeasurementTypeAdd(OneGroupRequiredMixin, AssayMeasurementTypeMixin, CreateView):
    pass


class AssayMeasurementTypeUpdate(CreatorAndNotInUseMixin, AssayMeasurementTypeMixin, UpdateView):
    pass


class AssayMeasurementTypeDetail(AssayMeasurementTypeMixin, DetailView):
    pass


class AssayMeasurementTypeList(ListHandlerMixin, ListView):
    model = AssayMeasurementType


class AssaySampleLocationMixin(FormHandlerMixin):
    model = AssaySampleLocation
    form_class = AssaySampleLocationForm

    # templates_need_to_be_modified = False

    # def pre_save_processing(self, form):
    #     """For dealing with new targets/changing names"""
    #     # Modify templates immediately if new
    #     if not self.object or not self.object.id:
    #         self.templates_need_to_be_modified = True
    #     elif self.object.name != form.cleaned_data.get('name', ''):
    #         self.templates_need_to_be_modified = True

    # def extra_form_processing(self):
    #     if self.templates_need_to_be_modified:
    #         modify_templates()


class AssaySampleLocationAdd(OneGroupRequiredMixin, AssaySampleLocationMixin, CreateView):
    pass


class AssaySampleLocationUpdate(CreatorAndNotInUseMixin, AssaySampleLocationMixin, UpdateView):
    pass


# TODO: PERHAPS THIS SHOULD NOT BE HERE
class AssaySampleLocationList(ListHandlerMixin, ListView):
    model = AssaySampleLocation
    # template_name = 'assays/assaylocation_list.html'


class AssaySettingMixin(FormHandlerMixin):
    model = AssaySetting
    form_class = AssaySettingForm


class AssaySettingAdd(OneGroupRequiredMixin, AssaySettingMixin, CreateView):
    pass


class AssaySettingUpdate(CreatorAndNotInUseMixin, AssaySettingMixin, UpdateView):
    pass


class AssaySettingDetail(AssaySettingMixin, DetailView):
    pass


class AssaySettingList(ListHandlerMixin, ListView):
    model = AssaySetting


class AssaySupplierMixin(FormHandlerMixin):
    model = AssaySupplier
    form_class = AssaySupplierForm


class AssaySupplierAdd(OneGroupRequiredMixin, AssaySupplierMixin, CreateView):
    pass


class AssaySupplierUpdate(CreatorAndNotInUseMixin, AssaySupplierMixin, UpdateView):
    pass


class AssaySupplierDetail(DetailView):
    pass


class AssaySupplierList(ListHandlerMixin, ListView):
    model = AssaySupplier


def get_component_display_for_model(model):
    return {
        'verbose_name': model._meta.verbose_name,
        'verbose_name_plural': model._meta.verbose_name_plural,
        'list_url': model.get_list_url(),
        'add_url': model.get_add_url()
    }


class AssayStudyComponents(TemplateView):
    template_name = 'assays/assaystudycomponents.html'

    def get_context_data(self, **kwargs):
        context = super(AssayStudyComponents, self).get_context_data(**kwargs)

        # Adds the word "editable" to the page
        context.update({
            'assay_components': [
                get_component_display_for_model(x) for x in
                [
                    AssayTarget.objects.first(),
                    AssayMethod.objects.first(),
                    AssayMeasurementType.objects.first(),
                    PhysicalUnits.objects.first(),
                    AssaySampleLocation.objects.first(),
                    AssaySetting.objects.first(),
                    AssaySupplier.objects.first(),
                    AssayReference.objects.first(),
                ]
            ],
            'model_components': [
                get_component_display_for_model(x) for x in
                [
                    apps.get_model(app_label='microdevices', model_name='microdevice').objects.first(),
                    apps.get_model(app_label='microdevices', model_name='organmodel').objects.first(),
                    # Note that sample location is more accurately placed here
                    AssaySampleLocation.objects.first(),
                    apps.get_model(app_label='microdevices', model_name='manufacturer').objects.first(),
                ]
            ],
            # NOTE WE COULD, IF WE WANTED, ADD COMPOUND SUPPLIER HERE
            'compound_components': [
                get_component_display_for_model(x) for x in
                [
                    apps.get_model(app_label='compounds', model_name='compound').objects.first(),
                ]
            ],
            'cell_components': [
                get_component_display_for_model(x) for x in
                [
                    apps.get_model(app_label='cellsamples', model_name='celltype').objects.first(),
                    apps.get_model(app_label='cellsamples', model_name='cellsubtype').objects.first(),
                    apps.get_model(app_label='cellsamples', model_name='cellsample').objects.first(),
                    apps.get_model(app_label='cellsamples', model_name='biosensor').objects.first(),
                    apps.get_model(app_label='cellsamples', model_name='supplier').objects.first(),
                ]
            ],
        })

        return context


def get_current_upload_template(request):
    # The workbook is just in memory
    current_output = io.BytesIO()
    current_template = xlsxwriter.Workbook(current_output)

    current_sheet = current_template.add_worksheet('Sheet 1')

    # Set up formats
    chip_red = current_template.add_format()
    chip_red.set_bg_color('#ff6f69')
    chip_green = current_template.add_format()
    chip_green.set_bg_color('#96ceb4')

    # Write the base files
    # Some danger here, must change this and other template
    initial = [
        DEFAULT_CSV_HEADER,
        [
            # Chip ID
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            # Target
            None,
            None,
            # Method
            None,
            # Sample
            None,
            None,
            # Value Unit
            None,
            None,
            None,
            None,
            None
        ]
    ]

    # Set the initial values

    initial_format = [
        [chip_red] * 17,
        [
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            chip_green,
            None,
            chip_green,
            chip_green,
            None,
            chip_green,
            None,
            None,
            None,
            None
        ]
    ]

    # Write out initial
    for row_index, row in enumerate(initial):
        for column_index, column in enumerate(row):
            cell_format = initial_format[row_index][column_index]
            current_sheet.write(row_index, column_index, column, cell_format)

    # Set column widths
    # Chip
    current_sheet.set_column('A:A', 20)
    current_sheet.set_column('B:B', 20)
    current_sheet.set_column('C:C', 20)
    current_sheet.set_column('D:D', 15)
    current_sheet.set_column('E:E', 10)
    current_sheet.set_column('F:F', 10)
    current_sheet.set_column('G:G', 10)
    current_sheet.set_column('H:H', 20)
    current_sheet.set_column('I:I', 10)
    current_sheet.set_column('J:J', 20)
    current_sheet.set_column('K:K', 15)
    current_sheet.set_column('L:L', 10)
    current_sheet.set_column('M:M', 10)
    current_sheet.set_column('N:N', 10)
    current_sheet.set_column('O:O', 10)
    current_sheet.set_column('P:P', 10)
    current_sheet.set_column('Q:Q', 100)
    # chip_sheet.set_column('I:I', 20)
    # chip_sheet.set_column('J:J', 15)
    # chip_sheet.set_column('K:K', 10)
    # chip_sheet.set_column('L:L', 10)
    # chip_sheet.set_column('M:M', 10)
    # chip_sheet.set_column('N:N', 10)
    # chip_sheet.set_column('O:O', 10)
    # chip_sheet.set_column('P:P', 100)

    current_sheet.set_column('BA:BD', 30)

    # Get list of value units  (TODO CHANGE ORDER_BY)
    value_units = PhysicalUnits.objects.all().order_by(
        'base_unit__unit',
        'scale_factor'
    ).values_list('unit', flat=True)

    # List of targets
    targets = AssayTarget.objects.all().order_by(
        'name'
    ).values_list('name', flat=True)

    # List of methods
    methods = AssayMethod.objects.all().order_by(
        'name'
    ).values_list('name', flat=True)

    # List of sample locations
    sample_locations = AssaySampleLocation.objects.all().order_by(
        'name'
    ).values_list('name', flat=True)

    for index, value in enumerate(sample_locations):
        current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX + 3, value)

    for index, value in enumerate(methods):
        current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX + 2, value)

    for index, value in enumerate(value_units):
        current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX + 1, value)

    for index, value in enumerate(targets):
        current_sheet.write(index, TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX, value)

    value_units_range = '=$BB$1:$BB$' + str(len(value_units))

    targets_range = '=$BA$1:$BA$' + str(len(targets))
    methods_range = '=$BC$1:$BC$' + str(len(methods))
    sample_locations_range = '=$BD$1:$BD$' + str(len(sample_locations))


    current_sheet.data_validation('H2', {'validate': 'list',
                                        'source': targets_range})
    current_sheet.data_validation('J2', {'validate': 'list',
                                'source': methods_range})
    current_sheet.data_validation('K2', {'validate': 'list',
                                'source': sample_locations_range})
    current_sheet.data_validation('M2', {'validate': 'list',
                                'source': value_units_range})

    current_template.close()

    # Return
    # Set response to binary
    # For xlsx
    response = HttpResponse(current_output.getvalue(), content_type='application/ms-excel')
    # response['Content-Disposition'] = 'attachment;filename="UploadTemplate-' + str() + '.xlsx"'
    response['Content-Disposition'] = 'attachment;filename="MPSUploadTemplate.xlsx"'

    return response


class PBPKFilterView(TemplateView):
    template_name = 'assays/assay_pbpk_filter.html'


class PBPKView(TemplateView):
    template_name = 'assays/assay_pbpk.html'


#####
# sck - ASSAY PLATE MAP START

# Plate map list, add, update, view and delete section
class AssayPlateReaderMapIndex(StudyViewerMixin, DetailView):
    """Assay plate map index (list) page class """
    model = AssayStudy
    context_object_name = 'assayplatereadermap_index'
    template_name = 'assays/assayplatereadermap_index.html'

    # For permission mixin
    def get_object(self, queryset=None):
        self.study = super(AssayPlateReaderMapIndex, self).get_object()
        return self.study

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapIndex, self).get_context_data(**kwargs)
        #####
        context['index'] = True
        context['page_called'] = 'index'
        #####

        # get maps
        assayplatereadermaps = AssayPlateReaderMap.objects.filter(
            study=self.object.id
        ).prefetch_related(
            'assayplatereadermapitem_set',
        )
        # print(assayplatereadermaps)

        # find block count per map id
        file_block_count = AssayPlateReaderMapDataFileBlock.objects.filter(
            study=self.object.id
        ).exclude(
            assayplatereadermap__exact=None
        ).values('assayplatereadermap').annotate(
            blocks=Count('assayplatereadermap')
        )
        # print(file_block_count)

        # get block count to a dictionary (the iterator is for single use of the query - optional)
        file_block_count_dict = {}
        # for each in file_block_count.iterator():
        # b = 0
        for each in file_block_count:
            # print("B ", b)
            # print("map ", each.get('assayplatereadermap'))
            # print("block ", each.get('blocks'))
            file_block_count_dict.update({each.get('assayplatereadermap'): each.get('blocks')})
            # b = b + 1

        # put the count of the blocks into the queryset of platemaps (this is very HANDY)
        for file in assayplatereadermaps:
            file.block_count = file_block_count_dict.get(int(file.id))
            # print("block added to queryset: ", file.id, " ",file.description, " ", file.block_count)

        # file count per map id
        file_file = AssayPlateReaderMapDataFileBlock.objects.filter(
            study=self.object.id
        ).exclude(
            assayplatereadermap__exact=None
        ).order_by('assayplatereadermap', 'assayplatereadermapdatafile')
        #  this will show <AssayPlateReaderMapDataFileBlock: 3>, for each file block with a plate map
        # print("file_file")
        # print(file_file)

        file_count_dict = {}
        counter = 1
        # get the first file so do not need to include in loop
        # set the variables for the first in the file block list
        # slice to get the 0ith in the queryset
        for each in file_file[:1]:
            previous_map = each.assayplatereadermap.id
            previous_file = each.assayplatereadermapdatafile.id
            me_map = each.assayplatereadermap.id
            # print("each ", each)
            # print("previous_map ", previous_map)
            # print("previous_file ", previous_file)
            # each
            # 1
            # previous_map
            # 89
            # previous_file
            # 151
            # the one found in the 0ith place of the queryset will always count, so add it!
            file_count_dict.update({me_map: 1})
            counter = counter + 1

        # the one found in the 0ith place of the queryset will always count, so start at 1
        files_this_map = 1
        counter = 1
        # iterate through the queryset from the second to the end
        # note: first (0ith) is excluded
        for each in file_file[1:]:
            # print("C ", counter)
            me_map = each.assayplatereadermap.id
            me_file = each.assayplatereadermapdatafile.id

            # print("previous_map ", previous_map)
            # print("me_map ", me_map)
            # print("previous_file ", previous_file)
            # print("me_file ", me_file)

            if previous_map == me_map and previous_file != me_file:
                # same map, different file, add a file
                files_this_map = files_this_map + 1
                # print("files same map ", files_this_map)
            elif previous_map != me_map:
                # different map - do not care if same or different file - start the count over
                files_this_map = 1
                # print("files reset ", files_this_map)
            else:
                # both same, nothing to do
                pass

            # remember, since a dict, will just keep replacing the count for each plate map
            file_count_dict.update({me_map: files_this_map})
            previous_map = me_map
            previous_file = me_file
            counter = counter + 1

        # print("dict: ", file_count_dict)

        for file in assayplatereadermaps:
            file.file_count = file_count_dict.get(int(file.id))
            # print(file.id, " ", file.description, " ", file.file_count)

        for file in assayplatereadermaps:
            my_tmu = str(file.study_assay)
            my_tmu_list = my_tmu.split("~@|")
            if len(my_tmu_list) > 2:
                file.new_study_assay = "TARGET: "+my_tmu_list[1]+"  METHOD: "+my_tmu_list[2]+"  UNIT: "+my_tmu_list[3]
            else:
                file.new_study_assay = file.study_assay

        # print(assayplatereadermaps)

        context['assayplatereadermaps'] = assayplatereadermaps

        # not using this right now, but KEEP here for now in case need to add to the index page
        # assayplatereadermapitems = AssayPlateReaderMapItem.objects.filter(
        #     assayplatereadermap__in=assayplatereadermaps
        # )
        # context['assayplatereaderitems'] = assayplatereadermapitems

        return context


class AssayPlateReaderMapAdd(StudyGroupMixin, CreateView):
    """Assay plate map add"""

    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_add.html'
    form_class = AssayPlateReaderMapForm

    # used in ADD, not same in UPDATE - check carefully if copy - changing, use partial in update
    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, study=study)
        else:
            return form_class(study=study)

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapAdd, self).get_context_data(**kwargs)
        #####
        context['add'] = True
        context['page_called'] = 'add'
        #####

        # pass the study_id to ADDITIONAL form as call it
        context['assay_map_additional_info'] = AssayPlateReadMapAdditionalInfoForm(study_id=self.kwargs['study_id'])
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        # get the items (one for each well in the plate)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = AssayPlateReaderMapItemFormSetFactory(
                    self.request.POST,
                    study=study,
                    user=self.request.user
                )
            else:
                context['formset'] = AssayPlateReaderMapItemFormSetFactory(
                    study=study,
                    user=self.request.user
                )

        # 20200522 getting rid of the value formset in the plate map form
        # # get the values (0 to many for each item)
        # if 'value_formset' not in context:
        #     if self.request.POST:
        #         context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
        #             self.request.POST,
        #             study=study,
        #             user=self.request.user
        #         )
        #     else:
        #         context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
        #             study=study,
        #             user=self.request.user
        #         )

        # this sends the info needed for display of setup info in the plate map
        # this function used by add, update, and edit
        # note to sck - sending para||el lists

        # move to ajax for performance reasons
        # return_list = get_matrix_item_information_for_plate_map(self.kwargs['study_id'])
        # matrix_items_in_study = return_list[0]
        # matrix_list_size = return_list[1]
        # matrix_list_pk = return_list[2]
        # context['matrix_items_in_study'] = matrix_items_in_study
        # context['matrix_list_size'] = matrix_list_size
        # context['matrix_list_pk'] = matrix_list_pk

        # return_list = get_matrix_item_information_for_plate_map(study_id=self.kwargs['study_id'])
        # context['matrix_list_size'] = return_list[0]
        # context['matrix_list_pk'] = return_list[1]
        # context['matrix_column_size'] = return_list[2]
        # print("add context")
        return context

    def form_valid(self, form):
        # print("a")
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])
        formset = AssayPlateReaderMapItemFormSetFactory(
            self.request.POST,
            instance=form.instance,
            study=study
        )

        # 20200522 getting rid of the value formset in the plate map form
        # print("b")
        # this is the add page, so yes, we want to call the value_formset
        # value_formset = AssayPlateReaderMapItemValueFormSetFactory(
        #     self.request.POST,
        #     instance=form.instance,
        #     study=study
        # )
        # formsets = [formset, value_formset, ]

        formsets = [formset, ]
        formsets_are_valid = True

        # print("c")
        for formset in formsets:
            if not formset.is_valid():
                formsets_are_valid = False

        # print("d")
        if form.is_valid() and formsets_are_valid:
            save_forms_with_tracking(self, form, formset=formsets, update=False)


            # 20200522 getting rid of the value formset in the plate map form
            # # ONLY NEED if ADD - START
            # # because the instances of the item do not yet exist, the pk from item can not be added to value on save
            # # so, in the ADD, formsets are saved, add the pk of the item table to the value table
            # # note that, these protect from a break in || between plate_index in item and item value
            # # specify where null so it ONLY happens to the first time adding
            # # This could perhaps be avoided by nesting forms....
            # this_platemap_id = form.instance.id
            # v = 'assays_assayplatereadermapitemvalue'
            # i = 'assays_assayplatereadermapitem'
            # c1 = 'assayplatereadermapitem_id'
            # c2 = 'id'
            # c3 = 'assayplatereadermap_id'
            # w1 = 'plate_index'
            # mysql = ""
            # mysql = mysql + "UPDATE " + v + " "
            # mysql = mysql + "SET " + c1 + " = " + i + "." + c2 + " "
            # mysql = mysql + "FROM " + i + " "
            # mysql = mysql + "WHERE " + i + "." + w1 + "=" + v + "." + w1 + " "
            # mysql = mysql + "AND " + v + "." + c3 + "=" + str(this_platemap_id) + " "
            # mysql = mysql + "AND " + v + "." + c1 + " is null"
            # # print(mysql)
            # cursor = connection.cursor()
            # cursor.execute(mysql)
            # # ONLY NEED if ADD - END
            # # print("e")

            return redirect(self.object.get_post_submission_url())
        else:
            # print("f")
            # return this for ADD
            return self.render_to_response(self.get_context_data(form=form))
            # return this for UPDATE or VIEW
            # return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayPlateReaderMapUpdate(StudyGroupMixin, UpdateView):
    """Assay plate map update"""

    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_add.html'
    form_class = AssayPlateReaderMapForm

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])
        study = self.object.study
        # print("study ", study)
        # print("study_id ", study.id)
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, instance=self.object, study=study, user=self.request.user)
        else:
            return form_class(instance=self.object, study=study, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapUpdate, self).get_context_data(**kwargs)
        #####
        context['update'] = True
        context['page_called'] = 'update'
        #####

        # using the form field for conditional logic was making the query file multiple times
        # let's just send a boolean
        block_combos = AssayPlateReaderMapItemValue.objects.filter(
            assayplatereadermap=self.object
        ).prefetch_related(
            'assayplatereadermapitem',
        ).filter(
            assayplatereadermapitem__plate_index=0
        ).filter(
            assayplatereadermapdatafileblock__isnull=False
        )
        if len(block_combos) > 0:
            data_attached = True
        else:
            data_attached = False
        context['data_attached'] = data_attached

        # Always acquire map_additional_info
        context['assay_map_additional_info'] = AssayPlateReadMapAdditionalInfoForm(study_id=self.object.study_id)

        # print("calling formset")
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = AssayPlateReaderMapItemFormSetFactory(
                        self.request.POST,
                        instance=self.object,
                        user=self.request.user
                )
            else:
                context['formset'] = AssayPlateReaderMapItemFormSetFactory(
                    instance=self.object,
                    user=self.request.user
                )

        # 20200522 getting rid of the value formset in the plate map form
        # # adding 20200113
        # value_formsets_include_template = AssayPlateReaderMapItemValue.objects.filter(
        #     assayplatereadermap=self.object
        # ).filter(
        #     plate_index=0
        # )
        # # one is the empty set (no file/block attached) - the template value set
        # if len(value_formsets_include_template) == 1:
        #
        #     if 'value_formset' not in context:
        #         if self.request.POST:
        #             context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
        #                     self.request.POST,
        #                     instance=self.object,
        #                     user=self.request.user
        #             )
        #         else:
        #             context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
        #                 instance=self.object,
        #                 user=self.request.user
        #             )
        # else:
        #     context['value_formset'] = "None"
        # # end update fo 20200113


        # print("back")
        # move to ajax for performance reasons
        # return_list = get_matrix_item_information_for_plate_map(self.object.study_id)
        # matrix_items_in_study = return_list[0]
        # matrix_list_size = return_list[1]
        # matrix_list_pk = return_list[2]
        # context['matrix_items_in_study'] = matrix_items_in_study
        # context['matrix_list_size'] = matrix_list_size
        # context['matrix_list_pk'] = matrix_list_pk

        # print("formset")
        # print(len(context['formset']))
        # print("value_formset")
        # print(len(context['value_formset']))

        # print("calling matrix return")
        # return_list = get_matrix_item_information_for_plate_map(self.object.study_id)
        # context['matrix_list_size'] = return_list[0]
        # context['matrix_list_pk'] = return_list[1]
        # context['matrix_column_size'] = return_list[2]
        # print("returning context map update")

        return context

    def form_valid(self, form):
        formset = AssayPlateReaderMapItemFormSetFactory(
            self.request.POST,
            instance=self.object
        )

        # 20200522 getting rid of the value formset in the plate map form
        # # adding 20200113
        # value_formsets_include_template = AssayPlateReaderMapItemValue.objects.filter(
        #     assayplatereadermap=self.object
        # ).filter(
        #     plate_index=0
        # )
        # # one is the empty set (no file/block attached) - the template value set
        # if len(value_formsets_include_template) == 1:
        #
        #     value_formset = AssayPlateReaderMapItemValueFormSetFactory(
        #         self.request.POST,
        #         instance=self.object
        #     )
        #     formsets = [formset, value_formset, ]
        #     formsets_are_valid = True
        # else:
        #     formsets = [formset, ]
        #     formsets_are_valid = True
        # # end update of 20200113

        formsets = [formset, ]
        formsets_are_valid = True

        for formset in formsets:
            if not formset.is_valid():
                formsets_are_valid = False

        if form.is_valid() and formset.is_valid():
            # name = form.cleaned_data.get('name')
            # print(name)
            # form_calibration_curve_method_used = form.cleaned_data.get('form_calibration_curve_method_used')
            # print("form_calibration_curve_method_used ", form_calibration_curve_method_used)


            # MOVING BACK TO FORMS.PY
            # #### START When saving AssayPlateReaderMapUpdate after a calibration
            # # if user checked the box to send to study summary, make that happen
            #
            # data = form.cleaned_data
            # # study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])
            #
            # if data.get('form_make_mifc_on_submit'):
            #     # search term MIFC - if MIFC changes, this will need changed
            #     # make a list of column headers for the mifc file
            #     column_table_headers_average = [
            #         'Chip ID',
            #         'Cross Reference',
            #         'Assay Plate ID',
            #         'Assay Well ID',
            #         'Day',
            #
            #         'Hour',
            #         'Minute',
            #         'Target/Analyte',
            #         'Subtarget',
            #         'Method/Kit',
            #
            #         'Sample Location',
            #         'Value',
            #         'Value Unit',
            #         'Replicate',
            #         'Caution Flag',
            #
            #         'Exclude',
            #         'Notes',
            #         'Processing Details',
            #     ]
            #     # search term MIFC - if MIFC changes, this will need changed
            #     # Make a dictionary of headers in utils and header needed in the mifc file
            #     utils_key_column_header = {
            #         'matrix_item_name': 'Chip ID',
            #         'cross_reference': 'Cross Reference',
            #         'plate_name': 'Assay Plate ID',
            #         'well_name': 'Assay Well ID',
            #         'day': 'Day',
            #         'hour': 'Hour',
            #         'minute': 'Minute',
            #         'target': 'Target/Analyte',
            #         'subtarget': 'Subtarget',
            #         'method': 'Method/Kit',
            #         'location_name': 'Sample Location',
            #         'processed_value': 'Value',
            #         'unit': 'Value Unit',
            #         'replicate': 'Replicate',
            #         'caution_flag': 'Caution Flag',
            #         'exclude': 'Exclude',
            #         'notes': 'Notes',
            #         'sendmessage': 'Processing Details'}
            #
            #     # these should match what is in the forms.py...could make a generic dict, but leave for now WATCH BE CAREFUL
            #     calibration_curve_xref = {
            #         'select_one': 'Select One',
            #         'no_calibration': 'No Calibration',
            #         'best_fit': 'Best Fit',
            #         'logistic4': '4 Parameter Logistic w/fitted bounds',
            #         'logistic4a0': '4 Parameter Logistic w/user specified bound(s)',
            #         'linear': 'Linear w/fitted intercept',
            #         'linear0': 'Linear w/intercept = 0',
            #         'log': 'Logarithmic',
            #         'poly2': 'Quadratic Polynomial'
            #     }
            #
            #     # print(".unit ",data.get('standard_unit').unit)
            #     # print(".id ", data.get('standard_unit').id)
            #     # .unit
            #     # µg / mL
            #     # .id
            #     # 6
            #     # print(".unit ",data.get('standard_unit').unit)
            #     # print(".id ", data.get('standard_unit').id)
            #
            #     if data.get('form_block_standard_borrow_pk_single_for_storage') == None:
            #         borrowed_block_pk = -1
            #     else:
            #         borrowed_block_pk = data.get('form_block_standard_borrow_pk_single_for_storage')
            #
            #     if data.get('form_block_standard_borrow_pk_platemap_single_for_storage') == None:
            #         borrowed_platemap_pk = -1
            #     else:
            #         borrowed_platemap_pk = data.get(
            #             'form_block_standard_borrow_pk_platemap_single_for_storage')
            #
            #     use_curve_long = data.get('form_calibration_curve_method_used')
            #     use_curve = find_a_key_by_value_in_dictionary(calibration_curve_xref, use_curve_long)
            #     if use_curve == 'select_one':
            #         use_curve = 'no_calibration'
            #
            #     # here here  prefer to get plate and study from form...fix this
            #     # make a dictionary to send to the utils.py when call the function
            #     set_dict = {
            #         'called_from': 'form_save',
            #         'study': data.get('form_hold_the_study_id'),
            #         'pk_platemap': data.get('form_hold_the_platemap_id'),
            #         'pk_data_block': data.get('form_block_file_data_block_selected_pk_for_storage'),
            #         'plate_name': data.get('name'),
            #         'form_calibration_curve': use_curve,
            #         'multiplier': data.get('form_data_processing_multiplier'),
            #         'unit': data.get('form_calibration_unit'),
            #         'standard_unit': data.get('standard_unit').unit,
            #         'form_min_standard': data.get('form_calibration_standard_fitted_min_for_e'),
            #         'form_max_standard': data.get('form_calibration_standard_fitted_max_for_e'),
            #         'form_blank_handling': data.get('se_form_blank_handling'),
            #         'radio_standard_option_use_or_not': data.get('radio_standard_option_use_or_not'),
            #         'radio_replicate_handling_average_or_not_0': data.get(
            #             'radio_replicate_handling_average_or_not'),
            #         'borrowed_block_pk': borrowed_block_pk,
            #         'borrowed_platemap_pk': borrowed_platemap_pk,
            #         'count_standards_current_plate': data.get('form_number_standards_this_plate'),
            #         'target': data.get('form_calibration_target'),
            #         'method': data.get('form_calibration_method'),
            #         'time_unit': data.get('time_unit'),
            #         'volume_unit': data.get('volume_unit'),
            #         'user_notes': data.get('form_hold_the_notes_string'),
            #         'user_omits': data.get('form_hold_the_omits_string'),
            #         'plate_size': data.get('device'),
            #     }
            #
            #     # this function is in utils.py that returns data
            #     data_mover = plate_reader_data_file_process_data(set_dict)
            #     # what comes back is a dictionary of
            #     list_of_dicts = data_mover[9]
            #     list_of_lists_mifc_headers_row_0 = [None] * (len(list_of_dicts) + 1)
            #     list_of_lists_mifc_headers_row_0[0] = column_table_headers_average
            #     i = 1
            #     # print(" ")
            #     for each_dict_in_list in list_of_dicts:
            #         list_each_row = []
            #         for this_mifc_header in column_table_headers_average:
            #             # print("this_mifc_header ", this_mifc_header)
            #             # find the key in the dictionary that we need
            #             utils_dict_header = find_a_key_by_value_in_dictionary(utils_key_column_header,
            #                                                                   this_mifc_header)
            #             # print("utils_dict_header ", utils_dict_header)
            #             # print("this_mifc_header ", this_mifc_header)
            #             # get the value that is associated with this header in the dict
            #             this_value = each_dict_in_list.get(utils_dict_header)
            #             # print("this_value ", this_value)
            #             # add the value to the list for this dict in the list of dicts
            #             list_each_row.append(this_value)
            #         # when down with the dictionary, add the completely list for this row to the list of lists
            #         # print("list_each_row ", list_each_row)
            #         list_of_lists_mifc_headers_row_0[i] = list_each_row
            #         i = i + 1
            #
            #     # print("  ")
            #     # print('list_of_lists_mifc_headers_row_0')
            #     # print(list_of_lists_mifc_headers_row_0)
            #     # print("  ")
            #
            #     # First make a csv from the list_of_lists (using list_of_lists_mifc_headers_row_0)
            #
            #     # or self.objects.study
            #     my_study = form.instance.study
            #     my_user = self.request.user
            #
            #     # Specify the file for use with the file uploader class
            #     # some of these caused errors in the file name so remove them
            #     platenamestring = data.get('name')
            #     platenamestring = re.sub("\\\\", '', platenamestring)
            #     platenamestring = re.sub('/', '', platenamestring)
            #     platenamestring = re.sub(' ', '', platenamestring)
            #
            #     metadatastring = data.get('form_hold_the_data_block_metadata_string')
            #     metadatastring = re.sub("\\\\", '', metadatastring)
            #     metadatastring = re.sub('/', '', metadatastring)
            #     metadatastring = re.sub(' ', '', metadatastring)
            #
            #     # print(platenamestring)
            #     # print(metadatastring)
            #
            #     bulk_location = upload_file_location(
            #         my_study,
            #         'PLATE-{}|METADATA-{}'.format(
            #             platenamestring,
            #             metadatastring
            #         )
            #     )
            #
            #     # Make sure study has directories
            #     if not os.path.exists(MEDIA_ROOT + '/data_points/{}'.format(data.get('form_hold_the_study_id'))):
            #         os.makedirs(MEDIA_ROOT + '/data_points/{}'.format(data.get('form_hold_the_study_id')))
            #
            #     # Need to import from models
            #     # Avoid magic string, use media location
            #     file_location = MEDIA_ROOT.replace('mps/../', '', 1) + '/' + bulk_location + '.csv'
            #
            #     # Should make a csv writer to avoid repetition
            #     file_to_write = open(file_location, 'w')
            #     csv_writer = csv.writer(file_to_write, dialect=csv.excel)
            #
            #     # Add the UTF-8 BOM
            #     list_of_lists_mifc_headers_row_0[0][0] = '\ufeff' + list_of_lists_mifc_headers_row_0[0][0]
            #
            #     # print("!!!!!!!!")
            #     # print("at views.py 3168 - turn this back on later!!!!!")
            #     # print("!!!!!!!!")
            #     # Write the lines here here uncomment this
            #     for one_line_of_data in list_of_lists_mifc_headers_row_0:
            #         csv_writer.writerow(one_line_of_data)
            #
            #     file_to_write.close()
            #     new_mifc_file = open(file_location, 'rb')
            #     file_processor = AssayFileProcessor(new_mifc_file,
            #                                         my_study,
            #                                         my_user, save=True,
            #                                         full_path='/media/' + bulk_location + '.csv')
            #
            #     # Process the file
            #     file_processor.process_file()
            #
            # #### END When saving AssayPlateReaderMapUpdate after a calibration


            # only save if the formSET is in "update/edit" mode, not calibrate
            # calibrate occurs when a file block has been added to this plate map (one or more)
            # The number of file blocks is passed in by the initialization of this form field in the forms.py
            # Save form and formset
            # print("form.cleaned_data.get('form_number_file_block_combos') ",form.cleaned_data.get('form_number_file_block_combos'))
            if int(form.cleaned_data.get('form_number_file_block_combos')) == 0:
                save_forms_with_tracking(self, form, formset=formsets, update=True)
            # HANDY - to Save just the form and not the formset
            else:
                # Note that we elect NOT to send the formset
                save_forms_with_tracking(self, form, formset=[], update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

# # MOVED BACK TO Forms.py    this finds the key for the value provided as thisHeader
# def find_a_key_by_value_in_dictionary(this_dict, this_header):
#     """This is a function to find a key by value."""
#     my_key = ''
#     for key, value in this_dict.items():
#         if value == this_header:
#             my_key = key
#             break
#     return my_key


class AssayPlateReaderMapView(StudyViewerMixin, DetailView):
    """Assay plate map view"""
    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_add.html'

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapView, self).get_context_data(**kwargs)
        #####
        context['review'] = True
        context['page_called'] = 'review'
        #####

        block_combos = AssayPlateReaderMapItemValue.objects.filter(
            assayplatereadermap=self.object
        ).prefetch_related(
            'assayplatereadermapitem',
        ).filter(
            assayplatereadermapitem__plate_index=0
        ).filter(
            assayplatereadermapdatafileblock__isnull=False
        )
        if len(block_combos) > 0:
            data_attached = True
        else:
            data_attached = False
        context['data_attached'] = data_attached

        context['assay_map_additional_info'] = AssayPlateReadMapAdditionalInfoForm(study_id=self.object.study_id)

        context.update({
            'form': AssayPlateReaderMapForm(instance=self.object),
            'formset': AssayPlateReaderMapItemFormSetFactory(instance=self.object, user=self.request.user),
        })

        return context


class AssayPlateReaderMapDelete(CreatorAndNotInUseMixin, DeleteView):
    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_delete.html'

    def get_success_url(self):
        return self.object.get_post_submission_url()


# function used in plate reader map app (add, view, and update) to get associated matrix item setup for display
# do not think need this anymore, code that called got moved
# here here todo remove this ..not needed, but do it separately to make sure no error generated
# def get_matrix_item_information_for_plate_map(study_id):
#
#     # # moved some of this function to ajax call instead
#     # matrix_items_with_setup = AssayMatrixItem.objects.filter(
#     #     study_id=study_id
#     # ).prefetch_related(
#     #     'matrix',
#     #     'assaysetupcompound_set__compound_instance__compound',
#     #     'assaysetupcompound_set__concentration_unit',
#     #     'assaysetupcompound_set__addition_location',
#     #     'assaysetupcell_set__cell_sample__cell_type__organ',
#     #     'assaysetupcell_set__cell_sample__cell_subtype',
#     #     'assaysetupcell_set__cell_sample__supplier',
#     #     'assaysetupcell_set__addition_location',
#     #     'assaysetupcell_set__density_unit',
#     #     'assaysetupsetting_set__setting',
#     #     'assaysetupsetting_set__unit',
#     #     'assaysetupsetting_set__addition_location',
#     # ).order_by('matrix__name', 'name',)
#
#     matrix_list_for_size = AssayMatrix.objects.filter(
#             study_id=study_id
#         ).order_by('name',)
#
#     matrix_list_size = []
#     matrix_list_pk = []
#     matrix_column_size = []
#
#     # #  HARDCODED plate map size
#     # for record in matrix_list_for_size:
#     #     if record.number_of_rows <= 4 and record.number_of_columns <= 6:
#     #         matrix_list_size.append(24)
#     #         matrix_list_pk.append(record.id)
#     #     elif record.number_of_rows <= 8 and record.number_of_columns <= 12:
#     #         matrix_list_size.append(96)
#     #         matrix_list_pk.append(record.id)
#     #     else:
#     #         matrix_list_size.append(384)
#     #         matrix_list_pk.append(record.id)
#
#
#     # START replacing the hardcoded stuff above
#     # HANDY - must sort in place or get empty list back
#     # copy list to new variable
#     plate_sizes = assay_plate_reader_map_info_plate_size_choices_list
#     # sort in place
#     plate_sizes.sort()
#     # print("list after sorting ", plate_sizes)
#
#     for record in matrix_list_for_size:
#         my_size = plate_sizes[-1]
#         my_record_id = record.id
#         for this_size in plate_sizes:
#             row_size = assay_plate_reader_map_info_shape_row_dict.get(this_size)
#             col_size = assay_plate_reader_map_info_shape_col_dict.get(this_size)
#             if record.number_of_rows <= row_size and record.number_of_columns <= col_size:
#                 my_size = this_size
#                 my_record_id = record.id
#                 my_col_size = col_size
#                 break
#
#         matrix_list_size.append(my_size)
#         matrix_list_pk.append(my_record_id)
#         matrix_column_size.append(my_col_size)
#     # END replacing the hardcoded stuff above
#
#     # return matrix_items_with_setup, matrix_list_size, matrix_list_pk
#     return matrix_list_size, matrix_list_pk, matrix_column_size


#####
# START Plate reader file list, add, update, view and delete section
class AssayPlateReaderMapDataFileIndex(StudyViewerMixin, DetailView):
    """Assay plate reader file"""

    model = AssayStudy
    context_object_name = 'assayplatereaderfile_index'
    template_name = 'assays/assayplatereaderfile_index.html'

    # For permission mixin
    def get_object(self, queryset=None):
        self.study = super(AssayPlateReaderMapDataFileIndex, self).get_object()
        return self.study

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapDataFileIndex, self).get_context_data(**kwargs)

        # get files
        assayplatereadermapdatafiles = AssayPlateReaderMapDataFile.objects.filter(
            study=self.object.id
        )
        # find block count per file id
        file_block_count = AssayPlateReaderMapDataFileBlock.objects.filter(
            study=self.object.id
        ).values('assayplatereadermapdatafile').annotate(
            blocks=Count('assayplatereadermapdatafile')
        )
        # find plate maps selected per file id
        file_map_count = AssayPlateReaderMapDataFileBlock.objects.filter(
            study=self.object.id
        ).filter(
            assayplatereadermap__isnull=False
        ).values('assayplatereadermapdatafile').annotate(
            maps=Count('assayplatereadermapdatafile')
        )

        # get data block count to a dictionary
        file_block_count_dict = {}
        file_map_count_dict = {}
        for each in file_block_count.iterator():
            file_block_count_dict.update({each.get('assayplatereadermapdatafile'): each.get('blocks')})
        for each in file_map_count.iterator():
            file_map_count_dict.update({each.get('assayplatereadermapdatafile'): each.get('maps')})

        # put the count of the blocks into the queryset of files (this is very HANDY)
        for file in assayplatereadermapdatafiles:
            file.block_count = file_block_count_dict.get(int(file.id))
            file.map_count = file_map_count_dict.get(int(file.id))
            # print(file.id, " ",file.description, " ", file.block_count)
            # print(file.id, " ",file.description, " ", file.map_count)
        # get and put short file name into queryset
        for file in assayplatereadermapdatafiles:
            file.name_short = os.path.basename(str(file.plate_reader_file))

        context['assayplatereadermapdatafiles'] = assayplatereadermapdatafiles
        return context


class AssayPlateReaderMapDataFileView(StudyViewerMixin, DetailView):
    """Assay Plate Reader File Detail View"""
    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_update.html'

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapDataFileView, self).get_context_data(**kwargs)
        #####
        context['review'] = True
        context['page_called'] = 'review'
        #####

        context.update({
            'form': AssayPlateReaderMapDataFileForm(instance=self.object),
            'formset': AssayPlateReaderMapDataFileBlockFormSetFactory(instance=self.object, user=self.request.user)
        })

        # find block count per file id
        file_block_count = AssayPlateReaderMapDataFileBlock.objects.filter(
            assayplatereadermapdatafile=self.object.id
        )
        number_of_blocks = len(file_block_count)
        if number_of_blocks == 0:
            context['no_saved_blocks'] = True

        return context


class AssayPlateReaderMapDataFileDelete(CreatorAndNotInUseMixin, DeleteView):
    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_delete.html'

    def get_success_url(self):
        return self.object.get_post_submission_url()


# Adding a file to the filefield on the add page
class AssayPlateReaderMapDataFileAdd(StudyGroupMixin, CreateView):
    """Upload an plate reader data file add"""

    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_add.html'
    form_class = AssayPlateReaderMapDataFileAddForm

    # used in ADD, not in UPDATE - check carefully if copy
    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, study=study)
        else:
            return form_class(study=study)

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapDataFileAdd, self).get_context_data(**kwargs)
        #####
        context['add'] = True
        context['page_called'] = 'add'
        #####
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        return context

    def form_valid(self, form):
        study_id = self.kwargs['study_id']
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        if form.is_valid():
            data = form.cleaned_data
            # https://stackoverflow.com/questions/11796383/django-set-the-upload-to-in-the-view
            model_instance = form.save(commit=False)
            model_instance.plate_reader_file.field.upload_to = 'assay_plate_map/' + str(study_id)
            # this is what map uses, but not work for this since one field only
            # save_forms_with_tracking(self, form, update=False)
            self.object = form.save()
            return redirect(self.object.get_post_add_submission_url())
        else:
            # return this for ADD
            return self.render_to_response(self.get_context_data(form=form))
            # return this for UPDATE or VIEW
            # return self.render_to_response(self.get_context_data(form=form, formset=formset))


# the user is routed here after adding the file by a get_post_add_submission_url in the models.py
class AssayPlateReaderMapDataFileUpdate(StudyGroupMixin, UpdateView):
    """Assay Plate Reader File Update"""
    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_update.html'
    form_class = AssayPlateReaderMapDataFileForm

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapDataFileUpdate, self).get_context_data(**kwargs)
        #####
        context['update'] = True
        context['page_called'] = 'update'
        #####

        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = AssayPlateReaderMapDataFileBlockFormSetFactory(
                        self.request.POST,
                        instance=self.object,
                        user=self.request.user
                )
            else:
                context['formset'] = AssayPlateReaderMapDataFileBlockFormSetFactory(
                    instance=self.object,
                    user=self.request.user
                )

        # find block count per file id
        file_block_count = AssayPlateReaderMapDataFileBlock.objects.filter(
            assayplatereadermapdatafile=self.object.id
        )
        number_of_blocks = len(file_block_count)
        if number_of_blocks == 0:
            context['no_saved_blocks'] = True

        return context

    def form_valid(self, form):

        pk_for_file = self.object

        formset = AssayPlateReaderMapDataFileBlockFormSetFactory(
            self.request.POST,
            instance=self.object
        )
        # print("form: ", form)
        # print("SELF.OBJECT - self.object: ", self.object)

        formsets = [formset, ]
        formsets_are_valid = True

        for formset in formsets:
            # this executes for EACH formset, but hard to read data
            # print("FORMSET IN FORMSETS: ", formset)
            if not formset.is_valid():
                formsets_are_valid = False

        if form.is_valid() and formsets_are_valid:

            instance = form.save(commit=False)
            # example of what can be done here - HANDY
            # this executes ONCE - if need for each formset - put in forms.py
            # password = form.cleaned_data.get(‘password’)
            # instance.set_password(password)
            # can do this BEFORE instance.save(), after, they are none
            data_block = form.cleaned_data.get('data_block')
            line_start = form.cleaned_data.get('line_start')
            # print("data_block ", data_block) --- None until saved

            instance.save()
            formset.save()

            #####
            # # this would work for all but the pk of the data block table, so do not use it
            # for each in formset:
            #     data_block = each.cleaned_data.get('data_block')
            #     if data_block < 999:
            #         pk_id = each.cleaned_data.get('id')
            #         assayplatereadermap = each.cleaned_data.get('assayplatereadermap')
            #         data_block_metadata = each.cleaned_data.get('data_block_metadata')
            #         over_write_sample_time = each.cleaned_data.get('over_write_sample_time')
            #         line_start = each.cleaned_data.get('line_start')
            #         line_end = each.cleaned_data.get('line_end')
            #         delimited_start = each.cleaned_data.get('delimited_start')
            #         delimited_end = each.cleaned_data.get('delimited_end')
            #
            #         block_data_dict['assayplatereadermapdatafile'] = pk_for_file
            #         block_data_dict['assayplatereadermap'] = assayplatereadermap
            #         block_data_dict['over_write_sample_time'] = over_write_sample_time
            #         block_data_dict['line_start'] = line_start
            #         block_data_dict['line_end'] = line_end
            #         block_data_dict['delimited_start'] = delimited_start
            #         block_data_dict['delimited_end'] = delimited_end
            #
            #         block_data_list_of_dicts.append(block_data_dict)
            #
            #####

            # .values makes a dictionary! saves some steps - HANDY
            block_dict = AssayPlateReaderMapDataFileBlock.objects.filter(
                assayplatereadermapdatafile=pk_for_file
            ).prefetch_related(
                'assayplatereadermap',
                'assayplatereadermapdatafile',
            ).values()

            # print('PK FOR FILE ', pk_for_file)
            # print('DICT:')
            # print(block_dict)

            # this function is in utils.py
            # add_update_map_item_values =
            # call it to write to the map item value table, do not need to return anything
            # in the utils.py file
            add_update_plate_reader_data_map_item_values_from_file(
                pk_for_file,
                block_dict
            )

            # some other methods...KEEP for reference for now
            # save_forms_with_tracking(self, form, formset=formsets, update=True)
            # form.save()
            # formset.save()

            # One for each field in the form - HANDY
            # countis=0
            # for each in form:
            #     .print("FORM ", countis)
            #     .print(each)
            #     countis=countis+1

            # One for each SAVED (no extra) formset, but hard to parse - HANDY
            # countss=0
            # for each in formset:
            #     .print("FORMSET: ", countss)
            #     .print(each)
            #     # print(each.data_block)  --  gives error, cannot get this way
            #     countss=countss+1

            # print("form and formset valid")
            return redirect(self.object.get_post_submission_url())
        else:
            # print("form or formset NOT valid")
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

# END Plate reader file list, add, update, view and delete section

# replacing with a detail page...hold for now
# class AssayPlateReaderMapView(StudyGroupMixin, UpdateView):
#     """Assay plate map view"""
#     model = AssayPlateReaderMap
#     template_name = 'assays/assayplatereadermap_add.html'
#     form_class = AssayPlateReaderMapForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayPlateReaderMapView, self).get_context_data(**kwargs)
#         #####
#         context['review'] = True
#         context['page_called'] = 'review'
#         #####
#         context['assay_map_additional_info'] = AssayPlateReadMapAdditionalInfoForm(study_id=self.object.study_id)
#
#         if 'formset' not in context:
#             if self.request.POST:
#                 context['formset'] = AssayPlateReaderMapItemFormSetFactory(
#                         self.request.POST,
#                         instance=self.object,
#                         user=self.request.user
#                 )
#             else:
#                 context['formset'] = AssayPlateReaderMapItemFormSetFactory(
#                     instance=self.object,
#                     user=self.request.user
#                 )
#
#         #  20200522 getting rid of the value_formset
#         # adding/changed 20200113
#         # value_formsets_include_template = AssayPlateReaderMapItemValue.objects.filter(
#         #     assayplatereadermap=self.object
#         # ).filter(
#         #     plate_index=0
#         # )
#         # # one is the empty set (no file/block attached) - the template value set
#         # if len(value_formsets_include_template) == 1:
#         #
#         #     if 'value_formset' not in context:
#         #         if self.request.POST:
#         #             context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
#         #                     self.request.POST,
#         #                     instance=self.object,
#         #                     user=self.request.user
#         #             )
#         #         else:
#         #             context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
#         #                 instance=self.object,
#         #                 user=self.request.user
#         #             )
#         # else:
#         #     context['value_formset'] = "None"
#         # # end update fo 20200113
#
#         # move to ajax for performance reasons
#         # return_list = get_matrix_item_information_for_plate_map(self.object.study_id)
#         # matrix_items_in_study = return_list[0]
#         # matrix_list_size = return_list[1]
#         # matrix_list_pk = return_list[2]
#         # context['matrix_items_in_study'] = matrix_items_in_study
#         # context['matrix_list_size'] = matrix_list_size
#         # context['matrix_list_pk'] = matrix_list_pk
#
#         # return_list = get_matrix_item_information_for_plate_map(self.object.study_id)
#         # context['matrix_list_size'] = return_list[0]
#         # context['matrix_list_pk'] = return_list[1]
#         # context['matrix_column_size'] = return_list[2]
#         return context
#
#     # no processing of form since view does not allow saving changes

# replaced with a detail page (above) for security
# class AssayPlateReaderMapDataFileView(StudyGroupMixin, UpdateView):
#     """Assay Plate Reader File View"""
#     model = AssayPlateReaderMapDataFile
#     template_name = 'assays/assayplatereaderfile_update.html'
#     form_class = AssayPlateReaderMapDataFileForm
#
#     def get_context_data(self, **kwargs):
#         context = super(AssayPlateReaderMapDataFileView, self).get_context_data(**kwargs)
#         #####
#         context['review'] = True
#         context['page_called'] = 'review'
#         #####
#
#         if 'formset' not in context:
#             if self.request.POST:
#                 context['formset'] = AssayPlateReaderMapDataFileBlockFormSetFactory(
#                         self.request.POST,
#                         instance=self.object,
#                         user=self.request.user
#                 )
#             else:
#                 context['formset'] = AssayPlateReaderMapDataFileBlockFormSetFactory(
#                     instance=self.object,
#                     user=self.request.user
#                 )
#
#         # find block count per file id
#         file_block_count = AssayPlateReaderMapDataFileBlock.objects.filter(
#             assayplatereadermapdatafile=self.object.id
#         )
#         number_of_blocks = len(file_block_count)
#         if number_of_blocks == 0:
#             context['no_saved_blocks'] = True
#
#         return context
#

#####
# END Plate reader file list, add, update, view and HOLD section

##### Start the omic data section

class AssayOmicDataFileUploadIndex(StudyViewerMixin, DetailView):
    """Assay Omic Data file"""

    model = AssayStudy
    context_object_name = 'assayomicdatafileupload_index'
    template_name = 'assays/assayomicdatafileupload_index.html'

    # For permission mixin
    def get_object(self, queryset=None):
        self.study = super(AssayOmicDataFileUploadIndex, self).get_object()
        return self.study

    def get_context_data(self, **kwargs):
        context = super(AssayOmicDataFileUploadIndex, self).get_context_data(**kwargs)

        # get files
        datafiles = AssayOmicDataFileUpload.objects.filter(
            study=self.object.id
        )
        # get and put short file name into queryset
        for file in datafiles:
            file.name_short = os.path.basename(str(file.omic_data_file))

        # find count of genomic data points associated to each file
        data_point_count = AssayOmicDataPoint.objects.filter(
            study=self.object.id
        ).values('omic_data_file').annotate(
            point_count=Count('omic_data_file')
        )
        # put point counts in a dictionary
        point_count_dict = {}
        for each in data_point_count.iterator():
            point_count_dict.update({each.get('omic_data_file'): each.get('point_count')})

        # put the counts into the queryset
        for file in datafiles:
            file.point_count = point_count_dict.get(int(file.id))

        context['datafiles'] = datafiles
        return context


class AssayOmicDataFileUploadDelete(CreatorAndNotInUseMixin, DeleteView):
    model = AssayOmicDataFileUpload
    template_name = 'assays/assayomicdatafileupload_delete.html'

    def get_success_url(self):
        return self.object.get_post_submission_url()


class AssayOmicDataFileUploadAdd(StudyGroupMixin, CreateView):
    """Views Add Upload an AssayOmicDataFileUpload file """

    model = AssayOmicDataFileUpload
    template_name = 'assays/assayomicdatafileupload_aur.html'
    form_class = AssayOmicDataFileUploadForm

    # For permission mixin
    def get_object(self, queryset=None):
        self.study = super(AssayOmicDataFileUploadAdd, self).get_object()
        return self.study

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, study=study)
        else:
            return form_class(study=study)

    def get_context_data(self, **kwargs):
        context = super(AssayOmicDataFileUploadAdd, self).get_context_data(**kwargs)
        context['add'] = True
        context['page_called'] = 'add'
        return context

    def form_valid(self, form):
        if form.is_valid():
            save_forms_with_tracking(self, form, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, ))

class AssayOmicDataFileUploadUpdate(StudyGroupMixin, UpdateView):
    """Views View Upload an AssayOmicDataFileUpload file """

    model = AssayOmicDataFileUpload
    template_name = 'assays/assayomicdatafileupload_aur.html'
    form_class = AssayOmicDataFileUploadForm

    def get_context_data(self, **kwargs):
        context = super(AssayOmicDataFileUploadUpdate, self).get_context_data(**kwargs)
        context['update'] = True
        context['page_called'] = 'update'
        return context

    def form_valid(self, form):
        if form.is_valid():
            save_forms_with_tracking(self, form, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, ))

class AssayOmicDataFileUploadView(StudyGroupMixin, DetailView):
    """Views View Upload an AssayOmicDataFileUpload file """

    model = AssayOmicDataFileUpload
    template_name = 'assays/assayomicdatafileupload_aur.html'
    form_class = AssayOmicDataFileUploadForm

    def get_context_data(self, **kwargs):
        context = super(AssayOmicDataFileUploadView, self).get_context_data(**kwargs)
        context['review'] = True
        context['page_called'] = 'review'

        # HANDY to use DetailView in a View view and trick Django into getting the form
        context.update({
            'form': AssayOmicDataFileUploadForm(instance=self.object),
        })

        return context

# END omic data file list, add, update, view and delete section


class AssayStudyOmics(StudyViewerMixin, DetailView):
    """Displays the omics interface for the current study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_omics.html'

    def get_context_data(self, **kwargs):
        context = super(AssayStudyOmics, self).get_context_data(**kwargs)
        context.update({
            'form': AssayStudyGroupForm(instance=self.object),
        })

        return context


class AssayStudyOmicsDownload(StudyViewerMixin, DetailView):
    """Returns a CSV of the filtered Omics Data for a study"""
    model = AssayStudy

    def render_to_response(self, context, **response_kwargs):
        # Make sure that the study exists, then continue
        if self.object:
            get_params = {
                'negative_log10_pvalue': self.request.GET.get("negative_log10_pvalue") == "true",
                'absolute_log2_foldchange': self.request.GET.get("absolute_log2_foldchange") == "true",
                'over_expressed': self.request.GET.get("over_expressed") == "true",
                'under_expressed': self.request.GET.get("under_expressed") == "true",
                'neither_expressed': self.request.GET.get("neither_expressed") == "true",
                'threshold_pvalue': float(self.request.GET.get("threshold_pvalue")),
                'threshold_log2_foldchange': float(self.request.GET.get("threshold_log2_foldchange")),
                'min_pvalue': float(self.request.GET.get("min_pvalue")),
                'max_pvalue': float(self.request.GET.get("max_pvalue")),
                'min_negative_log10_pvalue': float(self.request.GET.get("min_negative_log10_pvalue")),
                'max_negative_log10_pvalue': float(self.request.GET.get("max_negative_log10_pvalue")),
                'min_log2_foldchange': float(self.request.GET.get("min_log2_foldchange")),
                'max_log2_foldchange': float(self.request.GET.get("max_log2_foldchange")),
                'abs_log2_foldchange': float(self.request.GET.get("abs_log2_foldchange")),
                'visible_charts': self.request.GET.get("visible_charts").split("+")
            }

            data = ''
            if len(get_params['visible_charts']) > 0 and not (get_params['over_expressed'] == False and get_params['under_expressed'] == False and get_params['neither_expressed'] == False):
                data = get_filtered_omics_data_as_csv(get_params)
            else:
                return HttpResponse('', content_type='text/plain')

            # For specifically text
            response = HttpResponse(data, content_type='text/csv', charset='utf-8')
            response['Content-Disposition'] = 'attachment;filename="' + str(self.object) + '.csv"'

            return response
        # Return nothing otherwise
        else:
            return HttpResponse('', content_type='text/plain')


class AssayStudyOmicsHeatmap(StudyViewerMixin, DetailView):
    """Displays the omics interface for the current study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_omics_heatmap.html'


class AssayStudyOmicsHeatmapJSON(StudyViewerMixin, TemplateView):
    """Displays the omics interface for the current study"""
    template_name = 'assays/assaystudy_omics_heatmap.html'

    def get(self, request, *args, **kwargs):
        data = {
          "mat": [
            [
              -0.792803571,
              0.527687127,
              0.000622536,
              0.356722594,
              0.933286088,
              -0.131728538,
              0.8084519440000001,
              4.240884801,
              -0.5402313910000001,
              -0.981456952,
              -0.84689892,
              -0.25279592100000003,
              0.114189581,
              -0.06649884,
              0.149218809,
              1.351263924,
              0.6458672120000001,
              0.60561098,
              3.232454573,
              0.342634572,
              -0.43091232399999996,
              -0.40590567,
              0.199563989,
              -1.122536294,
              2.2103345709999997,
              0.405126315,
              -0.08976315900000001,
              0.405126315,
              0.340012773
            ],
            [
              0.17762054,
              -0.016061488999999998,
              5.422113832999999,
              1.307039675,
              0.355814985,
              0.27690499399999996,
              0.483153915,
              -0.24049582100000003,
              1.336445996,
              1.149618502,
              0.361412978,
              -0.380518938,
              -0.21354100399999998,
              -0.471938639,
              -0.620858723,
              -0.163637058,
              -0.487256142,
              -0.029569687999999997,
              -0.23205777800000002,
              -0.6690369389999999,
              -0.44924169799999997,
              1.1589304059999999,
              0.5119620220000001,
              2.370834155,
              0.262893885,
              -0.513128895,
              -0.501210068,
              0.43927756100000004,
              -0.342460508
            ],
            [
              -0.6978761509999999,
              -0.555610265,
              -0.36049755899999997,
              -0.460236731,
              -0.6807606970000001,
              -0.169463518,
              1.715708875,
              -0.5171048229999999,
              0.18498770899999997,
              0.8106597,
              -0.440334448,
              -0.621052026,
              -0.08680335800000001,
              -0.753966225,
              -0.401972037,
              -0.562086752,
              -0.560644597,
              0.542301381,
              -0.382639145,
              -0.37785352299999997,
              -0.713472923,
              -0.37760936799999995,
              4.308904581,
              -0.638131949,
              -0.556114063,
              -0.318145763,
              -0.489582714,
              1.6773765269999998,
              -0.6827904640000001
            ],
            [
              0.8505465179999999,
              -0.263279907,
              0.179253031,
              0.39864672100000004,
              1.537663802,
              0.505291411,
              0.902366491,
              -0.16628803,
              0.6307305639999999,
              0.39944828299999996,
              0.8471713670000001,
              -0.442268094,
              0.44368676,
              1.552969029,
              1.110283483,
              -0.326698072,
              -0.40526737399999996,
              0.663747183,
              0.42447003299999997,
              0.283221899,
              -4.243973921,
              0.718315578,
              1.747343933,
              -1.020927175,
              0.305028514,
              1.47174613,
              0.048902278,
              -0.255283556,
              0.5482245729999999
            ],
            [
              1.412416216,
              0.018987506,
              0.902251622,
              -0.17813747,
              0.781819022,
              0.211815895,
              -0.023427175,
              3.557295952,
              1.1737835559999998,
              -0.012362163999999998,
              0.769782484,
              -0.681031743,
              -1.0473753890000002,
              0.652065499,
              0.17231669100000002,
              2.072433469,
              1.135709377,
              -0.169977181,
              0.881067136,
              -0.486159025,
              -1.451838026,
              0.371237737,
              -0.581665325,
              -0.126356157,
              0.24100472399999998,
              1.06526919,
              0.974531796,
              0.668645091,
              0.05696489
            ],
            [
              -0.388039665,
              -0.5926266139999999,
              -0.24413651,
              0.740364734,
              3.023348415,
              -0.433985412,
              -0.6301244570000001,
              1.156531983,
              0.433696213,
              3.84950782,
              -0.22542574199999998,
              -0.656106808,
              -0.311953357,
              -0.397450226,
              1.0440255379999999,
              -0.247816912,
              3.640524345,
              -0.59251039,
              0.514666245,
              -0.45396994,
              1.649737631,
              3.366020313,
              -0.430502237,
              -0.295312303,
              2.824551497,
              -0.014275115,
              -0.410477794,
              -0.22971778399999998,
              3.7098286160000002
            ],
            [
              1.408537135,
              -0.017369325,
              -0.36712796200000003,
              0.313253548,
              -0.16288686,
              0.027411933,
              -0.281351556,
              5.8138464889999995,
              -0.16170658400000001,
              0.472386752,
              -0.33979584,
              0.669956625,
              -0.2596391,
              -0.386601295,
              -0.293654593,
              4.390499721,
              -0.420942214,
              -0.402955154,
              -0.346809494,
              -0.222725132,
              0.36849943,
              1.49303248,
              -0.34174718,
              -0.343420451,
              5.2848086069999995,
              -0.358156896,
              -0.222931558,
              -0.40139116700000005,
              -0.412478715
            ],
            [
              0.9066424059999999,
              -0.6847714229999999,
              0.015261253999999998,
              0.16056792,
              0.36500211299999996,
              -0.564392699,
              0.16907282699999998,
              -0.035192496000000004,
              -0.031210405,
              0.447742443,
              0.544075103,
              0.280008477,
              -0.066278222,
              -0.225814318,
              4.103496507,
              1.2196915659999998,
              -0.24502200100000002,
              -0.681552658,
              -0.304817333,
              -0.511212295,
              -1.100056017,
              1.335983295,
              -0.500561544,
              0.721259819,
              0.284747072,
              0.232812724,
              -0.796930101,
              -0.156381455,
              1.503853721
            ],
            [
              -0.45290705200000003,
              -0.392790536,
              -0.374173515,
              -0.527418493,
              -0.32010333399999996,
              -0.560657219,
              -0.31284750899999997,
              -0.463903623,
              -0.304652329,
              -0.30897114,
              -0.331935876,
              4.098930821000001,
              -0.413942149,
              -0.5014189170000001,
              1.256164876,
              -0.12356019,
              -0.425577927,
              -0.36998588,
              -0.054684881,
              -0.484730631,
              -0.419739472,
              -0.432412432,
              0.143245619,
              -0.266932489,
              -0.34086030700000003,
              -0.231847291,
              -0.448292539,
              -0.42868169,
              -0.615936889
            ],
            [
              3.579051735,
              0.92330807,
              -0.651094367,
              0.952743833,
              -0.212733397,
              0.006074527,
              -0.121038246,
              0.083769063,
              -0.7226782140000001,
              1.669410989,
              -0.247600883,
              -0.284623649,
              -0.687716717,
              -0.320883885,
              -0.93370415,
              -0.309230053,
              0.544870152,
              0.824029397,
              -0.087291924,
              -0.973905867,
              -0.308282983,
              0.8221457040000001,
              -0.72904308,
              -0.08886573099999999,
              -0.29848499,
              -0.451367112,
              -1.134040733,
              0.379230443,
              1.491612577
            ],
            [
              -0.582761335,
              -0.706379425,
              0.36431330100000003,
              -0.483011414,
              -0.71307719,
              -0.048548064,
              -0.527944549,
              0.337501769,
              -0.656781635,
              -0.323318624,
              -0.432950623,
              -0.414799098,
              -1.02570516,
              -0.861415433,
              0.11344713099999999,
              -0.110117735,
              -0.493510825,
              0.148841502,
              -0.341096914,
              -0.373760525,
              5.16013802,
              -0.20490693199999999,
              -0.46557486299999995,
              -0.17040549100000002,
              0.046286803,
              -0.100887639,
              0.936150906,
              -0.15980844,
              -0.846857677
            ],
            [
              -0.58688791,
              -0.186685902,
              -3.51852921,
              0.25062883399999997,
              -0.477773537,
              -0.62381107,
              -0.92202388,
              -0.55383453,
              0.018847867,
              1.2676445570000001,
              0.243732055,
              -0.233528273,
              0.07072635599999999,
              -0.256360198,
              1.7410016069999998,
              0.16824737899999997,
              -0.24597429899999998,
              0.014972758999999999,
              -0.537623787,
              0.259364957,
              1.303190492,
              1.0432080240000001,
              -1.0210949459999998,
              -0.09744421199999999,
              -0.6792905929999999,
              0.132592576,
              -0.440607517,
              -0.21005684,
              0.651311995
            ],
            [
              -0.693639785,
              -0.357559299,
              -0.903861262,
              -0.8104502790000001,
              0.293775461,
              1.012469252,
              -0.10446230000000001,
              -0.573757161,
              -0.629467998,
              -1.1311389379999999,
              -0.401984075,
              -0.672554564,
              -1.1827919740000001,
              -1.00138041,
              -1.020216093,
              -0.43779921299999996,
              -0.10378360199999999,
              -0.38756592799999995,
              0.38647177200000005,
              -0.524742175,
              3.6270702480000003,
              -0.846550806,
              -0.473736661,
              0.443388919,
              0.7661352570000001,
              0.193683015,
              -0.614757268,
              -0.382906171,
              -0.8644104109999999
            ],
            [
              0.327203594,
              0.857319301,
              -1.3973565959999998,
              -0.226683585,
              -0.986051455,
              0.438343505,
              0.095527129,
              5.598772307999999,
              0.5350257970000001,
              -0.057479225,
              -0.089086932,
              -0.47329101100000004,
              2.070252907,
              0.201409888,
              1.1347281329999999,
              0.095734104,
              0.22916067,
              0.566649702,
              1.011889663,
              0.9023425559999999,
              0.7355103040000001,
              -0.493538517,
              3.1769186019999998,
              0.49004573700000004,
              -0.693495689,
              -0.18370487800000002,
              -0.182356844,
              0.7447287690000001,
              -0.31106439199999997
            ],
            [
              0.331108191,
              -0.46797839700000005,
              0.6811123290000001,
              -1.195914121,
              -0.538461957,
              3.616542204,
              0.094919881,
              0.527357553,
              -0.16047831199999998,
              -0.940444939,
              -1.025689676,
              0.053722044000000004,
              0.081275611,
              -0.616337936,
              -0.48042057,
              0.6209033820000001,
              -0.7237930640000001,
              -0.759642991,
              -0.7449007440000001,
              -0.43363819,
              -0.8049298490000001,
              0.429022269,
              0.765012989,
              0.400356525,
              0.20774184899999998,
              1.4743730080000002,
              0.888734282,
              0.38771558100000003,
              -0.623678298
            ],
            [
              0.14118383699999998,
              0.788608352,
              0.51421388,
              0.528255597,
              0.906234597,
              0.050158065,
              -0.8433413820000001,
              1.44384296,
              -0.253699343,
              0.562537497,
              -0.505923659,
              -6.621630156,
              -1.253907087,
              0.947883556,
              0.394657662,
              0.613122698,
              -0.223205762,
              0.9053737359999999,
              0.679301554,
              0.8597892220000001,
              -0.022354553,
              1.0467260520000001,
              0.194471,
              0.35991283399999996,
              -0.8063482340000001,
              1.5866198759999999,
              0.31198582399999997,
              0.544470027,
              1.479598537
            ],
            [
              -0.5243099489999999,
              -0.285994749,
              -0.484871681,
              0.176655189,
              -0.139711627,
              -0.35297839700000005,
              -0.19252985399999997,
              -0.601257973,
              -0.42732342700000003,
              0.459403791,
              -0.38300100000000004,
              -0.571316753,
              -0.387982572,
              -0.35394511799999995,
              -0.24031472,
              -0.305685522,
              0.456864915,
              -0.134886653,
              2.136583182,
              -0.463127859,
              -0.6004083929999999,
              4.430955918,
              -0.374772774,
              -0.206853106,
              1.756104521,
              0.8328872890000001,
              -0.314392176,
              -0.31373742,
              0.49342028299999996
            ],
            [
              0.509592174,
              0.464774315,
              0.275495704,
              -0.01882253,
              -0.005537792,
              -0.457197866,
              3.408253083,
              -0.43040764299999995,
              -0.754186082,
              -0.836530855,
              -0.277053957,
              -0.54257843,
              0.8504395770000001,
              -0.298981449,
              -0.16939480899999998,
              0.254783369,
              -0.427821755,
              -0.1389465,
              0.618069135,
              1.926349897,
              -0.305399918,
              -0.535939215,
              -0.07866166599999999,
              6.267854465,
              -0.57293844,
              -0.302168609,
              0.72307512,
              0.611863003,
              -0.2145995
            ],
            [
              -0.554447111,
              -0.145753485,
              0.019807701,
              -0.634915727,
              -0.49376688700000004,
              -0.587644968,
              -0.22371499600000003,
              1.3850494759999998,
              -0.346100755,
              0.25453660899999997,
              0.057887318,
              -0.593081366,
              -0.47065185,
              -0.753944095,
              -0.044570503,
              -0.33459763600000003,
              0.33958778799999995,
              -0.135201173,
              -0.111896921,
              4.913848539,
              -0.542750046,
              -0.27783299,
              -0.689097582,
              -0.21668800600000002,
              1.127699857,
              0.03588747,
              -0.070416156,
              -0.553268062,
              -0.9774276890000001
            ],
            [
              -0.530831743,
              -0.260873607,
              -0.461134617,
              -0.38905618799999997,
              -0.512555424,
              -0.513202268,
              -0.33755039700000006,
              -0.449953768,
              -0.184845421,
              -0.565880657,
              -0.37635620200000003,
              -0.28526610399999996,
              -0.5705058789999999,
              3.598950655,
              -0.477052971,
              -0.364449691,
              -0.648917127,
              -0.390363086,
              1.117877995,
              -0.464086586,
              -0.456431016,
              -0.571010056,
              -0.456668794,
              -0.58230495,
              -0.426192704,
              -0.411161613,
              -0.455618608,
              -0.297498019,
              -0.47141323
            ],
            [
              -0.6432463310000001,
              0.052021433,
              -0.7350066259999999,
              0.041068843,
              -0.062094125,
              5.477714716,
              1.256686967,
              -0.136401851,
              0.5772668710000001,
              -0.60002565,
              0.087671916,
              -0.5609597789999999,
              -0.56490393,
              -0.629261602,
              -0.214226487,
              0.09929963,
              -0.095715004,
              -0.632856345,
              1.09320354,
              0.38697641899999996,
              -0.374720076,
              -0.564957229,
              1.680895489,
              0.508498891,
              0.916604247,
              -0.607497709,
              0.58989289,
              -0.12276483699999999,
              -0.533651064
            ],
            [
              -0.693868027,
              0.57619653,
              -0.488541037,
              -0.60094858,
              1.139598497,
              -0.024286993,
              -0.28819455899999996,
              -0.499250839,
              0.103697413,
              -1.044716157,
              -1.02427507,
              3.0230034439999995,
              3.859028873,
              0.7429784420000001,
              -0.35272281899999997,
              0.069205383,
              -1.117741919,
              0.651553716,
              -0.364768511,
              -0.5472691,
              -0.735728719,
              -0.623797671,
              -0.105370633,
              -0.13943154900000002,
              -0.055372648,
              0.774449831,
              0.538987341,
              0.35514519,
              -1.45386407
            ],
            [
              0.006531886,
              0.564826732,
              3.6953185239999997,
              0.316255033,
              -0.268737774,
              0.936461505,
              0.22915170000000004,
              0.649579007,
              -0.330103595,
              -0.504534505,
              0.264729237,
              -0.977228043,
              0.493632169,
              -0.401821398,
              -0.28623177899999996,
              0.14337127800000002,
              -0.360231532,
              0.34076271700000005,
              0.6331625120000001,
              -0.710530502,
              -1.334690191,
              0.158108045,
              -0.347820435,
              -0.07449706099999999,
              -0.970507716,
              -0.26479443,
              -0.298648517,
              -0.10090872,
              -0.11742112
            ],
            [
              -0.185695405,
              -0.173758799,
              0.084357105,
              1.826502656,
              0.00816719,
              -1.102148634,
              0.29900253600000004,
              0.458848186,
              0.292508806,
              0.110508201,
              0.083592283,
              -0.49433306299999996,
              -0.117947546,
              -0.539712481,
              -0.106334279,
              -0.403083002,
              -0.789473381,
              1.041787363,
              1.70041072,
              -0.293951867,
              4.8395247580000005,
              1.015480815,
              0.841188534,
              -0.620389764,
              -0.565583764,
              -0.262366184,
              0.226425315,
              -0.048000565,
              1.126249373
            ],
            [
              0.184462349,
              -0.526037871,
              0.432087272,
              -0.882311913,
              0.246356093,
              0.8587545209999999,
              0.052858019000000006,
              -1.118340603,
              -0.8469488159999999,
              -0.778824075,
              3.525192777,
              -1.8727450069999998,
              -0.779756435,
              -1.0396393990000001,
              -0.59333431,
              0.40215600700000004,
              -1.387426464,
              -0.145435051,
              -0.46497243,
              -0.22106446100000002,
              -0.861483648,
              0.125415634,
              -0.19184911600000001,
              2.3744602969999997,
              -0.74142144,
              0.7654394,
              1.029796862,
              0.03307866,
              0.44066582
            ],
            [
              1.760301448,
              -0.912259652,
              -1.1633458890000001,
              -0.965891664,
              -0.7951534140000001,
              -0.616300339,
              -1.360743997,
              -1.448291877,
              -0.024088935,
              -1.188868793,
              -0.229906845,
              2.1814891430000003,
              -1.154435684,
              6.28292787,
              -0.303782002,
              -0.165568925,
              -1.126153349,
              1.678721355,
              -1.683560793,
              -0.864063548,
              -0.025445472,
              1.8909462190000002,
              0.667805988,
              -0.625764381,
              -1.0633403129999999,
              3.222816803,
              -0.0013596189999999998,
              -0.20366175600000003,
              0.187669924
            ],
            [
              -0.07364355,
              -0.103789279,
              -0.17130483600000002,
              0.351910065,
              0.63677969,
              -0.136732984,
              0.356830815,
              3.8891158239999997,
              0.645442526,
              1.3663589180000002,
              0.995319244,
              5.608685402000001,
              1.101919141,
              -0.554900568,
              0.087820649,
              0.061305127,
              1.931275557,
              -0.692417574,
              -0.481807702,
              -0.16288735,
              -0.538298189,
              2.440412245,
              0.804274605,
              -0.605526195,
              1.788457016,
              -0.37652092200000004,
              0.35819202,
              0.164487781,
              3.719306763
            ],
            [
              -0.7515267409999999,
              0.49762292,
              -0.142534658,
              -0.882124083,
              -1.151282849,
              2.307907188,
              -0.12032085,
              -0.35126953200000005,
              -1.526178564,
              -0.7532684279999999,
              3.600861739,
              -1.223995853,
              -0.607229424,
              -0.027417898,
              0.190161632,
              0.6105504079999999,
              0.149796331,
              -0.122879865,
              0.247865963,
              -0.40483370799999996,
              0.736929754,
              -0.9442750679999999,
              -0.078919294,
              0.661648005,
              -0.24494877899999998,
              3.051534602,
              -0.10736522800000001,
              0.367536408,
              -1.5179858240000002
            ],
            [
              -0.31236414,
              0.7012570890000001,
              0.47520812,
              -0.585297054,
              -0.122694283,
              -0.8668751370000001,
              0.367939523,
              -0.481103706,
              2.072237711,
              10.29186436,
              1.298805701,
              -0.6281759170000001,
              -0.173084375,
              -0.02710755,
              0.35516907299999995,
              0.470456905,
              0.121400231,
              0.37492460200000005,
              -0.27830734100000004,
              -0.553746266,
              -0.935156558,
              -0.042420295999999996,
              -0.479479902,
              -0.332400886,
              -0.7100170109999999,
              1.873931755,
              0.20455442899999998,
              -0.32315246,
              0.18757252100000002
            ],
            [
              0.11931136,
              0.593670684,
              0.48915277100000004,
              0.841683345,
              1.064673748,
              0.095113499,
              1.050152022,
              1.8914884269999999,
              -5.5283552,
              0.64306832,
              -1.100026181,
              0.765710935,
              1.165406655,
              0.30638633,
              -1.3658942619999999,
              0.635492291,
              -0.37779861600000003,
              0.521665309,
              -0.6084974329999999,
              0.398484128,
              -0.988354968,
              1.36349214,
              1.36269783,
              -0.112291585,
              -0.262719995,
              0.503524059,
              0.498006014,
              1.525942005,
              0.339189212
            ],
            [
              -0.294263824,
              -0.618071649,
              -0.252534114,
              -0.78660676,
              -0.228026664,
              0.977860794,
              -1.200449832,
              -0.22037931,
              -0.240489906,
              -0.201675468,
              1.47598938,
              -0.557000568,
              -0.502553204,
              -0.437501309,
              0.966927023,
              0.37967009700000004,
              0.048795579000000006,
              0.25062286899999997,
              2.9610247139999997,
              2.299033235,
              -1.210659274,
              0.418655141,
              1.161954005,
              -0.15700654,
              -1.2541429370000001,
              -0.574558055,
              -0.662438275,
              3.702617515,
              -0.35302723
            ],
            [
              -0.000863802,
              0.735638383,
              -0.680289747,
              0.040925842999999996,
              0.359330228,
              -1.587400295,
              -1.041686081,
              0.071551408,
              -0.168322665,
              -1.3773033080000001,
              3.6045390889999998,
              -0.004601068,
              1.527568732,
              -0.30015470699999997,
              -0.7861355090000001,
              -0.138050924,
              -0.366480418,
              -0.7969702059999999,
              -0.030155544,
              0.8031000559999999,
              0.6831455609999999,
              -0.900708154,
              0.15251077,
              0.140092011,
              0.37681542100000004,
              -1.214319621,
              1.326197465,
              1.5230702790000001,
              -1.312001824
            ],
            [
              -0.27673681899999997,
              -0.426080887,
              -0.160160461,
              -0.8900327709999999,
              -0.437405434,
              0.143897214,
              -0.573425958,
              -0.48641938100000004,
              -0.536963482,
              -0.657041002,
              -0.47334541799999996,
              -0.23747527899999998,
              -0.669396538,
              -0.559435302,
              0.038953301,
              0.033709721,
              -0.343587801,
              -0.513218087,
              -0.5923033129999999,
              -0.431221835,
              5.339202897,
              -0.49377858700000005,
              -0.645000361,
              -0.47798486700000004,
              -0.401579746,
              -0.621782124,
              -0.24939462699999998,
              -0.303365249,
              -0.922343302
            ],
            [
              -0.31807579,
              -0.8141108090000001,
              0.6465451879999999,
              0.26837169,
              -9.425120961000001,
              -1.073853473,
              -2.049589626,
              -0.34692102399999997,
              0.9972831809999999,
              0.30061925300000003,
              -0.543103864,
              -1.150792172,
              -2.283061167,
              -0.162802216,
              -1.053859713,
              -1.377541743,
              -0.288349474,
              -0.922266884,
              -1.123953091,
              -0.7629538929999999,
              -0.6873571479999999,
              0.28991073,
              0.317576672,
              -0.345565515,
              0.541683,
              0.009754099,
              0.73792006,
              -0.6242717520000001,
              0.10053254699999999
            ],
            [
              -0.670177714,
              3.2245335010000002,
              0.145509552,
              0.107432319,
              -1.1204927390000001,
              0.288890539,
              1.5495459180000002,
              -0.342665051,
              -0.017402855,
              -0.42000224399999997,
              -0.36138745299999997,
              -1.264272075,
              -0.794507765,
              -0.619944678,
              -0.338767802,
              -0.14852947800000002,
              -1.078879645,
              0.130939014,
              -1.3078153129999999,
              -1.818798474,
              3.683694337,
              0.920647357,
              -0.847056974,
              -0.34379849799999995,
              -1.21552566,
              -0.8538453340000001,
              -0.357215055,
              -0.043911541,
              -0.955847309
            ],
            [
              -0.695252888,
              4.299877134,
              -0.175587126,
              -0.061022137000000004,
              -0.391646018,
              3.3854510380000002,
              0.345114288,
              -0.505734993,
              -0.482953864,
              -0.081815586,
              -0.928486879,
              0.976209137,
              0.09902148699999999,
              2.494690556,
              -1.0887427790000002,
              0.43717475100000003,
              -0.507169467,
              2.028724319,
              -0.507954247,
              0.14350628099999999,
              -1.19702953,
              0.610379518,
              0.095879151,
              -0.6631187270000001,
              0.50821984,
              -0.741815419,
              2.38531026,
              0.354750355,
              0.658437634
            ],
            [
              -0.337849025,
              -0.535265918,
              0.8031604590000001,
              0.275911465,
              0.981343049,
              -0.748451144,
              -0.092431408,
              -0.32647710399999996,
              -0.38124391700000004,
              -0.575343824,
              -0.63351617,
              -0.380961411,
              -1.7206161969999998,
              -0.85605361,
              -0.5809503739999999,
              0.37329311600000004,
              0.9054908859999999,
              0.135705555,
              1.1077806559999999,
              -0.545183144,
              0.475561701,
              0.016687596000000002,
              -0.172178219,
              0.585186686,
              -0.40480014,
              -3.997318149,
              0.711029765,
              -0.470884061,
              0.354386296
            ],
            [
              -0.36817321700000005,
              0.209192446,
              0.266317555,
              -0.100656799,
              -0.33679171799999996,
              -0.060827204,
              -0.199021599,
              -0.765882671,
              -0.071476548,
              -0.44027029999999995,
              -0.35486840000000003,
              3.468121376,
              5.8537267139999996,
              -0.465135408,
              0.074434692,
              7.085199705,
              -0.399050575,
              -0.334999773,
              -0.623071147,
              -0.40623083299999996,
              0.9390581159999999,
              -0.269533885,
              0.11795050300000001,
              0.1975473,
              -0.365407931,
              -0.056856473,
              0.0019832120000000003,
              0.08160995900000001,
              -0.603299855
            ]
          ],
          "links": [],
          "views": [
            {
              "N_row_sum": "all",
              "dist": "cos",
              "nodes": {
                "row_nodes": [
                  {
                    "group": [
                      10.0,
                      9.0,
                      8.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CDK4",
                    "clust": 14,
                    "cat_0_index": 0,
                    "rank": 30,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 20,
                    "ini": 38
                  },
                  {
                    "group": [
                      21.0,
                      20.0,
                      19.0,
                      13.0,
                      11.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LMTK3",
                    "clust": 20,
                    "cat_0_index": 17,
                    "rank": 28,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 24,
                    "ini": 37
                  },
                  {
                    "group": [
                      26.0,
                      25.0,
                      22.0,
                      16.0,
                      13.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LRRK2",
                    "clust": 26,
                    "cat_0_index": 18,
                    "rank": 9,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 10,
                    "ini": 36
                  },
                  {
                    "group": [
                      28.0,
                      27.0,
                      24.0,
                      18.0,
                      14.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: UHMK1",
                    "clust": 25,
                    "cat_0_index": 19,
                    "rank": 26,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 14,
                    "ini": 35
                  },
                  {
                    "group": [
                      12.0,
                      11.0,
                      10.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: EGFR",
                    "clust": 13,
                    "cat_0_index": 1,
                    "rank": 33,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 7,
                    "ini": 34
                  },
                  {
                    "group": [
                      33.0,
                      32.0,
                      29.0,
                      22.0,
                      17.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK32A",
                    "clust": 32,
                    "cat_0_index": 2,
                    "rank": 36,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 32,
                    "ini": 33
                  },
                  {
                    "group": [
                      11.0,
                      10.0,
                      9.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NRK",
                    "clust": 15,
                    "cat_0_index": 3,
                    "rank": 35,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 33,
                    "ini": 32
                  },
                  {
                    "group": [
                      35.0,
                      34.0,
                      31.0,
                      23.0,
                      18.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ERBB2",
                    "clust": 34,
                    "cat_0_index": 20,
                    "rank": 24,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 9,
                    "ini": 31
                  },
                  {
                    "group": [
                      31.0,
                      30.0,
                      27.0,
                      20.0,
                      16.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ERBB4",
                    "clust": 30,
                    "cat_0_index": 21,
                    "rank": 6,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 2,
                    "ini": 30
                  },
                  {
                    "group": [
                      37.0,
                      36.0,
                      33.0,
                      25.0,
                      19.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: AAK1",
                    "clust": 36,
                    "cat_0_index": 22,
                    "rank": 18,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 8,
                    "ini": 29
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: SRPK3",
                    "clust": 4,
                    "cat_0_index": 23,
                    "rank": 8,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 15,
                    "ini": 28
                  },
                  {
                    "group": [
                      36.0,
                      35.0,
                      32.0,
                      24.0,
                      18.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK39",
                    "clust": 35,
                    "cat_0_index": 4,
                    "rank": 7,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 4,
                    "ini": 27
                  },
                  {
                    "group": [
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: GRK4",
                    "clust": 3,
                    "cat_0_index": 24,
                    "rank": 1,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 3,
                    "ini": 26
                  },
                  {
                    "group": [
                      13.0,
                      12.0,
                      11.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: TBK1",
                    "clust": 12,
                    "cat_0_index": 25,
                    "rank": 34,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 26,
                    "ini": 25
                  },
                  {
                    "group": [
                      23.0,
                      22.0,
                      20.0,
                      14.0,
                      12.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: INSRR",
                    "clust": 23,
                    "cat_0_index": 26,
                    "rank": 13,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 5,
                    "ini": 24
                  },
                  {
                    "group": [
                      14.0,
                      13.0,
                      12.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: IRAK1",
                    "clust": 11,
                    "cat_0_index": 5,
                    "rank": 20,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 30,
                    "ini": 23
                  },
                  {
                    "group": [
                      34.0,
                      33.0,
                      30.0,
                      22.0,
                      17.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: KDR",
                    "clust": 33,
                    "cat_0_index": 27,
                    "rank": 19,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 11,
                    "ini": 22
                  },
                  {
                    "group": [
                      20.0,
                      19.0,
                      18.0,
                      12.0,
                      10.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NPR1",
                    "clust": 16,
                    "cat_0_index": 6,
                    "rank": 27,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 29,
                    "ini": 21
                  },
                  {
                    "group": [
                      16.0,
                      15.0,
                      14.0,
                      9.0,
                      8.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PAK3",
                    "clust": 9,
                    "cat_0_index": 28,
                    "rank": 11,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 12,
                    "ini": 20
                  },
                  {
                    "group": [
                      7.0,
                      6.0,
                      5.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PDGFRA",
                    "clust": 7,
                    "cat_0_index": 7,
                    "rank": 2,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 0,
                    "ini": 19
                  },
                  {
                    "group": [
                      24.0,
                      23.0,
                      20.0,
                      14.0,
                      12.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PDK4",
                    "clust": 24,
                    "cat_0_index": 29,
                    "rank": 22,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 22,
                    "ini": 18
                  },
                  {
                    "group": [
                      29.0,
                      28.0,
                      25.0,
                      19.0,
                      15.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ULK4",
                    "clust": 28,
                    "cat_0_index": 8,
                    "rank": 16,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 19,
                    "ini": 17
                  },
                  {
                    "group": [
                      22.0,
                      21.0,
                      19.0,
                      13.0,
                      11.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PRKCE",
                    "clust": 21,
                    "cat_0_index": 30,
                    "rank": 14,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 1,
                    "ini": 16
                  },
                  {
                    "group": [
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PRKG2",
                    "clust": 2,
                    "cat_0_index": 31,
                    "rank": 25,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 18,
                    "ini": 15
                  },
                  {
                    "group": [
                      17.0,
                      16.0,
                      15.0,
                      10.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAPK4",
                    "clust": 18,
                    "cat_0_index": 9,
                    "rank": 10,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 16,
                    "ini": 14
                  },
                  {
                    "group": [
                      8.0,
                      7.0,
                      6.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAPK11",
                    "clust": 8,
                    "cat_0_index": 10,
                    "rank": 17,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 34,
                    "ini": 13
                  },
                  {
                    "group": [
                      32.0,
                      31.0,
                      28.0,
                      21.0,
                      16.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK31",
                    "clust": 31,
                    "cat_0_index": 11,
                    "rank": 37,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 31,
                    "ini": 12
                  },
                  {
                    "group": [
                      18.0,
                      17.0,
                      16.0,
                      10.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: GRK1",
                    "clust": 19,
                    "cat_0_index": 32,
                    "rank": 15,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 23,
                    "ini": 11
                  },
                  {
                    "group": [
                      38.0,
                      37.0,
                      34.0,
                      26.0,
                      20.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ROS1",
                    "clust": 37,
                    "cat_0_index": 12,
                    "rank": 31,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 37,
                    "ini": 10
                  },
                  {
                    "group": [
                      15.0,
                      14.0,
                      13.0,
                      8.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAP2K4",
                    "clust": 10,
                    "cat_0_index": 13,
                    "rank": 23,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 28,
                    "ini": 9
                  },
                  {
                    "group": [
                      27.0,
                      26.0,
                      23.0,
                      17.0,
                      13.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: SRC",
                    "clust": 27,
                    "cat_0_index": 14,
                    "rank": 21,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 21,
                    "ini": 8
                  },
                  {
                    "group": [
                      19.0,
                      18.0,
                      17.0,
                      11.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: TGFBR1",
                    "clust": 17,
                    "cat_0_index": 15,
                    "rank": 12,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 13,
                    "ini": 7
                  },
                  {
                    "group": [
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CAMK2B",
                    "clust": 5,
                    "cat_0_index": 33,
                    "rank": 3,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 17,
                    "ini": 6
                  },
                  {
                    "group": [
                      9.0,
                      8.0,
                      7.0,
                      4.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK24",
                    "clust": 6,
                    "cat_0_index": 16,
                    "rank": 0,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 36,
                    "ini": 5
                  },
                  {
                    "group": [
                      5.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: DCLK3",
                    "clust": 1,
                    "cat_0_index": 34,
                    "rank": 5,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 25,
                    "ini": 4
                  },
                  {
                    "group": [
                      25.0,
                      24.0,
                      21.0,
                      15.0,
                      12.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LATS1",
                    "clust": 22,
                    "cat_0_index": 35,
                    "rank": 29,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 27,
                    "ini": 3
                  },
                  {
                    "group": [
                      6.0,
                      5.0,
                      4.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NEK9",
                    "clust": 0,
                    "cat_0_index": 36,
                    "rank": 4,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 6,
                    "ini": 2
                  },
                  {
                    "group": [
                      30.0,
                      29.0,
                      26.0,
                      19.0,
                      15.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MYLK3",
                    "clust": 29,
                    "cat_0_index": 37,
                    "rank": 32,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 35,
                    "ini": 1
                  }
                ],
                "col_nodes": [
                  {
                    "group": [
                      15.0,
                      15.0,
                      15.0,
                      15.0,
                      12.0,
                      10.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1650",
                    "clust": 12,
                    "cat_1_index": 10,
                    "cat_0_index": 24,
                    "rank": 6,
                    "cat-1": "Gender: Male",
                    "ini": 29,
                    "cat-0": "Category: two",
                    "rankvar": 4
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H23",
                    "clust": 2,
                    "cat_1_index": 11,
                    "cat_0_index": 25,
                    "rank": 17,
                    "cat-1": "Gender: Male",
                    "ini": 28,
                    "cat-0": "Category: two",
                    "rankvar": 8
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      6.0,
                      6.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CAL-12T",
                    "clust": 4,
                    "cat_1_index": 12,
                    "cat_0_index": 26,
                    "rank": 10,
                    "cat-1": "Gender: Male",
                    "ini": 27,
                    "cat-0": "Category: two",
                    "rankvar": 19
                  },
                  {
                    "group": [
                      27.0,
                      27.0,
                      27.0,
                      26.0,
                      20.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H358",
                    "clust": 25,
                    "cat_1_index": 13,
                    "cat_0_index": 13,
                    "rank": 4,
                    "cat-1": "Gender: Male",
                    "ini": 26,
                    "cat-0": "Category: one",
                    "rankvar": 0
                  },
                  {
                    "group": [
                      28.0,
                      28.0,
                      28.0,
                      27.0,
                      21.0,
                      16.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1975",
                    "clust": 22,
                    "cat_1_index": 0,
                    "cat_0_index": 27,
                    "rank": 0,
                    "cat-1": "Gender: Female",
                    "ini": 25,
                    "cat-0": "Category: two",
                    "rankvar": 24
                  },
                  {
                    "group": [
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC15",
                    "clust": 1,
                    "cat_1_index": 14,
                    "cat_0_index": 28,
                    "rank": 24,
                    "cat-1": "Gender: Male",
                    "ini": 24,
                    "cat-0": "Category: two",
                    "rankvar": 20
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1355",
                    "clust": 5,
                    "cat_1_index": 15,
                    "cat_0_index": 19,
                    "rank": 9,
                    "cat-1": "Gender: Male",
                    "ini": 23,
                    "cat-0": "Category: three",
                    "rankvar": 6
                  },
                  {
                    "group": [
                      22.0,
                      22.0,
                      22.0,
                      22.0,
                      18.0,
                      14.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC827",
                    "clust": 23,
                    "cat_1_index": 1,
                    "cat_0_index": 14,
                    "rank": 28,
                    "cat-1": "Gender: Female",
                    "ini": 22,
                    "cat-0": "Category: one",
                    "rankvar": 25
                  },
                  {
                    "group": [
                      19.0,
                      19.0,
                      19.0,
                      19.0,
                      15.0,
                      12.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2405",
                    "clust": 20,
                    "cat_1_index": 16,
                    "cat_0_index": 0,
                    "rank": 1,
                    "cat-1": "Gender: Male",
                    "ini": 21,
                    "cat-0": "Category: five",
                    "rankvar": 12
                  },
                  {
                    "group": [
                      20.0,
                      20.0,
                      20.0,
                      20.0,
                      16.0,
                      12.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC78",
                    "clust": 21,
                    "cat_1_index": 17,
                    "cat_0_index": 1,
                    "rank": 25,
                    "cat-1": "Gender: Male",
                    "ini": 20,
                    "cat-0": "Category: five",
                    "rankvar": 27
                  },
                  {
                    "group": [
                      11.0,
                      11.0,
                      11.0,
                      11.0,
                      9.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1666",
                    "clust": 7,
                    "cat_1_index": 2,
                    "cat_0_index": 6,
                    "rank": 18,
                    "cat-1": "Gender: Female",
                    "ini": 19,
                    "cat-0": "Category: four",
                    "rankvar": 15
                  },
                  {
                    "group": [
                      18.0,
                      18.0,
                      18.0,
                      18.0,
                      14.0,
                      11.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H661",
                    "clust": 16,
                    "cat_1_index": 18,
                    "cat_0_index": 2,
                    "rank": 3,
                    "cat-1": "Gender: Male",
                    "ini": 18,
                    "cat-0": "Category: five",
                    "rankvar": 26
                  },
                  {
                    "group": [
                      16.0,
                      16.0,
                      16.0,
                      16.0,
                      13.0,
                      11.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H838",
                    "clust": 17,
                    "cat_1_index": 19,
                    "cat_0_index": 3,
                    "rank": 7,
                    "cat-1": "Gender: Male",
                    "ini": 17,
                    "cat-0": "Category: five",
                    "rankvar": 23
                  },
                  {
                    "group": [
                      12.0,
                      12.0,
                      12.0,
                      12.0,
                      10.0,
                      9.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1703",
                    "clust": 14,
                    "cat_1_index": 20,
                    "cat_0_index": 4,
                    "rank": 11,
                    "cat-1": "Gender: Male",
                    "ini": 16,
                    "cat-0": "Category: five",
                    "rankvar": 21
                  },
                  {
                    "group": [
                      21.0,
                      21.0,
                      21.0,
                      21.0,
                      17.0,
                      13.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CALU-3",
                    "clust": 19,
                    "cat_1_index": 21,
                    "cat_0_index": 7,
                    "rank": 8,
                    "cat-1": "Gender: Male",
                    "ini": 15,
                    "cat-0": "Category: four",
                    "rankvar": 7
                  },
                  {
                    "group": [
                      17.0,
                      17.0,
                      17.0,
                      17.0,
                      13.0,
                      11.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2342",
                    "clust": 18,
                    "cat_1_index": 3,
                    "cat_0_index": 8,
                    "rank": 26,
                    "cat-1": "Gender: Female",
                    "ini": 14,
                    "cat-0": "Category: four",
                    "rankvar": 22
                  },
                  {
                    "group": [
                      26.0,
                      26.0,
                      26.0,
                      25.0,
                      19.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2228",
                    "clust": 26,
                    "cat_1_index": 4,
                    "cat_0_index": 15,
                    "rank": 2,
                    "cat-1": "Gender: Female",
                    "ini": 13,
                    "cat-0": "Category: one",
                    "rankvar": 5
                  },
                  {
                    "group": [
                      13.0,
                      13.0,
                      13.0,
                      13.0,
                      10.0,
                      9.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1299",
                    "clust": 15,
                    "cat_1_index": 22,
                    "cat_0_index": 20,
                    "rank": 12,
                    "cat-1": "Gender: Male",
                    "ini": 12,
                    "cat-0": "Category: three",
                    "rankvar": 1
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      9.0,
                      9.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1792",
                    "clust": 10,
                    "cat_1_index": 23,
                    "cat_0_index": 21,
                    "rank": 20,
                    "cat-1": "Gender: Male",
                    "ini": 11,
                    "cat-0": "Category: three",
                    "rankvar": 9
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      10.0,
                      10.0,
                      8.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H460",
                    "clust": 11,
                    "cat_1_index": 24,
                    "cat_0_index": 22,
                    "rank": 5,
                    "cat-1": "Gender: Male",
                    "ini": 10,
                    "cat-0": "Category: three",
                    "rankvar": 11
                  },
                  {
                    "group": [
                      29.0,
                      29.0,
                      29.0,
                      28.0,
                      22.0,
                      17.0,
                      10.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2106",
                    "clust": 0,
                    "cat_1_index": 25,
                    "cat_0_index": 9,
                    "rank": 22,
                    "cat-1": "Gender: Male",
                    "ini": 9,
                    "cat-0": "Category: four",
                    "rankvar": 28
                  },
                  {
                    "group": [
                      24.0,
                      24.0,
                      24.0,
                      24.0,
                      19.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H441",
                    "clust": 27,
                    "cat_1_index": 26,
                    "cat_0_index": 16,
                    "rank": 27,
                    "cat-1": "Gender: Male",
                    "ini": 8,
                    "cat-0": "Category: one",
                    "rankvar": 14
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      7.0,
                      7.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1944",
                    "clust": 8,
                    "cat_1_index": 5,
                    "cat_0_index": 23,
                    "rank": 23,
                    "cat-1": "Gender: Female",
                    "ini": 7,
                    "cat-0": "Category: three",
                    "rankvar": 10
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1437",
                    "clust": 6,
                    "cat_1_index": 27,
                    "cat_0_index": 10,
                    "rank": 16,
                    "cat-1": "Gender: Male",
                    "ini": 6,
                    "cat-0": "Category: four",
                    "rankvar": 17
                  },
                  {
                    "group": [
                      23.0,
                      23.0,
                      23.0,
                      23.0,
                      18.0,
                      14.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1734",
                    "clust": 24,
                    "cat_1_index": 6,
                    "cat_0_index": 17,
                    "rank": 19,
                    "cat-1": "Gender: Female",
                    "ini": 5,
                    "cat-0": "Category: one",
                    "rankvar": 18
                  },
                  {
                    "group": [
                      14.0,
                      14.0,
                      14.0,
                      14.0,
                      11.0,
                      9.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: LOU-NH91",
                    "clust": 13,
                    "cat_1_index": 7,
                    "cat_0_index": 5,
                    "rank": 15,
                    "cat-1": "Gender: Female",
                    "ini": 4,
                    "cat-0": "Category: five",
                    "rankvar": 16
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC44",
                    "clust": 3,
                    "cat_1_index": 8,
                    "cat_0_index": 11,
                    "rank": 14,
                    "cat-1": "Gender: Female",
                    "ini": 3,
                    "cat-0": "Category: four",
                    "rankvar": 2
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      8.0,
                      8.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: A549",
                    "clust": 9,
                    "cat_1_index": 28,
                    "cat_0_index": 12,
                    "rank": 21,
                    "cat-1": "Gender: Male",
                    "ini": 2,
                    "cat-0": "Category: four",
                    "rankvar": 3
                  },
                  {
                    "group": [
                      25.0,
                      25.0,
                      25.0,
                      24.0,
                      19.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1781",
                    "clust": 28,
                    "cat_1_index": 9,
                    "cat_0_index": 18,
                    "rank": 13,
                    "cat-1": "Gender: Female",
                    "ini": 1,
                    "cat-0": "Category: one",
                    "rankvar": 13
                  }
                ]
              }
            },
            {
              "N_row_sum": 20,
              "dist": "cos",
              "nodes": {
                "row_nodes": [
                  {
                    "group": [
                      6.0,
                      6.0,
                      6.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK31",
                    "clust": 5,
                    "cat_0_index": 0,
                    "rank": 19,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 14,
                    "ini": 20
                  },
                  {
                    "group": [
                      19.0,
                      18.0,
                      18.0,
                      14.0,
                      11.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK24",
                    "clust": 18,
                    "cat_0_index": 1,
                    "rank": 0,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 18,
                    "ini": 19
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      7.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK32A",
                    "clust": 6,
                    "cat_0_index": 2,
                    "rank": 18,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 15,
                    "ini": 18
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      8.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NRK",
                    "clust": 9,
                    "cat_0_index": 3,
                    "rank": 17,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 16,
                    "ini": 17
                  },
                  {
                    "group": [
                      11.0,
                      11.0,
                      11.0,
                      8.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: TBK1",
                    "clust": 7,
                    "cat_0_index": 10,
                    "rank": 16,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 10,
                    "ini": 16
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      10.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: EGFR",
                    "clust": 8,
                    "cat_0_index": 4,
                    "rank": 15,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 3,
                    "ini": 15
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MYLK3",
                    "clust": 2,
                    "cat_0_index": 11,
                    "rank": 14,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 17,
                    "ini": 14
                  },
                  {
                    "group": [
                      14.0,
                      14.0,
                      14.0,
                      11.0,
                      8.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ROS1",
                    "clust": 11,
                    "cat_0_index": 5,
                    "rank": 13,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 19,
                    "ini": 13
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      9.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CDK4",
                    "clust": 10,
                    "cat_0_index": 6,
                    "rank": 12,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 8,
                    "ini": 12
                  },
                  {
                    "group": [
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LATS1",
                    "clust": 3,
                    "cat_0_index": 12,
                    "rank": 11,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 11,
                    "ini": 11
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LMTK3",
                    "clust": 0,
                    "cat_0_index": 13,
                    "rank": 10,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 9,
                    "ini": 10
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NPR1",
                    "clust": 1,
                    "cat_0_index": 7,
                    "rank": 9,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 13,
                    "ini": 9
                  },
                  {
                    "group": [
                      12.0,
                      12.0,
                      12.0,
                      9.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: UHMK1",
                    "clust": 12,
                    "cat_0_index": 14,
                    "rank": 8,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 5,
                    "ini": 8
                  },
                  {
                    "group": [
                      17.0,
                      16.0,
                      16.0,
                      12.0,
                      9.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PRKG2",
                    "clust": 15,
                    "cat_0_index": 15,
                    "rank": 7,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 7,
                    "ini": 7
                  },
                  {
                    "group": [
                      15.0,
                      15.0,
                      15.0,
                      12.0,
                      9.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: GRK4",
                    "clust": 16,
                    "cat_0_index": 16,
                    "rank": 1,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 1,
                    "ini": 6
                  },
                  {
                    "group": [
                      20.0,
                      19.0,
                      19.0,
                      15.0,
                      12.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PDGFRA",
                    "clust": 19,
                    "cat_0_index": 8,
                    "rank": 2,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 0,
                    "ini": 5
                  },
                  {
                    "group": [
                      16.0,
                      15.0,
                      15.0,
                      12.0,
                      9.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CAMK2B",
                    "clust": 17,
                    "cat_0_index": 17,
                    "rank": 3,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 6,
                    "ini": 4
                  },
                  {
                    "group": [
                      13.0,
                      13.0,
                      13.0,
                      10.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ERBB2",
                    "clust": 13,
                    "cat_0_index": 18,
                    "rank": 6,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 4,
                    "ini": 3
                  },
                  {
                    "group": [
                      18.0,
                      17.0,
                      17.0,
                      13.0,
                      10.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NEK9",
                    "clust": 14,
                    "cat_0_index": 19,
                    "rank": 4,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 2,
                    "ini": 2
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAP2K4",
                    "clust": 4,
                    "cat_0_index": 9,
                    "rank": 5,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 12,
                    "ini": 1
                  }
                ],
                "col_nodes": [
                  {
                    "group": [
                      14.0,
                      14.0,
                      12.0,
                      8.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1650",
                    "clust": 14,
                    "cat_1_index": 10,
                    "cat_0_index": 24,
                    "rank": 7,
                    "cat-1": "Gender: Male",
                    "ini": 29,
                    "cat-0": "Category: two",
                    "rankvar": 3
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H23",
                    "clust": 7,
                    "cat_1_index": 11,
                    "cat_0_index": 25,
                    "rank": 14,
                    "cat-1": "Gender: Male",
                    "ini": 28,
                    "cat-0": "Category: two",
                    "rankvar": 12
                  },
                  {
                    "group": [
                      20.0,
                      20.0,
                      18.0,
                      13.0,
                      8.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CAL-12T",
                    "clust": 20,
                    "cat_1_index": 12,
                    "cat_0_index": 26,
                    "rank": 21,
                    "cat-1": "Gender: Male",
                    "ini": 27,
                    "cat-0": "Category: two",
                    "rankvar": 18
                  },
                  {
                    "group": [
                      21.0,
                      21.0,
                      19.0,
                      14.0,
                      8.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H358",
                    "clust": 21,
                    "cat_1_index": 13,
                    "cat_0_index": 13,
                    "rank": 15,
                    "cat-1": "Gender: Male",
                    "ini": 26,
                    "cat-0": "Category: one",
                    "rankvar": 2
                  },
                  {
                    "group": [
                      27.0,
                      27.0,
                      24.0,
                      17.0,
                      10.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1975",
                    "clust": 27,
                    "cat_1_index": 0,
                    "cat_0_index": 27,
                    "rank": 1,
                    "cat-1": "Gender: Female",
                    "ini": 25,
                    "cat-0": "Category: two",
                    "rankvar": 27
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC15",
                    "clust": 8,
                    "cat_1_index": 14,
                    "cat_0_index": 28,
                    "rank": 5,
                    "cat-1": "Gender: Male",
                    "ini": 24,
                    "cat-0": "Category: two",
                    "rankvar": 8
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      8.0,
                      5.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1355",
                    "clust": 10,
                    "cat_1_index": 15,
                    "cat_0_index": 19,
                    "rank": 16,
                    "cat-1": "Gender: Male",
                    "ini": 23,
                    "cat-0": "Category: three",
                    "rankvar": 9
                  },
                  {
                    "group": [
                      25.0,
                      25.0,
                      22.0,
                      16.0,
                      9.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC827",
                    "clust": 25,
                    "cat_1_index": 1,
                    "cat_0_index": 14,
                    "rank": 28,
                    "cat-1": "Gender: Female",
                    "ini": 22,
                    "cat-0": "Category: one",
                    "rankvar": 26
                  },
                  {
                    "group": [
                      16.0,
                      16.0,
                      14.0,
                      10.0,
                      6.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2405",
                    "clust": 18,
                    "cat_1_index": 16,
                    "cat_0_index": 0,
                    "rank": 4,
                    "cat-1": "Gender: Male",
                    "ini": 21,
                    "cat-0": "Category: five",
                    "rankvar": 20
                  },
                  {
                    "group": [
                      18.0,
                      18.0,
                      16.0,
                      11.0,
                      6.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC78",
                    "clust": 17,
                    "cat_1_index": 17,
                    "cat_0_index": 1,
                    "rank": 26,
                    "cat-1": "Gender: Male",
                    "ini": 20,
                    "cat-0": "Category: five",
                    "rankvar": 28
                  },
                  {
                    "group": [
                      17.0,
                      17.0,
                      15.0,
                      10.0,
                      6.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1666",
                    "clust": 19,
                    "cat_1_index": 2,
                    "cat_0_index": 6,
                    "rank": 3,
                    "cat-1": "Gender: Female",
                    "ini": 19,
                    "cat-0": "Category: four",
                    "rankvar": 4
                  },
                  {
                    "group": [
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H661",
                    "clust": 1,
                    "cat_1_index": 18,
                    "cat_0_index": 2,
                    "rank": 18,
                    "cat-1": "Gender: Male",
                    "ini": 18,
                    "cat-0": "Category: five",
                    "rankvar": 21
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H838",
                    "clust": 2,
                    "cat_1_index": 19,
                    "cat_0_index": 3,
                    "rank": 11,
                    "cat-1": "Gender: Male",
                    "ini": 17,
                    "cat-0": "Category: five",
                    "rankvar": 23
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      7.0,
                      4.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1703",
                    "clust": 4,
                    "cat_1_index": 20,
                    "cat_0_index": 4,
                    "rank": 10,
                    "cat-1": "Gender: Male",
                    "ini": 16,
                    "cat-0": "Category: five",
                    "rankvar": 15
                  },
                  {
                    "group": [
                      15.0,
                      15.0,
                      13.0,
                      9.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CALU-3",
                    "clust": 15,
                    "cat_1_index": 21,
                    "cat_0_index": 7,
                    "rank": 8,
                    "cat-1": "Gender: Male",
                    "ini": 15,
                    "cat-0": "Category: four",
                    "rankvar": 16
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2342",
                    "clust": 3,
                    "cat_1_index": 3,
                    "cat_0_index": 8,
                    "rank": 27,
                    "cat-1": "Gender: Female",
                    "ini": 14,
                    "cat-0": "Category: four",
                    "rankvar": 24
                  },
                  {
                    "group": [
                      24.0,
                      24.0,
                      21.0,
                      15.0,
                      9.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2228",
                    "clust": 22,
                    "cat_1_index": 4,
                    "cat_0_index": 15,
                    "rank": 12,
                    "cat-1": "Gender: Female",
                    "ini": 13,
                    "cat-0": "Category: one",
                    "rankvar": 11
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1299",
                    "clust": 6,
                    "cat_1_index": 22,
                    "cat_0_index": 20,
                    "rank": 6,
                    "cat-1": "Gender: Male",
                    "ini": 12,
                    "cat-0": "Category: three",
                    "rankvar": 5
                  },
                  {
                    "group": [
                      28.0,
                      28.0,
                      25.0,
                      18.0,
                      11.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1792",
                    "clust": 28,
                    "cat_1_index": 23,
                    "cat_0_index": 21,
                    "rank": 22,
                    "cat-1": "Gender: Male",
                    "ini": 11,
                    "cat-0": "Category: three",
                    "rankvar": 10
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      8.0,
                      5.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H460",
                    "clust": 11,
                    "cat_1_index": 24,
                    "cat_0_index": 22,
                    "rank": 0,
                    "cat-1": "Gender: Male",
                    "ini": 10,
                    "cat-0": "Category: three",
                    "rankvar": 1
                  },
                  {
                    "group": [
                      29.0,
                      29.0,
                      26.0,
                      19.0,
                      12.0,
                      8.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2106",
                    "clust": 0,
                    "cat_1_index": 25,
                    "cat_0_index": 9,
                    "rank": 20,
                    "cat-1": "Gender: Male",
                    "ini": 9,
                    "cat-0": "Category: four",
                    "rankvar": 25
                  },
                  {
                    "group": [
                      22.0,
                      22.0,
                      20.0,
                      15.0,
                      9.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H441",
                    "clust": 23,
                    "cat_1_index": 26,
                    "cat_0_index": 16,
                    "rank": 24,
                    "cat-1": "Gender: Male",
                    "ini": 8,
                    "cat-0": "Category: one",
                    "rankvar": 13
                  },
                  {
                    "group": [
                      12.0,
                      12.0,
                      10.0,
                      6.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1944",
                    "clust": 12,
                    "cat_1_index": 5,
                    "cat_0_index": 23,
                    "rank": 19,
                    "cat-1": "Gender: Female",
                    "ini": 7,
                    "cat-0": "Category: three",
                    "rankvar": 7
                  },
                  {
                    "group": [
                      11.0,
                      11.0,
                      9.0,
                      5.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1437",
                    "clust": 9,
                    "cat_1_index": 27,
                    "cat_0_index": 10,
                    "rank": 17,
                    "cat-1": "Gender: Male",
                    "ini": 6,
                    "cat-0": "Category: four",
                    "rankvar": 22
                  },
                  {
                    "group": [
                      26.0,
                      26.0,
                      23.0,
                      16.0,
                      9.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1734",
                    "clust": 26,
                    "cat_1_index": 6,
                    "cat_0_index": 17,
                    "rank": 25,
                    "cat-1": "Gender: Female",
                    "ini": 5,
                    "cat-0": "Category: one",
                    "rankvar": 19
                  },
                  {
                    "group": [
                      19.0,
                      19.0,
                      17.0,
                      12.0,
                      7.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: LOU-NH91",
                    "clust": 16,
                    "cat_1_index": 7,
                    "cat_0_index": 5,
                    "rank": 2,
                    "cat-1": "Gender: Female",
                    "ini": 4,
                    "cat-0": "Category: five",
                    "rankvar": 14
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      6.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC44",
                    "clust": 5,
                    "cat_1_index": 8,
                    "cat_0_index": 11,
                    "rank": 13,
                    "cat-1": "Gender: Female",
                    "ini": 3,
                    "cat-0": "Category: four",
                    "rankvar": 6
                  },
                  {
                    "group": [
                      13.0,
                      13.0,
                      11.0,
                      7.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: A549",
                    "clust": 13,
                    "cat_1_index": 28,
                    "cat_0_index": 12,
                    "rank": 9,
                    "cat-1": "Gender: Male",
                    "ini": 2,
                    "cat-0": "Category: four",
                    "rankvar": 0
                  },
                  {
                    "group": [
                      23.0,
                      23.0,
                      20.0,
                      15.0,
                      9.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1781",
                    "clust": 24,
                    "cat_1_index": 9,
                    "cat_0_index": 18,
                    "rank": 23,
                    "cat-1": "Gender: Female",
                    "ini": 1,
                    "cat-0": "Category: one",
                    "rankvar": 17
                  }
                ]
              }
            },
            {
              "N_row_sum": 10,
              "dist": "cos",
              "nodes": {
                "row_nodes": [
                  {
                    "group": [
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK31",
                    "clust": 4,
                    "cat_0_index": 0,
                    "rank": 9,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 4,
                    "ini": 10
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK24",
                    "clust": 0,
                    "cat_0_index": 1,
                    "rank": 0,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 8,
                    "ini": 9
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK32A",
                    "clust": 5,
                    "cat_0_index": 2,
                    "rank": 8,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 5,
                    "ini": 8
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      4.0,
                      4.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NRK",
                    "clust": 8,
                    "cat_0_index": 3,
                    "rank": 7,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 6,
                    "ini": 7
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      8.0,
                      8.0,
                      5.0,
                      4.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: TBK1",
                    "clust": 6,
                    "cat_0_index": 7,
                    "rank": 6,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 2,
                    "ini": 6
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      7.0,
                      7.0,
                      4.0,
                      4.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: EGFR",
                    "clust": 7,
                    "cat_0_index": 4,
                    "rank": 5,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 0,
                    "ini": 5
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      9.0,
                      9.0,
                      6.0,
                      5.0,
                      4.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MYLK3",
                    "clust": 3,
                    "cat_0_index": 8,
                    "rank": 4,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 7,
                    "ini": 4
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ROS1",
                    "clust": 1,
                    "cat_0_index": 5,
                    "rank": 3,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 9,
                    "ini": 3
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      6.0,
                      6.0,
                      4.0,
                      4.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CDK4",
                    "clust": 9,
                    "cat_0_index": 6,
                    "rank": 2,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 1,
                    "ini": 2
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      10.0,
                      10.0,
                      7.0,
                      6.0,
                      5.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LATS1",
                    "clust": 2,
                    "cat_0_index": 9,
                    "rank": 1,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 3,
                    "ini": 1
                  }
                ],
                "col_nodes": [
                  {
                    "group": [
                      28.0,
                      23.0,
                      17.0,
                      11.0,
                      7.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1650",
                    "clust": 27,
                    "cat_1_index": 10,
                    "cat_0_index": 24,
                    "rank": 7,
                    "cat-1": "Gender: Male",
                    "ini": 29,
                    "cat-0": "Category: two",
                    "rankvar": 9
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H23",
                    "clust": 6,
                    "cat_1_index": 11,
                    "cat_0_index": 25,
                    "rank": 19,
                    "cat-1": "Gender: Male",
                    "ini": 28,
                    "cat-0": "Category: two",
                    "rankvar": 20
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CAL-12T",
                    "clust": 0,
                    "cat_1_index": 12,
                    "cat_0_index": 26,
                    "rank": 6,
                    "cat-1": "Gender: Male",
                    "ini": 27,
                    "cat-0": "Category: two",
                    "rankvar": 4
                  },
                  {
                    "group": [
                      26.0,
                      21.0,
                      16.0,
                      10.0,
                      6.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H358",
                    "clust": 25,
                    "cat_1_index": 13,
                    "cat_0_index": 13,
                    "rank": 11,
                    "cat-1": "Gender: Male",
                    "ini": 26,
                    "cat-0": "Category: one",
                    "rankvar": 0
                  },
                  {
                    "group": [
                      13.0,
                      10.0,
                      7.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1975",
                    "clust": 12,
                    "cat_1_index": 0,
                    "cat_0_index": 27,
                    "rank": 0,
                    "cat-1": "Gender: Female",
                    "ini": 25,
                    "cat-0": "Category: two",
                    "rankvar": 27
                  },
                  {
                    "group": [
                      8.0,
                      6.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC15",
                    "clust": 8,
                    "cat_1_index": 14,
                    "cat_0_index": 28,
                    "rank": 13,
                    "cat-1": "Gender: Male",
                    "ini": 24,
                    "cat-0": "Category: two",
                    "rankvar": 16
                  },
                  {
                    "group": [
                      14.0,
                      11.0,
                      7.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1355",
                    "clust": 13,
                    "cat_1_index": 15,
                    "cat_0_index": 19,
                    "rank": 4,
                    "cat-1": "Gender: Male",
                    "ini": 23,
                    "cat-0": "Category: three",
                    "rankvar": 8
                  },
                  {
                    "group": [
                      29.0,
                      24.0,
                      18.0,
                      12.0,
                      7.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC827",
                    "clust": 28,
                    "cat_1_index": 1,
                    "cat_0_index": 14,
                    "rank": 28,
                    "cat-1": "Gender: Female",
                    "ini": 22,
                    "cat-0": "Category: one",
                    "rankvar": 26
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2405",
                    "clust": 3,
                    "cat_1_index": 16,
                    "cat_0_index": 0,
                    "rank": 18,
                    "cat-1": "Gender: Male",
                    "ini": 21,
                    "cat-0": "Category: five",
                    "rankvar": 10
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC78",
                    "clust": 4,
                    "cat_1_index": 17,
                    "cat_0_index": 1,
                    "rank": 27,
                    "cat-1": "Gender: Male",
                    "ini": 20,
                    "cat-0": "Category: five",
                    "rankvar": 28
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1666",
                    "clust": 1,
                    "cat_1_index": 2,
                    "cat_0_index": 6,
                    "rank": 5,
                    "cat-1": "Gender: Female",
                    "ini": 19,
                    "cat-0": "Category: four",
                    "rankvar": 7
                  },
                  {
                    "group": [
                      22.0,
                      19.0,
                      14.0,
                      9.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H661",
                    "clust": 19,
                    "cat_1_index": 18,
                    "cat_0_index": 2,
                    "rank": 22,
                    "cat-1": "Gender: Male",
                    "ini": 18,
                    "cat-0": "Category: five",
                    "rankvar": 23
                  },
                  {
                    "group": [
                      20.0,
                      17.0,
                      13.0,
                      9.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H838",
                    "clust": 20,
                    "cat_1_index": 19,
                    "cat_0_index": 3,
                    "rank": 20,
                    "cat-1": "Gender: Male",
                    "ini": 17,
                    "cat-0": "Category: five",
                    "rankvar": 24
                  },
                  {
                    "group": [
                      9.0,
                      6.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1703",
                    "clust": 9,
                    "cat_1_index": 20,
                    "cat_0_index": 4,
                    "rank": 12,
                    "cat-1": "Gender: Male",
                    "ini": 16,
                    "cat-0": "Category: five",
                    "rankvar": 13
                  },
                  {
                    "group": [
                      17.0,
                      14.0,
                      10.0,
                      7.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CALU-3",
                    "clust": 17,
                    "cat_1_index": 21,
                    "cat_0_index": 7,
                    "rank": 9,
                    "cat-1": "Gender: Male",
                    "ini": 15,
                    "cat-0": "Category: four",
                    "rankvar": 5
                  },
                  {
                    "group": [
                      21.0,
                      18.0,
                      13.0,
                      9.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2342",
                    "clust": 21,
                    "cat_1_index": 3,
                    "cat_0_index": 8,
                    "rank": 26,
                    "cat-1": "Gender: Female",
                    "ini": 14,
                    "cat-0": "Category: four",
                    "rankvar": 25
                  },
                  {
                    "group": [
                      23.0,
                      20.0,
                      15.0,
                      10.0,
                      6.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2228",
                    "clust": 23,
                    "cat_1_index": 4,
                    "cat_0_index": 15,
                    "rank": 21,
                    "cat-1": "Gender: Female",
                    "ini": 13,
                    "cat-0": "Category: one",
                    "rankvar": 19
                  },
                  {
                    "group": [
                      7.0,
                      6.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1299",
                    "clust": 7,
                    "cat_1_index": 22,
                    "cat_0_index": 20,
                    "rank": 8,
                    "cat-1": "Gender: Male",
                    "ini": 12,
                    "cat-0": "Category: three",
                    "rankvar": 12
                  },
                  {
                    "group": [
                      15.0,
                      12.0,
                      8.0,
                      6.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1792",
                    "clust": 14,
                    "cat_1_index": 23,
                    "cat_0_index": 21,
                    "rank": 15,
                    "cat-1": "Gender: Male",
                    "ini": 11,
                    "cat-0": "Category: three",
                    "rankvar": 17
                  },
                  {
                    "group": [
                      11.0,
                      8.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H460",
                    "clust": 10,
                    "cat_1_index": 24,
                    "cat_0_index": 22,
                    "rank": 2,
                    "cat-1": "Gender: Male",
                    "ini": 10,
                    "cat-0": "Category: three",
                    "rankvar": 3
                  },
                  {
                    "group": [
                      18.0,
                      15.0,
                      11.0,
                      7.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2106",
                    "clust": 18,
                    "cat_1_index": 25,
                    "cat_0_index": 9,
                    "rank": 3,
                    "cat-1": "Gender: Male",
                    "ini": 9,
                    "cat-0": "Category: four",
                    "rankvar": 14
                  },
                  {
                    "group": [
                      25.0,
                      20.0,
                      15.0,
                      10.0,
                      6.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H441",
                    "clust": 22,
                    "cat_1_index": 26,
                    "cat_0_index": 16,
                    "rank": 23,
                    "cat-1": "Gender: Male",
                    "ini": 8,
                    "cat-0": "Category: one",
                    "rankvar": 18
                  },
                  {
                    "group": [
                      12.0,
                      9.0,
                      6.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1944",
                    "clust": 11,
                    "cat_1_index": 5,
                    "cat_0_index": 23,
                    "rank": 16,
                    "cat-1": "Gender: Female",
                    "ini": 7,
                    "cat-0": "Category: three",
                    "rankvar": 15
                  },
                  {
                    "group": [
                      19.0,
                      16.0,
                      12.0,
                      8.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1437",
                    "clust": 16,
                    "cat_1_index": 27,
                    "cat_0_index": 10,
                    "rank": 1,
                    "cat-1": "Gender: Male",
                    "ini": 6,
                    "cat-0": "Category: four",
                    "rankvar": 1
                  },
                  {
                    "group": [
                      27.0,
                      22.0,
                      16.0,
                      10.0,
                      6.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1734",
                    "clust": 26,
                    "cat_1_index": 6,
                    "cat_0_index": 17,
                    "rank": 25,
                    "cat-1": "Gender: Female",
                    "ini": 5,
                    "cat-0": "Category: one",
                    "rankvar": 22
                  },
                  {
                    "group": [
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: LOU-NH91",
                    "clust": 2,
                    "cat_1_index": 7,
                    "cat_0_index": 5,
                    "rank": 14,
                    "cat-1": "Gender: Female",
                    "ini": 4,
                    "cat-0": "Category: five",
                    "rankvar": 6
                  },
                  {
                    "group": [
                      10.0,
                      7.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC44",
                    "clust": 5,
                    "cat_1_index": 8,
                    "cat_0_index": 11,
                    "rank": 17,
                    "cat-1": "Gender: Female",
                    "ini": 3,
                    "cat-0": "Category: four",
                    "rankvar": 11
                  },
                  {
                    "group": [
                      16.0,
                      13.0,
                      9.0,
                      6.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: A549",
                    "clust": 15,
                    "cat_1_index": 28,
                    "cat_0_index": 12,
                    "rank": 10,
                    "cat-1": "Gender: Male",
                    "ini": 2,
                    "cat-0": "Category: four",
                    "rankvar": 2
                  },
                  {
                    "group": [
                      24.0,
                      20.0,
                      15.0,
                      10.0,
                      6.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1781",
                    "clust": 24,
                    "cat_1_index": 9,
                    "cat_0_index": 18,
                    "rank": 24,
                    "cat-1": "Gender: Female",
                    "ini": 1,
                    "cat-0": "Category: one",
                    "rankvar": 21
                  }
                ]
              }
            },
            {
              "N_row_var": "all",
              "nodes": {
                "row_nodes": [
                  {
                    "group": [
                      10.0,
                      9.0,
                      8.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CDK4",
                    "clust": 14,
                    "cat_0_index": 0,
                    "rank": 30,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 20,
                    "ini": 38
                  },
                  {
                    "group": [
                      21.0,
                      20.0,
                      19.0,
                      13.0,
                      11.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LMTK3",
                    "clust": 20,
                    "cat_0_index": 17,
                    "rank": 28,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 24,
                    "ini": 37
                  },
                  {
                    "group": [
                      26.0,
                      25.0,
                      22.0,
                      16.0,
                      13.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LRRK2",
                    "clust": 26,
                    "cat_0_index": 18,
                    "rank": 9,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 10,
                    "ini": 36
                  },
                  {
                    "group": [
                      28.0,
                      27.0,
                      24.0,
                      18.0,
                      14.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: UHMK1",
                    "clust": 25,
                    "cat_0_index": 19,
                    "rank": 26,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 14,
                    "ini": 35
                  },
                  {
                    "group": [
                      12.0,
                      11.0,
                      10.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: EGFR",
                    "clust": 13,
                    "cat_0_index": 1,
                    "rank": 33,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 7,
                    "ini": 34
                  },
                  {
                    "group": [
                      33.0,
                      32.0,
                      29.0,
                      22.0,
                      17.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK32A",
                    "clust": 32,
                    "cat_0_index": 2,
                    "rank": 36,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 32,
                    "ini": 33
                  },
                  {
                    "group": [
                      11.0,
                      10.0,
                      9.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NRK",
                    "clust": 15,
                    "cat_0_index": 3,
                    "rank": 35,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 33,
                    "ini": 32
                  },
                  {
                    "group": [
                      35.0,
                      34.0,
                      31.0,
                      23.0,
                      18.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ERBB2",
                    "clust": 34,
                    "cat_0_index": 20,
                    "rank": 24,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 9,
                    "ini": 31
                  },
                  {
                    "group": [
                      31.0,
                      30.0,
                      27.0,
                      20.0,
                      16.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ERBB4",
                    "clust": 30,
                    "cat_0_index": 21,
                    "rank": 6,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 2,
                    "ini": 30
                  },
                  {
                    "group": [
                      37.0,
                      36.0,
                      33.0,
                      25.0,
                      19.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: AAK1",
                    "clust": 36,
                    "cat_0_index": 22,
                    "rank": 18,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 8,
                    "ini": 29
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: SRPK3",
                    "clust": 4,
                    "cat_0_index": 23,
                    "rank": 8,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 15,
                    "ini": 28
                  },
                  {
                    "group": [
                      36.0,
                      35.0,
                      32.0,
                      24.0,
                      18.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK39",
                    "clust": 35,
                    "cat_0_index": 4,
                    "rank": 7,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 4,
                    "ini": 27
                  },
                  {
                    "group": [
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: GRK4",
                    "clust": 3,
                    "cat_0_index": 24,
                    "rank": 1,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 3,
                    "ini": 26
                  },
                  {
                    "group": [
                      13.0,
                      12.0,
                      11.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: TBK1",
                    "clust": 12,
                    "cat_0_index": 25,
                    "rank": 34,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 26,
                    "ini": 25
                  },
                  {
                    "group": [
                      23.0,
                      22.0,
                      20.0,
                      14.0,
                      12.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: INSRR",
                    "clust": 23,
                    "cat_0_index": 26,
                    "rank": 13,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 5,
                    "ini": 24
                  },
                  {
                    "group": [
                      14.0,
                      13.0,
                      12.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: IRAK1",
                    "clust": 11,
                    "cat_0_index": 5,
                    "rank": 20,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 30,
                    "ini": 23
                  },
                  {
                    "group": [
                      34.0,
                      33.0,
                      30.0,
                      22.0,
                      17.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: KDR",
                    "clust": 33,
                    "cat_0_index": 27,
                    "rank": 19,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 11,
                    "ini": 22
                  },
                  {
                    "group": [
                      20.0,
                      19.0,
                      18.0,
                      12.0,
                      10.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NPR1",
                    "clust": 16,
                    "cat_0_index": 6,
                    "rank": 27,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 29,
                    "ini": 21
                  },
                  {
                    "group": [
                      16.0,
                      15.0,
                      14.0,
                      9.0,
                      8.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PAK3",
                    "clust": 9,
                    "cat_0_index": 28,
                    "rank": 11,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 12,
                    "ini": 20
                  },
                  {
                    "group": [
                      7.0,
                      6.0,
                      5.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PDGFRA",
                    "clust": 7,
                    "cat_0_index": 7,
                    "rank": 2,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 0,
                    "ini": 19
                  },
                  {
                    "group": [
                      24.0,
                      23.0,
                      20.0,
                      14.0,
                      12.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PDK4",
                    "clust": 24,
                    "cat_0_index": 29,
                    "rank": 22,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 22,
                    "ini": 18
                  },
                  {
                    "group": [
                      29.0,
                      28.0,
                      25.0,
                      19.0,
                      15.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ULK4",
                    "clust": 28,
                    "cat_0_index": 8,
                    "rank": 16,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 19,
                    "ini": 17
                  },
                  {
                    "group": [
                      22.0,
                      21.0,
                      19.0,
                      13.0,
                      11.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PRKCE",
                    "clust": 21,
                    "cat_0_index": 30,
                    "rank": 14,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 1,
                    "ini": 16
                  },
                  {
                    "group": [
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PRKG2",
                    "clust": 2,
                    "cat_0_index": 31,
                    "rank": 25,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 18,
                    "ini": 15
                  },
                  {
                    "group": [
                      17.0,
                      16.0,
                      15.0,
                      10.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAPK4",
                    "clust": 18,
                    "cat_0_index": 9,
                    "rank": 10,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 16,
                    "ini": 14
                  },
                  {
                    "group": [
                      8.0,
                      7.0,
                      6.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAPK11",
                    "clust": 8,
                    "cat_0_index": 10,
                    "rank": 17,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 34,
                    "ini": 13
                  },
                  {
                    "group": [
                      32.0,
                      31.0,
                      28.0,
                      21.0,
                      16.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK31",
                    "clust": 31,
                    "cat_0_index": 11,
                    "rank": 37,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 31,
                    "ini": 12
                  },
                  {
                    "group": [
                      18.0,
                      17.0,
                      16.0,
                      10.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: GRK1",
                    "clust": 19,
                    "cat_0_index": 32,
                    "rank": 15,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 23,
                    "ini": 11
                  },
                  {
                    "group": [
                      38.0,
                      37.0,
                      34.0,
                      26.0,
                      20.0,
                      8.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ROS1",
                    "clust": 37,
                    "cat_0_index": 12,
                    "rank": 31,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 37,
                    "ini": 10
                  },
                  {
                    "group": [
                      15.0,
                      14.0,
                      13.0,
                      8.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAP2K4",
                    "clust": 10,
                    "cat_0_index": 13,
                    "rank": 23,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 28,
                    "ini": 9
                  },
                  {
                    "group": [
                      27.0,
                      26.0,
                      23.0,
                      17.0,
                      13.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: SRC",
                    "clust": 27,
                    "cat_0_index": 14,
                    "rank": 21,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 21,
                    "ini": 8
                  },
                  {
                    "group": [
                      19.0,
                      18.0,
                      17.0,
                      11.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: TGFBR1",
                    "clust": 17,
                    "cat_0_index": 15,
                    "rank": 12,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 13,
                    "ini": 7
                  },
                  {
                    "group": [
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CAMK2B",
                    "clust": 5,
                    "cat_0_index": 33,
                    "rank": 3,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 17,
                    "ini": 6
                  },
                  {
                    "group": [
                      9.0,
                      8.0,
                      7.0,
                      4.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK24",
                    "clust": 6,
                    "cat_0_index": 16,
                    "rank": 0,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 36,
                    "ini": 5
                  },
                  {
                    "group": [
                      5.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: DCLK3",
                    "clust": 1,
                    "cat_0_index": 34,
                    "rank": 5,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 25,
                    "ini": 4
                  },
                  {
                    "group": [
                      25.0,
                      24.0,
                      21.0,
                      15.0,
                      12.0,
                      6.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LATS1",
                    "clust": 22,
                    "cat_0_index": 35,
                    "rank": 29,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 27,
                    "ini": 3
                  },
                  {
                    "group": [
                      6.0,
                      5.0,
                      4.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NEK9",
                    "clust": 0,
                    "cat_0_index": 36,
                    "rank": 4,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 6,
                    "ini": 2
                  },
                  {
                    "group": [
                      30.0,
                      29.0,
                      26.0,
                      19.0,
                      15.0,
                      7.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MYLK3",
                    "clust": 29,
                    "cat_0_index": 37,
                    "rank": 32,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 35,
                    "ini": 1
                  }
                ],
                "col_nodes": [
                  {
                    "group": [
                      15.0,
                      15.0,
                      15.0,
                      15.0,
                      12.0,
                      10.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1650",
                    "clust": 12,
                    "cat_1_index": 10,
                    "cat_0_index": 24,
                    "rank": 6,
                    "cat-1": "Gender: Male",
                    "ini": 29,
                    "cat-0": "Category: two",
                    "rankvar": 4
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H23",
                    "clust": 2,
                    "cat_1_index": 11,
                    "cat_0_index": 25,
                    "rank": 17,
                    "cat-1": "Gender: Male",
                    "ini": 28,
                    "cat-0": "Category: two",
                    "rankvar": 8
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      6.0,
                      6.0,
                      5.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CAL-12T",
                    "clust": 4,
                    "cat_1_index": 12,
                    "cat_0_index": 26,
                    "rank": 10,
                    "cat-1": "Gender: Male",
                    "ini": 27,
                    "cat-0": "Category: two",
                    "rankvar": 19
                  },
                  {
                    "group": [
                      27.0,
                      27.0,
                      27.0,
                      26.0,
                      20.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H358",
                    "clust": 25,
                    "cat_1_index": 13,
                    "cat_0_index": 13,
                    "rank": 4,
                    "cat-1": "Gender: Male",
                    "ini": 26,
                    "cat-0": "Category: one",
                    "rankvar": 0
                  },
                  {
                    "group": [
                      28.0,
                      28.0,
                      28.0,
                      27.0,
                      21.0,
                      16.0,
                      9.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1975",
                    "clust": 22,
                    "cat_1_index": 0,
                    "cat_0_index": 27,
                    "rank": 0,
                    "cat-1": "Gender: Female",
                    "ini": 25,
                    "cat-0": "Category: two",
                    "rankvar": 24
                  },
                  {
                    "group": [
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC15",
                    "clust": 1,
                    "cat_1_index": 14,
                    "cat_0_index": 28,
                    "rank": 24,
                    "cat-1": "Gender: Male",
                    "ini": 24,
                    "cat-0": "Category: two",
                    "rankvar": 20
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1355",
                    "clust": 5,
                    "cat_1_index": 15,
                    "cat_0_index": 19,
                    "rank": 9,
                    "cat-1": "Gender: Male",
                    "ini": 23,
                    "cat-0": "Category: three",
                    "rankvar": 6
                  },
                  {
                    "group": [
                      22.0,
                      22.0,
                      22.0,
                      22.0,
                      18.0,
                      14.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC827",
                    "clust": 23,
                    "cat_1_index": 1,
                    "cat_0_index": 14,
                    "rank": 28,
                    "cat-1": "Gender: Female",
                    "ini": 22,
                    "cat-0": "Category: one",
                    "rankvar": 25
                  },
                  {
                    "group": [
                      19.0,
                      19.0,
                      19.0,
                      19.0,
                      15.0,
                      12.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2405",
                    "clust": 20,
                    "cat_1_index": 16,
                    "cat_0_index": 0,
                    "rank": 1,
                    "cat-1": "Gender: Male",
                    "ini": 21,
                    "cat-0": "Category: five",
                    "rankvar": 12
                  },
                  {
                    "group": [
                      20.0,
                      20.0,
                      20.0,
                      20.0,
                      16.0,
                      12.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC78",
                    "clust": 21,
                    "cat_1_index": 17,
                    "cat_0_index": 1,
                    "rank": 25,
                    "cat-1": "Gender: Male",
                    "ini": 20,
                    "cat-0": "Category: five",
                    "rankvar": 27
                  },
                  {
                    "group": [
                      11.0,
                      11.0,
                      11.0,
                      11.0,
                      9.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1666",
                    "clust": 7,
                    "cat_1_index": 2,
                    "cat_0_index": 6,
                    "rank": 18,
                    "cat-1": "Gender: Female",
                    "ini": 19,
                    "cat-0": "Category: four",
                    "rankvar": 15
                  },
                  {
                    "group": [
                      18.0,
                      18.0,
                      18.0,
                      18.0,
                      14.0,
                      11.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H661",
                    "clust": 16,
                    "cat_1_index": 18,
                    "cat_0_index": 2,
                    "rank": 3,
                    "cat-1": "Gender: Male",
                    "ini": 18,
                    "cat-0": "Category: five",
                    "rankvar": 26
                  },
                  {
                    "group": [
                      16.0,
                      16.0,
                      16.0,
                      16.0,
                      13.0,
                      11.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H838",
                    "clust": 17,
                    "cat_1_index": 19,
                    "cat_0_index": 3,
                    "rank": 7,
                    "cat-1": "Gender: Male",
                    "ini": 17,
                    "cat-0": "Category: five",
                    "rankvar": 23
                  },
                  {
                    "group": [
                      12.0,
                      12.0,
                      12.0,
                      12.0,
                      10.0,
                      9.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1703",
                    "clust": 14,
                    "cat_1_index": 20,
                    "cat_0_index": 4,
                    "rank": 11,
                    "cat-1": "Gender: Male",
                    "ini": 16,
                    "cat-0": "Category: five",
                    "rankvar": 21
                  },
                  {
                    "group": [
                      21.0,
                      21.0,
                      21.0,
                      21.0,
                      17.0,
                      13.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CALU-3",
                    "clust": 19,
                    "cat_1_index": 21,
                    "cat_0_index": 7,
                    "rank": 8,
                    "cat-1": "Gender: Male",
                    "ini": 15,
                    "cat-0": "Category: four",
                    "rankvar": 7
                  },
                  {
                    "group": [
                      17.0,
                      17.0,
                      17.0,
                      17.0,
                      13.0,
                      11.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2342",
                    "clust": 18,
                    "cat_1_index": 3,
                    "cat_0_index": 8,
                    "rank": 26,
                    "cat-1": "Gender: Female",
                    "ini": 14,
                    "cat-0": "Category: four",
                    "rankvar": 22
                  },
                  {
                    "group": [
                      26.0,
                      26.0,
                      26.0,
                      25.0,
                      19.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2228",
                    "clust": 26,
                    "cat_1_index": 4,
                    "cat_0_index": 15,
                    "rank": 2,
                    "cat-1": "Gender: Female",
                    "ini": 13,
                    "cat-0": "Category: one",
                    "rankvar": 5
                  },
                  {
                    "group": [
                      13.0,
                      13.0,
                      13.0,
                      13.0,
                      10.0,
                      9.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1299",
                    "clust": 15,
                    "cat_1_index": 22,
                    "cat_0_index": 20,
                    "rank": 12,
                    "cat-1": "Gender: Male",
                    "ini": 12,
                    "cat-0": "Category: three",
                    "rankvar": 1
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      9.0,
                      9.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1792",
                    "clust": 10,
                    "cat_1_index": 23,
                    "cat_0_index": 21,
                    "rank": 20,
                    "cat-1": "Gender: Male",
                    "ini": 11,
                    "cat-0": "Category: three",
                    "rankvar": 9
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      10.0,
                      10.0,
                      8.0,
                      7.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H460",
                    "clust": 11,
                    "cat_1_index": 24,
                    "cat_0_index": 22,
                    "rank": 5,
                    "cat-1": "Gender: Male",
                    "ini": 10,
                    "cat-0": "Category: three",
                    "rankvar": 11
                  },
                  {
                    "group": [
                      29.0,
                      29.0,
                      29.0,
                      28.0,
                      22.0,
                      17.0,
                      10.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2106",
                    "clust": 0,
                    "cat_1_index": 25,
                    "cat_0_index": 9,
                    "rank": 22,
                    "cat-1": "Gender: Male",
                    "ini": 9,
                    "cat-0": "Category: four",
                    "rankvar": 28
                  },
                  {
                    "group": [
                      24.0,
                      24.0,
                      24.0,
                      24.0,
                      19.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H441",
                    "clust": 27,
                    "cat_1_index": 26,
                    "cat_0_index": 16,
                    "rank": 27,
                    "cat-1": "Gender: Male",
                    "ini": 8,
                    "cat-0": "Category: one",
                    "rankvar": 14
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      7.0,
                      7.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1944",
                    "clust": 8,
                    "cat_1_index": 5,
                    "cat_0_index": 23,
                    "rank": 23,
                    "cat-1": "Gender: Female",
                    "ini": 7,
                    "cat-0": "Category: three",
                    "rankvar": 10
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1437",
                    "clust": 6,
                    "cat_1_index": 27,
                    "cat_0_index": 10,
                    "rank": 16,
                    "cat-1": "Gender: Male",
                    "ini": 6,
                    "cat-0": "Category: four",
                    "rankvar": 17
                  },
                  {
                    "group": [
                      23.0,
                      23.0,
                      23.0,
                      23.0,
                      18.0,
                      14.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1734",
                    "clust": 24,
                    "cat_1_index": 6,
                    "cat_0_index": 17,
                    "rank": 19,
                    "cat-1": "Gender: Female",
                    "ini": 5,
                    "cat-0": "Category: one",
                    "rankvar": 18
                  },
                  {
                    "group": [
                      14.0,
                      14.0,
                      14.0,
                      14.0,
                      11.0,
                      9.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: LOU-NH91",
                    "clust": 13,
                    "cat_1_index": 7,
                    "cat_0_index": 5,
                    "rank": 15,
                    "cat-1": "Gender: Female",
                    "ini": 4,
                    "cat-0": "Category: five",
                    "rankvar": 16
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC44",
                    "clust": 3,
                    "cat_1_index": 8,
                    "cat_0_index": 11,
                    "rank": 14,
                    "cat-1": "Gender: Female",
                    "ini": 3,
                    "cat-0": "Category: four",
                    "rankvar": 2
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      8.0,
                      8.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: A549",
                    "clust": 9,
                    "cat_1_index": 28,
                    "cat_0_index": 12,
                    "rank": 21,
                    "cat-1": "Gender: Male",
                    "ini": 2,
                    "cat-0": "Category: four",
                    "rankvar": 3
                  },
                  {
                    "group": [
                      25.0,
                      25.0,
                      25.0,
                      24.0,
                      19.0,
                      15.0,
                      8.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1781",
                    "clust": 28,
                    "cat_1_index": 9,
                    "cat_0_index": 18,
                    "rank": 13,
                    "cat-1": "Gender: Female",
                    "ini": 1,
                    "cat-0": "Category: one",
                    "rankvar": 13
                  }
                ]
              },
              "dist": "cos"
            },
            {
              "N_row_var": 20,
              "nodes": {
                "row_nodes": [
                  {
                    "group": [
                      20.0,
                      20.0,
                      20.0,
                      18.0,
                      15.0,
                      12.0,
                      7.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ROS1",
                    "clust": 17,
                    "cat_0_index": 0,
                    "rank": 14,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 19,
                    "ini": 20
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK24",
                    "clust": 0,
                    "cat_0_index": 1,
                    "rank": 0,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 18,
                    "ini": 19
                  },
                  {
                    "group": [
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MYLK3",
                    "clust": 2,
                    "cat_0_index": 12,
                    "rank": 15,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 17,
                    "ini": 18
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAPK11",
                    "clust": 1,
                    "cat_0_index": 2,
                    "rank": 4,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 16,
                    "ini": 17
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      7.0,
                      6.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NRK",
                    "clust": 8,
                    "cat_0_index": 3,
                    "rank": 17,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 15,
                    "ini": 16
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      5.0,
                      4.0,
                      4.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK32A",
                    "clust": 5,
                    "cat_0_index": 4,
                    "rank": 18,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 14,
                    "ini": 15
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      6.0,
                      5.0,
                      4.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK31",
                    "clust": 6,
                    "cat_0_index": 5,
                    "rank": 19,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 13,
                    "ini": 14
                  },
                  {
                    "group": [
                      17.0,
                      17.0,
                      17.0,
                      15.0,
                      12.0,
                      10.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: IRAK1",
                    "clust": 14,
                    "cat_0_index": 6,
                    "rank": 5,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 12,
                    "ini": 13
                  },
                  {
                    "group": [
                      18.0,
                      18.0,
                      18.0,
                      16.0,
                      13.0,
                      11.0,
                      6.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NPR1",
                    "clust": 18,
                    "cat_0_index": 7,
                    "rank": 10,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 11,
                    "ini": 12
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      10.0,
                      8.0,
                      6.0,
                      5.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAP2K4",
                    "clust": 4,
                    "cat_0_index": 8,
                    "rank": 8,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 10,
                    "ini": 11
                  },
                  {
                    "group": [
                      13.0,
                      13.0,
                      13.0,
                      11.0,
                      8.0,
                      7.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LATS1",
                    "clust": 12,
                    "cat_0_index": 13,
                    "rank": 12,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 9,
                    "ini": 10
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      9.0,
                      7.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: TBK1",
                    "clust": 7,
                    "cat_0_index": 14,
                    "rank": 16,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 8,
                    "ini": 9
                  },
                  {
                    "group": [
                      11.0,
                      11.0,
                      11.0,
                      9.0,
                      7.0,
                      6.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: DCLK3",
                    "clust": 10,
                    "cat_0_index": 15,
                    "rank": 1,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 7,
                    "ini": 8
                  },
                  {
                    "group": [
                      19.0,
                      19.0,
                      19.0,
                      17.0,
                      14.0,
                      11.0,
                      6.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: LMTK3",
                    "clust": 19,
                    "cat_0_index": 16,
                    "rank": 11,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 6,
                    "ini": 7
                  },
                  {
                    "group": [
                      15.0,
                      15.0,
                      15.0,
                      13.0,
                      10.0,
                      8.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: GRK1",
                    "clust": 15,
                    "cat_0_index": 17,
                    "rank": 2,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 5,
                    "ini": 6
                  },
                  {
                    "group": [
                      14.0,
                      14.0,
                      14.0,
                      12.0,
                      9.0,
                      7.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PDK4",
                    "clust": 13,
                    "cat_0_index": 18,
                    "rank": 7,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 4,
                    "ini": 5
                  },
                  {
                    "group": [
                      16.0,
                      16.0,
                      16.0,
                      14.0,
                      11.0,
                      9.0,
                      5.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: SRC",
                    "clust": 16,
                    "cat_0_index": 9,
                    "rank": 6,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 3,
                    "ini": 4
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      8.0,
                      6.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: CDK4",
                    "clust": 9,
                    "cat_0_index": 10,
                    "rank": 13,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 2,
                    "ini": 3
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      4.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ULK4",
                    "clust": 3,
                    "cat_0_index": 11,
                    "rank": 3,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 1,
                    "ini": 2
                  },
                  {
                    "group": [
                      12.0,
                      12.0,
                      12.0,
                      10.0,
                      7.0,
                      6.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: PRKG2",
                    "clust": 11,
                    "cat_0_index": 19,
                    "rank": 9,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 0,
                    "ini": 1
                  }
                ],
                "col_nodes": [
                  {
                    "group": [
                      4.0,
                      4.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1650",
                    "clust": 0,
                    "cat_1_index": 10,
                    "cat_0_index": 24,
                    "rank": 2,
                    "cat-1": "Gender: Male",
                    "ini": 29,
                    "cat-0": "Category: two",
                    "rankvar": 2
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      7.0,
                      6.0,
                      4.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H23",
                    "clust": 8,
                    "cat_1_index": 11,
                    "cat_0_index": 25,
                    "rank": 24,
                    "cat-1": "Gender: Male",
                    "ini": 28,
                    "cat-0": "Category: two",
                    "rankvar": 13
                  },
                  {
                    "group": [
                      17.0,
                      17.0,
                      16.0,
                      11.0,
                      7.0,
                      6.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CAL-12T",
                    "clust": 17,
                    "cat_1_index": 12,
                    "cat_0_index": 26,
                    "rank": 10,
                    "cat-1": "Gender: Male",
                    "ini": 27,
                    "cat-0": "Category: two",
                    "rankvar": 15
                  },
                  {
                    "group": [
                      18.0,
                      18.0,
                      17.0,
                      12.0,
                      7.0,
                      6.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H358",
                    "clust": 18,
                    "cat_1_index": 13,
                    "cat_0_index": 13,
                    "rank": 8,
                    "cat-1": "Gender: Male",
                    "ini": 26,
                    "cat-0": "Category: one",
                    "rankvar": 3
                  },
                  {
                    "group": [
                      29.0,
                      29.0,
                      27.0,
                      20.0,
                      14.0,
                      10.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1975",
                    "clust": 23,
                    "cat_1_index": 0,
                    "cat_0_index": 27,
                    "rank": 0,
                    "cat-1": "Gender: Female",
                    "ini": 25,
                    "cat-0": "Category: two",
                    "rankvar": 26
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      9.0,
                      7.0,
                      4.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC15",
                    "clust": 7,
                    "cat_1_index": 14,
                    "cat_0_index": 28,
                    "rank": 22,
                    "cat-1": "Gender: Male",
                    "ini": 24,
                    "cat-0": "Category: two",
                    "rankvar": 21
                  },
                  {
                    "group": [
                      15.0,
                      15.0,
                      14.0,
                      10.0,
                      6.0,
                      5.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1355",
                    "clust": 15,
                    "cat_1_index": 15,
                    "cat_0_index": 19,
                    "rank": 9,
                    "cat-1": "Gender: Male",
                    "ini": 23,
                    "cat-0": "Category: three",
                    "rankvar": 11
                  },
                  {
                    "group": [
                      24.0,
                      24.0,
                      23.0,
                      18.0,
                      12.0,
                      9.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC827",
                    "clust": 24,
                    "cat_1_index": 1,
                    "cat_0_index": 14,
                    "rank": 28,
                    "cat-1": "Gender: Female",
                    "ini": 22,
                    "cat-0": "Category: one",
                    "rankvar": 25
                  },
                  {
                    "group": [
                      22.0,
                      22.0,
                      21.0,
                      16.0,
                      10.0,
                      8.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2405",
                    "clust": 21,
                    "cat_1_index": 16,
                    "cat_0_index": 0,
                    "rank": 1,
                    "cat-1": "Gender: Male",
                    "ini": 21,
                    "cat-0": "Category: five",
                    "rankvar": 17
                  },
                  {
                    "group": [
                      23.0,
                      23.0,
                      22.0,
                      17.0,
                      11.0,
                      8.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC78",
                    "clust": 22,
                    "cat_1_index": 17,
                    "cat_0_index": 1,
                    "rank": 26,
                    "cat-1": "Gender: Male",
                    "ini": 20,
                    "cat-0": "Category: five",
                    "rankvar": 28
                  },
                  {
                    "group": [
                      20.0,
                      20.0,
                      19.0,
                      14.0,
                      9.0,
                      8.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1666",
                    "clust": 19,
                    "cat_1_index": 2,
                    "cat_0_index": 6,
                    "rank": 6,
                    "cat-1": "Gender: Female",
                    "ini": 19,
                    "cat-0": "Category: four",
                    "rankvar": 8
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      6.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H661",
                    "clust": 4,
                    "cat_1_index": 18,
                    "cat_0_index": 2,
                    "rank": 7,
                    "cat-1": "Gender: Male",
                    "ini": 18,
                    "cat-0": "Category: five",
                    "rankvar": 27
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      4.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H838",
                    "clust": 5,
                    "cat_1_index": 19,
                    "cat_0_index": 3,
                    "rank": 20,
                    "cat-1": "Gender: Male",
                    "ini": 17,
                    "cat-0": "Category: five",
                    "rankvar": 23
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1703",
                    "clust": 2,
                    "cat_1_index": 20,
                    "cat_0_index": 4,
                    "rank": 17,
                    "cat-1": "Gender: Male",
                    "ini": 16,
                    "cat-0": "Category: five",
                    "rankvar": 19
                  },
                  {
                    "group": [
                      21.0,
                      21.0,
                      20.0,
                      15.0,
                      9.0,
                      8.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CALU-3",
                    "clust": 20,
                    "cat_1_index": 21,
                    "cat_0_index": 7,
                    "rank": 3,
                    "cat-1": "Gender: Male",
                    "ini": 15,
                    "cat-0": "Category: four",
                    "rankvar": 1
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2342",
                    "clust": 6,
                    "cat_1_index": 3,
                    "cat_0_index": 8,
                    "rank": 27,
                    "cat-1": "Gender: Female",
                    "ini": 14,
                    "cat-0": "Category: four",
                    "rankvar": 24
                  },
                  {
                    "group": [
                      28.0,
                      28.0,
                      26.0,
                      19.0,
                      13.0,
                      9.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2228",
                    "clust": 26,
                    "cat_1_index": 4,
                    "cat_0_index": 15,
                    "rank": 4,
                    "cat-1": "Gender: Female",
                    "ini": 13,
                    "cat-0": "Category: one",
                    "rankvar": 9
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1299",
                    "clust": 3,
                    "cat_1_index": 22,
                    "cat_0_index": 20,
                    "rank": 13,
                    "cat-1": "Gender: Male",
                    "ini": 12,
                    "cat-0": "Category: three",
                    "rankvar": 4
                  },
                  {
                    "group": [
                      13.0,
                      13.0,
                      12.0,
                      8.0,
                      5.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1792",
                    "clust": 11,
                    "cat_1_index": 23,
                    "cat_0_index": 21,
                    "rank": 12,
                    "cat-1": "Gender: Male",
                    "ini": 11,
                    "cat-0": "Category: three",
                    "rankvar": 14
                  },
                  {
                    "group": [
                      11.0,
                      11.0,
                      10.0,
                      8.0,
                      5.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H460",
                    "clust": 12,
                    "cat_1_index": 24,
                    "cat_0_index": 22,
                    "rank": 5,
                    "cat-1": "Gender: Male",
                    "ini": 10,
                    "cat-0": "Category: three",
                    "rankvar": 7
                  },
                  {
                    "group": [
                      19.0,
                      19.0,
                      18.0,
                      13.0,
                      8.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2106",
                    "clust": 14,
                    "cat_1_index": 25,
                    "cat_0_index": 9,
                    "rank": 14,
                    "cat-1": "Gender: Male",
                    "ini": 9,
                    "cat-0": "Category: four",
                    "rankvar": 18
                  },
                  {
                    "group": [
                      26.0,
                      26.0,
                      25.0,
                      19.0,
                      13.0,
                      9.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H441",
                    "clust": 27,
                    "cat_1_index": 26,
                    "cat_0_index": 16,
                    "rank": 25,
                    "cat-1": "Gender: Male",
                    "ini": 8,
                    "cat-0": "Category: one",
                    "rankvar": 10
                  },
                  {
                    "group": [
                      14.0,
                      14.0,
                      13.0,
                      9.0,
                      5.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1944",
                    "clust": 10,
                    "cat_1_index": 5,
                    "cat_0_index": 23,
                    "rank": 23,
                    "cat-1": "Gender: Female",
                    "ini": 7,
                    "cat-0": "Category: three",
                    "rankvar": 5
                  },
                  {
                    "group": [
                      16.0,
                      16.0,
                      15.0,
                      10.0,
                      6.0,
                      5.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1437",
                    "clust": 16,
                    "cat_1_index": 27,
                    "cat_0_index": 10,
                    "rank": 15,
                    "cat-1": "Gender: Male",
                    "ini": 6,
                    "cat-0": "Category: four",
                    "rankvar": 20
                  },
                  {
                    "group": [
                      25.0,
                      25.0,
                      24.0,
                      18.0,
                      12.0,
                      9.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1734",
                    "clust": 25,
                    "cat_1_index": 6,
                    "cat_0_index": 17,
                    "rank": 18,
                    "cat-1": "Gender: Female",
                    "ini": 5,
                    "cat-0": "Category: one",
                    "rankvar": 22
                  },
                  {
                    "group": [
                      3.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: LOU-NH91",
                    "clust": 1,
                    "cat_1_index": 7,
                    "cat_0_index": 5,
                    "rank": 19,
                    "cat-1": "Gender: Female",
                    "ini": 4,
                    "cat-0": "Category: five",
                    "rankvar": 12
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      8.0,
                      6.0,
                      4.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC44",
                    "clust": 9,
                    "cat_1_index": 8,
                    "cat_0_index": 11,
                    "rank": 11,
                    "cat-1": "Gender: Female",
                    "ini": 3,
                    "cat-0": "Category: four",
                    "rankvar": 0
                  },
                  {
                    "group": [
                      12.0,
                      12.0,
                      11.0,
                      8.0,
                      5.0,
                      4.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: A549",
                    "clust": 13,
                    "cat_1_index": 28,
                    "cat_0_index": 12,
                    "rank": 21,
                    "cat-1": "Gender: Male",
                    "ini": 2,
                    "cat-0": "Category: four",
                    "rankvar": 6
                  },
                  {
                    "group": [
                      27.0,
                      27.0,
                      25.0,
                      19.0,
                      13.0,
                      9.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1781",
                    "clust": 28,
                    "cat_1_index": 9,
                    "cat_0_index": 18,
                    "rank": 16,
                    "cat-1": "Gender: Female",
                    "ini": 1,
                    "cat-0": "Category: one",
                    "rankvar": 16
                  }
                ]
              },
              "dist": "cos"
            },
            {
              "N_row_var": 10,
              "nodes": {
                "row_nodes": [
                  {
                    "group": [
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: ROS1",
                    "clust": 3,
                    "cat_0_index": 0,
                    "rank": 5,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 9,
                    "ini": 10
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK24",
                    "clust": 0,
                    "cat_0_index": 1,
                    "rank": 0,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 8,
                    "ini": 9
                  },
                  {
                    "group": [
                      9.0,
                      9.0,
                      9.0,
                      9.0,
                      8.0,
                      7.0,
                      6.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MYLK3",
                    "clust": 5,
                    "cat_0_index": 9,
                    "rank": 6,
                    "cat-0": "Gene Type: Not Interesting",
                    "rankvar": 7,
                    "ini": 8
                  },
                  {
                    "group": [
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAPK11",
                    "clust": 1,
                    "cat_0_index": 2,
                    "rank": 1,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 6,
                    "ini": 7
                  },
                  {
                    "group": [
                      7.0,
                      7.0,
                      7.0,
                      7.0,
                      6.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NRK",
                    "clust": 7,
                    "cat_0_index": 3,
                    "rank": 7,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 5,
                    "ini": 6
                  },
                  {
                    "group": [
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK32A",
                    "clust": 8,
                    "cat_0_index": 4,
                    "rank": 8,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 4,
                    "ini": 5
                  },
                  {
                    "group": [
                      6.0,
                      6.0,
                      6.0,
                      6.0,
                      5.0,
                      5.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: STK31",
                    "clust": 9,
                    "cat_0_index": 5,
                    "rank": 9,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 3,
                    "ini": 4
                  },
                  {
                    "group": [
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      4.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: IRAK1",
                    "clust": 4,
                    "cat_0_index": 6,
                    "rank": 2,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 2,
                    "ini": 3
                  },
                  {
                    "group": [
                      10.0,
                      10.0,
                      10.0,
                      10.0,
                      9.0,
                      8.0,
                      7.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: NPR1",
                    "clust": 2,
                    "cat_0_index": 7,
                    "rank": 4,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 1,
                    "ini": 2
                  },
                  {
                    "group": [
                      8.0,
                      8.0,
                      8.0,
                      8.0,
                      7.0,
                      6.0,
                      5.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Gene: MAP2K4",
                    "clust": 6,
                    "cat_0_index": 8,
                    "rank": 3,
                    "cat-0": "Gene Type: Interesting",
                    "rankvar": 0,
                    "ini": 1
                  }
                ],
                "col_nodes": [
                  {
                    "group": [
                      4.0,
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1650",
                    "clust": 0,
                    "cat_1_index": 10,
                    "cat_0_index": 24,
                    "rank": 17,
                    "cat-1": "Gender: Male",
                    "ini": 29,
                    "cat-0": "Category: two",
                    "rankvar": 9
                  },
                  {
                    "group": [
                      11.0,
                      9.0,
                      6.0,
                      4.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H23",
                    "clust": 10,
                    "cat_1_index": 11,
                    "cat_0_index": 25,
                    "rank": 9,
                    "cat-1": "Gender: Male",
                    "ini": 28,
                    "cat-0": "Category: two",
                    "rankvar": 5
                  },
                  {
                    "group": [
                      12.0,
                      10.0,
                      7.0,
                      4.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CAL-12T",
                    "clust": 11,
                    "cat_1_index": 12,
                    "cat_0_index": 26,
                    "rank": 11,
                    "cat-1": "Gender: Male",
                    "ini": 27,
                    "cat-0": "Category: two",
                    "rankvar": 2
                  },
                  {
                    "group": [
                      24.0,
                      20.0,
                      14.0,
                      9.0,
                      5.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H358",
                    "clust": 21,
                    "cat_1_index": 13,
                    "cat_0_index": 13,
                    "rank": 13,
                    "cat-1": "Gender: Male",
                    "ini": 26,
                    "cat-0": "Category: one",
                    "rankvar": 3
                  },
                  {
                    "group": [
                      27.0,
                      23.0,
                      16.0,
                      11.0,
                      6.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1975",
                    "clust": 27,
                    "cat_1_index": 0,
                    "cat_0_index": 27,
                    "rank": 0,
                    "cat-1": "Gender: Female",
                    "ini": 25,
                    "cat-0": "Category: two",
                    "rankvar": 27
                  },
                  {
                    "group": [
                      28.0,
                      24.0,
                      17.0,
                      11.0,
                      6.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC15",
                    "clust": 28,
                    "cat_1_index": 14,
                    "cat_0_index": 28,
                    "rank": 1,
                    "cat-1": "Gender: Male",
                    "ini": 24,
                    "cat-0": "Category: two",
                    "rankvar": 1
                  },
                  {
                    "group": [
                      10.0,
                      8.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1355",
                    "clust": 7,
                    "cat_1_index": 15,
                    "cat_0_index": 19,
                    "rank": 8,
                    "cat-1": "Gender: Male",
                    "ini": 23,
                    "cat-0": "Category: three",
                    "rankvar": 17
                  },
                  {
                    "group": [
                      22.0,
                      19.0,
                      13.0,
                      9.0,
                      5.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC827",
                    "clust": 22,
                    "cat_1_index": 1,
                    "cat_0_index": 14,
                    "rank": 25,
                    "cat-1": "Gender: Female",
                    "ini": 22,
                    "cat-0": "Category: one",
                    "rankvar": 24
                  },
                  {
                    "group": [
                      13.0,
                      11.0,
                      8.0,
                      5.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2405",
                    "clust": 13,
                    "cat_1_index": 16,
                    "cat_0_index": 0,
                    "rank": 3,
                    "cat-1": "Gender: Male",
                    "ini": 21,
                    "cat-0": "Category: five",
                    "rankvar": 19
                  },
                  {
                    "group": [
                      15.0,
                      13.0,
                      9.0,
                      6.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC78",
                    "clust": 12,
                    "cat_1_index": 17,
                    "cat_0_index": 1,
                    "rank": 28,
                    "cat-1": "Gender: Male",
                    "ini": 20,
                    "cat-0": "Category: five",
                    "rankvar": 28
                  },
                  {
                    "group": [
                      14.0,
                      12.0,
                      8.0,
                      5.0,
                      3.0,
                      3.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1666",
                    "clust": 14,
                    "cat_1_index": 2,
                    "cat_0_index": 6,
                    "rank": 4,
                    "cat-1": "Gender: Female",
                    "ini": 19,
                    "cat-0": "Category: four",
                    "rankvar": 8
                  },
                  {
                    "group": [
                      18.0,
                      16.0,
                      11.0,
                      8.0,
                      4.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H661",
                    "clust": 15,
                    "cat_1_index": 18,
                    "cat_0_index": 2,
                    "rank": 18,
                    "cat-1": "Gender: Male",
                    "ini": 18,
                    "cat-0": "Category: five",
                    "rankvar": 26
                  },
                  {
                    "group": [
                      16.0,
                      14.0,
                      10.0,
                      7.0,
                      4.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H838",
                    "clust": 16,
                    "cat_1_index": 19,
                    "cat_0_index": 3,
                    "rank": 19,
                    "cat-1": "Gender: Male",
                    "ini": 17,
                    "cat-0": "Category: five",
                    "rankvar": 23
                  },
                  {
                    "group": [
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1703",
                    "clust": 2,
                    "cat_1_index": 20,
                    "cat_0_index": 4,
                    "rank": 21,
                    "cat-1": "Gender: Male",
                    "ini": 16,
                    "cat-0": "Category: five",
                    "rankvar": 21
                  },
                  {
                    "group": [
                      25.0,
                      21.0,
                      15.0,
                      10.0,
                      6.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: CALU-3",
                    "clust": 24,
                    "cat_1_index": 21,
                    "cat_0_index": 7,
                    "rank": 5,
                    "cat-1": "Gender: Male",
                    "ini": 15,
                    "cat-0": "Category: four",
                    "rankvar": 7
                  },
                  {
                    "group": [
                      17.0,
                      15.0,
                      10.0,
                      7.0,
                      4.0,
                      4.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2342",
                    "clust": 17,
                    "cat_1_index": 3,
                    "cat_0_index": 8,
                    "rank": 27,
                    "cat-1": "Gender: Female",
                    "ini": 14,
                    "cat-0": "Category: four",
                    "rankvar": 25
                  },
                  {
                    "group": [
                      19.0,
                      17.0,
                      12.0,
                      9.0,
                      5.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2228",
                    "clust": 19,
                    "cat_1_index": 4,
                    "cat_0_index": 15,
                    "rank": 16,
                    "cat-1": "Gender: Female",
                    "ini": 13,
                    "cat-0": "Category: one",
                    "rankvar": 16
                  },
                  {
                    "group": [
                      3.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1299",
                    "clust": 1,
                    "cat_1_index": 22,
                    "cat_0_index": 20,
                    "rank": 10,
                    "cat-1": "Gender: Male",
                    "ini": 12,
                    "cat-0": "Category: three",
                    "rankvar": 11
                  },
                  {
                    "group": [
                      29.0,
                      25.0,
                      18.0,
                      11.0,
                      6.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1792",
                    "clust": 26,
                    "cat_1_index": 23,
                    "cat_0_index": 21,
                    "rank": 2,
                    "cat-1": "Gender: Male",
                    "ini": 11,
                    "cat-0": "Category: three",
                    "rankvar": 10
                  },
                  {
                    "group": [
                      8.0,
                      7.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H460",
                    "clust": 8,
                    "cat_1_index": 24,
                    "cat_0_index": 22,
                    "rank": 7,
                    "cat-1": "Gender: Male",
                    "ini": 10,
                    "cat-0": "Category: three",
                    "rankvar": 13
                  },
                  {
                    "group": [
                      26.0,
                      22.0,
                      15.0,
                      10.0,
                      6.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H2106",
                    "clust": 25,
                    "cat_1_index": 25,
                    "cat_0_index": 9,
                    "rank": 6,
                    "cat-1": "Gender: Male",
                    "ini": 9,
                    "cat-0": "Category: four",
                    "rankvar": 12
                  },
                  {
                    "group": [
                      21.0,
                      18.0,
                      12.0,
                      9.0,
                      5.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H441",
                    "clust": 18,
                    "cat_1_index": 26,
                    "cat_0_index": 16,
                    "rank": 26,
                    "cat-1": "Gender: Male",
                    "ini": 8,
                    "cat-0": "Category: one",
                    "rankvar": 15
                  },
                  {
                    "group": [
                      5.0,
                      4.0,
                      3.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1944",
                    "clust": 5,
                    "cat_1_index": 5,
                    "cat_0_index": 23,
                    "rank": 14,
                    "cat-1": "Gender: Female",
                    "ini": 7,
                    "cat-0": "Category: three",
                    "rankvar": 4
                  },
                  {
                    "group": [
                      9.0,
                      7.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1437",
                    "clust": 9,
                    "cat_1_index": 27,
                    "cat_0_index": 10,
                    "rank": 20,
                    "cat-1": "Gender: Male",
                    "ini": 6,
                    "cat-0": "Category: four",
                    "rankvar": 22
                  },
                  {
                    "group": [
                      23.0,
                      19.0,
                      13.0,
                      9.0,
                      5.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1734",
                    "clust": 23,
                    "cat_1_index": 6,
                    "cat_0_index": 17,
                    "rank": 23,
                    "cat-1": "Gender: Female",
                    "ini": 5,
                    "cat-0": "Category: one",
                    "rankvar": 20
                  },
                  {
                    "group": [
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: LOU-NH91",
                    "clust": 3,
                    "cat_1_index": 7,
                    "cat_0_index": 5,
                    "rank": 22,
                    "cat-1": "Gender: Female",
                    "ini": 4,
                    "cat-0": "Category: five",
                    "rankvar": 14
                  },
                  {
                    "group": [
                      7.0,
                      6.0,
                      4.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: HCC44",
                    "clust": 4,
                    "cat_1_index": 8,
                    "cat_0_index": 11,
                    "rank": 15,
                    "cat-1": "Gender: Female",
                    "ini": 3,
                    "cat-0": "Category: four",
                    "rankvar": 0
                  },
                  {
                    "group": [
                      6.0,
                      5.0,
                      3.0,
                      2.0,
                      2.0,
                      2.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: A549",
                    "clust": 6,
                    "cat_1_index": 28,
                    "cat_0_index": 12,
                    "rank": 12,
                    "cat-1": "Gender: Male",
                    "ini": 2,
                    "cat-0": "Category: four",
                    "rankvar": 6
                  },
                  {
                    "group": [
                      20.0,
                      17.0,
                      12.0,
                      9.0,
                      5.0,
                      5.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0,
                      1.0
                    ],
                    "name": "Cell Line: H1781",
                    "clust": 20,
                    "cat_1_index": 9,
                    "cat_0_index": 18,
                    "rank": 24,
                    "cat-1": "Gender: Female",
                    "ini": 1,
                    "cat-0": "Category: one",
                    "rankvar": 18
                  }
                ]
              },
              "dist": "cos"
            }
          ],
          "cat_colors": {
            "col": {
              "cat-0": {
                "Category: five": "#98df8a",
                "Category: four": "#404040",
                "Category: one": "#c5b0d5",
                "Category: two": "#FFDB58",
                "Category: three": "#1f77b4"
              },
              "cat-1": {
                "Gender: Male": "#98df8a",
                "Gender: Female": "#ff7f0e"
              }
            },
            "row": {
              "cat-0": {
                "Gene Type: Interesting": "#393b79",
                "Gene Type: Not Interesting": "#eee"
              }
            }
          },
          "row_nodes": [
            {
              "group": [
                10.0,
                9.0,
                8.0,
                5.0,
                5.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: CDK4",
              "clust": 14,
              "cat_0_index": 0,
              "rank": 30,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 20,
              "ini": 38
            },
            {
              "group": [
                21.0,
                20.0,
                19.0,
                13.0,
                11.0,
                5.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: LMTK3",
              "clust": 20,
              "cat_0_index": 17,
              "rank": 28,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 24,
              "ini": 37
            },
            {
              "group": [
                26.0,
                25.0,
                22.0,
                16.0,
                13.0,
                6.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: LRRK2",
              "clust": 26,
              "cat_0_index": 18,
              "rank": 9,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 10,
              "ini": 36
            },
            {
              "group": [
                28.0,
                27.0,
                24.0,
                18.0,
                14.0,
                6.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: UHMK1",
              "clust": 25,
              "cat_0_index": 19,
              "rank": 26,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 14,
              "ini": 35
            },
            {
              "group": [
                12.0,
                11.0,
                10.0,
                5.0,
                5.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: EGFR",
              "clust": 13,
              "cat_0_index": 1,
              "rank": 33,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 7,
              "ini": 34
            },
            {
              "group": [
                33.0,
                32.0,
                29.0,
                22.0,
                17.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: STK32A",
              "clust": 32,
              "cat_0_index": 2,
              "rank": 36,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 32,
              "ini": 33
            },
            {
              "group": [
                11.0,
                10.0,
                9.0,
                5.0,
                5.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: NRK",
              "clust": 15,
              "cat_0_index": 3,
              "rank": 35,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 33,
              "ini": 32
            },
            {
              "group": [
                35.0,
                34.0,
                31.0,
                23.0,
                18.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: ERBB2",
              "clust": 34,
              "cat_0_index": 20,
              "rank": 24,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 9,
              "ini": 31
            },
            {
              "group": [
                31.0,
                30.0,
                27.0,
                20.0,
                16.0,
                7.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: ERBB4",
              "clust": 30,
              "cat_0_index": 21,
              "rank": 6,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 2,
              "ini": 30
            },
            {
              "group": [
                37.0,
                36.0,
                33.0,
                25.0,
                19.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: AAK1",
              "clust": 36,
              "cat_0_index": 22,
              "rank": 18,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 8,
              "ini": 29
            },
            {
              "group": [
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: SRPK3",
              "clust": 4,
              "cat_0_index": 23,
              "rank": 8,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 15,
              "ini": 28
            },
            {
              "group": [
                36.0,
                35.0,
                32.0,
                24.0,
                18.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: STK39",
              "clust": 35,
              "cat_0_index": 4,
              "rank": 7,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 4,
              "ini": 27
            },
            {
              "group": [
                3.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: GRK4",
              "clust": 3,
              "cat_0_index": 24,
              "rank": 1,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 3,
              "ini": 26
            },
            {
              "group": [
                13.0,
                12.0,
                11.0,
                6.0,
                5.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: TBK1",
              "clust": 12,
              "cat_0_index": 25,
              "rank": 34,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 26,
              "ini": 25
            },
            {
              "group": [
                23.0,
                22.0,
                20.0,
                14.0,
                12.0,
                6.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: INSRR",
              "clust": 23,
              "cat_0_index": 26,
              "rank": 13,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 5,
              "ini": 24
            },
            {
              "group": [
                14.0,
                13.0,
                12.0,
                7.0,
                6.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: IRAK1",
              "clust": 11,
              "cat_0_index": 5,
              "rank": 20,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 30,
              "ini": 23
            },
            {
              "group": [
                34.0,
                33.0,
                30.0,
                22.0,
                17.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: KDR",
              "clust": 33,
              "cat_0_index": 27,
              "rank": 19,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 11,
              "ini": 22
            },
            {
              "group": [
                20.0,
                19.0,
                18.0,
                12.0,
                10.0,
                4.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: NPR1",
              "clust": 16,
              "cat_0_index": 6,
              "rank": 27,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 29,
              "ini": 21
            },
            {
              "group": [
                16.0,
                15.0,
                14.0,
                9.0,
                8.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: PAK3",
              "clust": 9,
              "cat_0_index": 28,
              "rank": 11,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 12,
              "ini": 20
            },
            {
              "group": [
                7.0,
                6.0,
                5.0,
                3.0,
                3.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: PDGFRA",
              "clust": 7,
              "cat_0_index": 7,
              "rank": 2,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 0,
              "ini": 19
            },
            {
              "group": [
                24.0,
                23.0,
                20.0,
                14.0,
                12.0,
                6.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: PDK4",
              "clust": 24,
              "cat_0_index": 29,
              "rank": 22,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 22,
              "ini": 18
            },
            {
              "group": [
                29.0,
                28.0,
                25.0,
                19.0,
                15.0,
                7.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: ULK4",
              "clust": 28,
              "cat_0_index": 8,
              "rank": 16,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 19,
              "ini": 17
            },
            {
              "group": [
                22.0,
                21.0,
                19.0,
                13.0,
                11.0,
                5.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: PRKCE",
              "clust": 21,
              "cat_0_index": 30,
              "rank": 14,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 1,
              "ini": 16
            },
            {
              "group": [
                4.0,
                3.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: PRKG2",
              "clust": 2,
              "cat_0_index": 31,
              "rank": 25,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 18,
              "ini": 15
            },
            {
              "group": [
                17.0,
                16.0,
                15.0,
                10.0,
                9.0,
                4.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: MAPK4",
              "clust": 18,
              "cat_0_index": 9,
              "rank": 10,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 16,
              "ini": 14
            },
            {
              "group": [
                8.0,
                7.0,
                6.0,
                3.0,
                3.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: MAPK11",
              "clust": 8,
              "cat_0_index": 10,
              "rank": 17,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 34,
              "ini": 13
            },
            {
              "group": [
                32.0,
                31.0,
                28.0,
                21.0,
                16.0,
                7.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: STK31",
              "clust": 31,
              "cat_0_index": 11,
              "rank": 37,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 31,
              "ini": 12
            },
            {
              "group": [
                18.0,
                17.0,
                16.0,
                10.0,
                9.0,
                4.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: GRK1",
              "clust": 19,
              "cat_0_index": 32,
              "rank": 15,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 23,
              "ini": 11
            },
            {
              "group": [
                38.0,
                37.0,
                34.0,
                26.0,
                20.0,
                8.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: ROS1",
              "clust": 37,
              "cat_0_index": 12,
              "rank": 31,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 37,
              "ini": 10
            },
            {
              "group": [
                15.0,
                14.0,
                13.0,
                8.0,
                7.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: MAP2K4",
              "clust": 10,
              "cat_0_index": 13,
              "rank": 23,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 28,
              "ini": 9
            },
            {
              "group": [
                27.0,
                26.0,
                23.0,
                17.0,
                13.0,
                6.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: SRC",
              "clust": 27,
              "cat_0_index": 14,
              "rank": 21,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 21,
              "ini": 8
            },
            {
              "group": [
                19.0,
                18.0,
                17.0,
                11.0,
                9.0,
                4.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: TGFBR1",
              "clust": 17,
              "cat_0_index": 15,
              "rank": 12,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 13,
              "ini": 7
            },
            {
              "group": [
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: CAMK2B",
              "clust": 5,
              "cat_0_index": 33,
              "rank": 3,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 17,
              "ini": 6
            },
            {
              "group": [
                9.0,
                8.0,
                7.0,
                4.0,
                4.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: STK24",
              "clust": 6,
              "cat_0_index": 16,
              "rank": 0,
              "cat-0": "Gene Type: Interesting",
              "rankvar": 36,
              "ini": 5
            },
            {
              "group": [
                5.0,
                4.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: DCLK3",
              "clust": 1,
              "cat_0_index": 34,
              "rank": 5,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 25,
              "ini": 4
            },
            {
              "group": [
                25.0,
                24.0,
                21.0,
                15.0,
                12.0,
                6.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: LATS1",
              "clust": 22,
              "cat_0_index": 35,
              "rank": 29,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 27,
              "ini": 3
            },
            {
              "group": [
                6.0,
                5.0,
                4.0,
                2.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: NEK9",
              "clust": 0,
              "cat_0_index": 36,
              "rank": 4,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 6,
              "ini": 2
            },
            {
              "group": [
                30.0,
                29.0,
                26.0,
                19.0,
                15.0,
                7.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Gene: MYLK3",
              "clust": 29,
              "cat_0_index": 37,
              "rank": 32,
              "cat-0": "Gene Type: Not Interesting",
              "rankvar": 35,
              "ini": 1
            }
          ],
          "col_nodes": [
            {
              "group": [
                15.0,
                15.0,
                15.0,
                15.0,
                12.0,
                10.0,
                5.0,
                2.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1650",
              "clust": 12,
              "cat_1_index": 10,
              "cat_0_index": 24,
              "rank": 6,
              "cat-1": "Gender: Male",
              "ini": 29,
              "cat-0": "Category: two",
              "rankvar": 4
            },
            {
              "group": [
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H23",
              "clust": 2,
              "cat_1_index": 11,
              "cat_0_index": 25,
              "rank": 17,
              "cat-1": "Gender: Male",
              "ini": 28,
              "cat-0": "Category: two",
              "rankvar": 8
            },
            {
              "group": [
                6.0,
                6.0,
                6.0,
                6.0,
                5.0,
                4.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: CAL-12T",
              "clust": 4,
              "cat_1_index": 12,
              "cat_0_index": 26,
              "rank": 10,
              "cat-1": "Gender: Male",
              "ini": 27,
              "cat-0": "Category: two",
              "rankvar": 19
            },
            {
              "group": [
                27.0,
                27.0,
                27.0,
                26.0,
                20.0,
                15.0,
                8.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H358",
              "clust": 25,
              "cat_1_index": 13,
              "cat_0_index": 13,
              "rank": 4,
              "cat-1": "Gender: Male",
              "ini": 26,
              "cat-0": "Category: one",
              "rankvar": 0
            },
            {
              "group": [
                28.0,
                28.0,
                28.0,
                27.0,
                21.0,
                16.0,
                9.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1975",
              "clust": 22,
              "cat_1_index": 0,
              "cat_0_index": 27,
              "rank": 0,
              "cat-1": "Gender: Female",
              "ini": 25,
              "cat-0": "Category: two",
              "rankvar": 24
            },
            {
              "group": [
                3.0,
                3.0,
                3.0,
                3.0,
                3.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: HCC15",
              "clust": 1,
              "cat_1_index": 14,
              "cat_0_index": 28,
              "rank": 24,
              "cat-1": "Gender: Male",
              "ini": 24,
              "cat-0": "Category: two",
              "rankvar": 20
            },
            {
              "group": [
                4.0,
                4.0,
                4.0,
                4.0,
                4.0,
                3.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1355",
              "clust": 5,
              "cat_1_index": 15,
              "cat_0_index": 19,
              "rank": 9,
              "cat-1": "Gender: Male",
              "ini": 23,
              "cat-0": "Category: three",
              "rankvar": 6
            },
            {
              "group": [
                22.0,
                22.0,
                22.0,
                22.0,
                18.0,
                14.0,
                8.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: HCC827",
              "clust": 23,
              "cat_1_index": 1,
              "cat_0_index": 14,
              "rank": 28,
              "cat-1": "Gender: Female",
              "ini": 22,
              "cat-0": "Category: one",
              "rankvar": 25
            },
            {
              "group": [
                19.0,
                19.0,
                19.0,
                19.0,
                15.0,
                12.0,
                7.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H2405",
              "clust": 20,
              "cat_1_index": 16,
              "cat_0_index": 0,
              "rank": 1,
              "cat-1": "Gender: Male",
              "ini": 21,
              "cat-0": "Category: five",
              "rankvar": 12
            },
            {
              "group": [
                20.0,
                20.0,
                20.0,
                20.0,
                16.0,
                12.0,
                7.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: HCC78",
              "clust": 21,
              "cat_1_index": 17,
              "cat_0_index": 1,
              "rank": 25,
              "cat-1": "Gender: Male",
              "ini": 20,
              "cat-0": "Category: five",
              "rankvar": 27
            },
            {
              "group": [
                11.0,
                11.0,
                11.0,
                11.0,
                9.0,
                8.0,
                4.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1666",
              "clust": 7,
              "cat_1_index": 2,
              "cat_0_index": 6,
              "rank": 18,
              "cat-1": "Gender: Female",
              "ini": 19,
              "cat-0": "Category: four",
              "rankvar": 15
            },
            {
              "group": [
                18.0,
                18.0,
                18.0,
                18.0,
                14.0,
                11.0,
                6.0,
                3.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H661",
              "clust": 16,
              "cat_1_index": 18,
              "cat_0_index": 2,
              "rank": 3,
              "cat-1": "Gender: Male",
              "ini": 18,
              "cat-0": "Category: five",
              "rankvar": 26
            },
            {
              "group": [
                16.0,
                16.0,
                16.0,
                16.0,
                13.0,
                11.0,
                6.0,
                3.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H838",
              "clust": 17,
              "cat_1_index": 19,
              "cat_0_index": 3,
              "rank": 7,
              "cat-1": "Gender: Male",
              "ini": 17,
              "cat-0": "Category: five",
              "rankvar": 23
            },
            {
              "group": [
                12.0,
                12.0,
                12.0,
                12.0,
                10.0,
                9.0,
                5.0,
                2.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1703",
              "clust": 14,
              "cat_1_index": 20,
              "cat_0_index": 4,
              "rank": 11,
              "cat-1": "Gender: Male",
              "ini": 16,
              "cat-0": "Category: five",
              "rankvar": 21
            },
            {
              "group": [
                21.0,
                21.0,
                21.0,
                21.0,
                17.0,
                13.0,
                7.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: CALU-3",
              "clust": 19,
              "cat_1_index": 21,
              "cat_0_index": 7,
              "rank": 8,
              "cat-1": "Gender: Male",
              "ini": 15,
              "cat-0": "Category: four",
              "rankvar": 7
            },
            {
              "group": [
                17.0,
                17.0,
                17.0,
                17.0,
                13.0,
                11.0,
                6.0,
                3.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H2342",
              "clust": 18,
              "cat_1_index": 3,
              "cat_0_index": 8,
              "rank": 26,
              "cat-1": "Gender: Female",
              "ini": 14,
              "cat-0": "Category: four",
              "rankvar": 22
            },
            {
              "group": [
                26.0,
                26.0,
                26.0,
                25.0,
                19.0,
                15.0,
                8.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H2228",
              "clust": 26,
              "cat_1_index": 4,
              "cat_0_index": 15,
              "rank": 2,
              "cat-1": "Gender: Female",
              "ini": 13,
              "cat-0": "Category: one",
              "rankvar": 5
            },
            {
              "group": [
                13.0,
                13.0,
                13.0,
                13.0,
                10.0,
                9.0,
                5.0,
                2.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1299",
              "clust": 15,
              "cat_1_index": 22,
              "cat_0_index": 20,
              "rank": 12,
              "cat-1": "Gender: Male",
              "ini": 12,
              "cat-0": "Category: three",
              "rankvar": 1
            },
            {
              "group": [
                9.0,
                9.0,
                9.0,
                9.0,
                7.0,
                6.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1792",
              "clust": 10,
              "cat_1_index": 23,
              "cat_0_index": 21,
              "rank": 20,
              "cat-1": "Gender: Male",
              "ini": 11,
              "cat-0": "Category: three",
              "rankvar": 9
            },
            {
              "group": [
                10.0,
                10.0,
                10.0,
                10.0,
                8.0,
                7.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H460",
              "clust": 11,
              "cat_1_index": 24,
              "cat_0_index": 22,
              "rank": 5,
              "cat-1": "Gender: Male",
              "ini": 10,
              "cat-0": "Category: three",
              "rankvar": 11
            },
            {
              "group": [
                29.0,
                29.0,
                29.0,
                28.0,
                22.0,
                17.0,
                10.0,
                5.0,
                2.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H2106",
              "clust": 0,
              "cat_1_index": 25,
              "cat_0_index": 9,
              "rank": 22,
              "cat-1": "Gender: Male",
              "ini": 9,
              "cat-0": "Category: four",
              "rankvar": 28
            },
            {
              "group": [
                24.0,
                24.0,
                24.0,
                24.0,
                19.0,
                15.0,
                8.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H441",
              "clust": 27,
              "cat_1_index": 26,
              "cat_0_index": 16,
              "rank": 27,
              "cat-1": "Gender: Male",
              "ini": 8,
              "cat-0": "Category: one",
              "rankvar": 14
            },
            {
              "group": [
                7.0,
                7.0,
                7.0,
                7.0,
                6.0,
                5.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1944",
              "clust": 8,
              "cat_1_index": 5,
              "cat_0_index": 23,
              "rank": 23,
              "cat-1": "Gender: Female",
              "ini": 7,
              "cat-0": "Category: three",
              "rankvar": 10
            },
            {
              "group": [
                5.0,
                5.0,
                5.0,
                5.0,
                4.0,
                3.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1437",
              "clust": 6,
              "cat_1_index": 27,
              "cat_0_index": 10,
              "rank": 16,
              "cat-1": "Gender: Male",
              "ini": 6,
              "cat-0": "Category: four",
              "rankvar": 17
            },
            {
              "group": [
                23.0,
                23.0,
                23.0,
                23.0,
                18.0,
                14.0,
                8.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1734",
              "clust": 24,
              "cat_1_index": 6,
              "cat_0_index": 17,
              "rank": 19,
              "cat-1": "Gender: Female",
              "ini": 5,
              "cat-0": "Category: one",
              "rankvar": 18
            },
            {
              "group": [
                14.0,
                14.0,
                14.0,
                14.0,
                11.0,
                9.0,
                5.0,
                2.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: LOU-NH91",
              "clust": 13,
              "cat_1_index": 7,
              "cat_0_index": 5,
              "rank": 15,
              "cat-1": "Gender: Female",
              "ini": 4,
              "cat-0": "Category: five",
              "rankvar": 16
            },
            {
              "group": [
                2.0,
                2.0,
                2.0,
                2.0,
                2.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: HCC44",
              "clust": 3,
              "cat_1_index": 8,
              "cat_0_index": 11,
              "rank": 14,
              "cat-1": "Gender: Female",
              "ini": 3,
              "cat-0": "Category: four",
              "rankvar": 2
            },
            {
              "group": [
                8.0,
                8.0,
                8.0,
                8.0,
                6.0,
                5.0,
                3.0,
                1.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: A549",
              "clust": 9,
              "cat_1_index": 28,
              "cat_0_index": 12,
              "rank": 21,
              "cat-1": "Gender: Male",
              "ini": 2,
              "cat-0": "Category: four",
              "rankvar": 3
            },
            {
              "group": [
                25.0,
                25.0,
                25.0,
                24.0,
                19.0,
                15.0,
                8.0,
                4.0,
                1.0,
                1.0,
                1.0
              ],
              "name": "Cell Line: H1781",
              "clust": 28,
              "cat_1_index": 9,
              "cat_0_index": 18,
              "rank": 13,
              "cat-1": "Gender: Female",
              "ini": 1,
              "cat-0": "Category: one",
              "rankvar": 13
            }
          ],
          "enrichrgram": False
        }

        return JsonResponse(data)
