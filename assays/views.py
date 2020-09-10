# coding=utf-8
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    TemplateView,
    DeleteView,
)
from django.http import HttpResponse
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
    # Deprecated, just in case
    AssayRun,
    AssayDataUpload,
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
    AssayGroup,
    AssayOmicDataFileUpload,
    AssayOmicDataPoint,
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
    AssayMatrixItemForm,
    AssayOmicDataFileUploadForm,
)

from microdevices.models import MicrophysiologyCenter
from django import forms

# TODO REVISE SPAGHETTI CODE
from assays.ajax import get_data_as_csv, fetch_data_points_from_filters
from assays.utils import (
    AssayFileProcessor,
    get_user_accessible_studies,
    add_update_plate_reader_data_map_item_values_from_file,
    # modify_templates,
    DEFAULT_CSV_HEADER,
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
    SuperuserRequiredMixin,
    FormHandlerMixin,
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

# File writing
from io import BytesIO
import xlsxwriter
from assays.utils import DEFAULT_CSV_HEADER
from mps.settings import TEMPLATE_VALIDATION_STARTING_COLUMN_INDEX
from django.db import connection
import xlsxwriter
import io

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

    # for data_file_upload in data_file_uploads:
    #     if data_file_upload_map.get(data_file_upload.id, ''):
    #         valid_files.append(data_file_upload)
    #
    # return valid_files

    for data_file_upload in data_file_uploads:
        if data_file_upload_map.get(data_file_upload.id, ''):
            data_file_upload.present = True

    return data_file_uploads


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
        queryset = get_user_accessible_studies(self.request.user)

        # Excessive, but not horrible
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


class AssayGroupDetail(StudyGroupMixin, DetailView):
    # Why not have the mixin look for DetailView?
    model = AssayGroup
    detail = True

    def get_context_data(self, **kwargs):
        context = super(AssayGroupDetail, self).get_context_data(**kwargs)

        context.update({
            'detail': True,
            'items': AssayMatrixItem.objects.filter(group=self.object).order_by('name')
        })

        return context


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
            # CONTRIVED!!!
            'update': True,
            # TODO REVISE
            'plates': AssayMatrix.objects.filter(
                # OLD
                # device__isnull=False,
                organ_model__isnull=False,
                study_id=self.object.id
            ).prefetch_related(
                'organ_model',
                'assaymatrixitem_set'
            )
        })

        return context


class AssayStudyPlateMixin(FormHandlerMixin):
    model = AssayMatrix
    template_name = 'assays/assaystudy_plate_add.html'
    # Might actually be a formset or something?
    form_class = AssayStudyPlateForm

    # CRUDE: BUT PREVENTS LOOKING AT NON PLATE MATRICES
    def get_object(self, queryset=None):
        current_object = super(AssayStudyPlateMixin, self).get_object()
        return get_object_or_404(AssayMatrix, pk=current_object.id, representation='plate')

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


class AssayStudyPlateDetail(StudyGroupMixin, AssayStudyPlateMixin, DetailView):
    detail = True

    def get_context_data(self, **kwargs):
        context = super(AssayStudyPlateDetail, self).get_context_data(**kwargs)

        context.update({
            'form': AssayStudyPlateForm(instance=self.object),
            'detail': True
        })

        return context



class AssayStudyAssays(ObjectGroupRequiredMixin, AssayStudyMixin, UpdateView):
    template_name = 'assays/assaystudy_assays.html'
    # This will probably just be a contrived empty form
    form_class = AssayStudyAssaysForm

    formsets = (
        ('study_assay_formset', AssayStudyAssayFormSetFactory),
    )


# TODO: TO BE REVISED
class AssayStudyDataIndex(StudyViewerMixin, AssayStudyMixin, DetailView):
    """Show all data sections for a given study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_data_index.html'

    # For permission mixin NOT AS USELESS AS IT SEEMS
    def get_object(self, queryset=None):
        self.study = super(AssayStudyDataIndex, self).get_object()
        return self.study

    # NOTE: bracket assignations are against PEP, one should use .update
    def get_context_data(self, **kwargs):
        context = super(AssayStudyDataIndex, self).get_context_data(**kwargs)

        # STAGE ONLY
        # SUBJECT TO CHANGE
        log2fold_files = AssayOmicDataFileUpload.objects.filter(
            study_id=self.object.id,
            data_type='log2fc'
        )

        context.update({
            # CONTRIVED!!!
            'update': True,
            # NECESSARILY FALSE
            'has_next_button': False,
            # STAGE ONLY SUBJECT TO CHANGE
            # Count only log2fold for the moment?
            'log2fold_files': log2fold_files,
            'log2fold_points': AssayOmicDataPoint.objects.filter(
                omic_data_file__in=log2fold_files
            ),
        })

        return context


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
            'group__assaygroupcompound_set__compound_instance__supplier',
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
        ).prefetch_related(
            'organ_model',
            'assaymatrixitem_set'
        )

        context.update({
            'chip_groups': chip_groups,
            'plate_groups': plate_groups,
            'number_of_chips': number_of_chips,
            'plates': plates,
            'form': AssayStudyGroupForm(instance=self.object)
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
            # 'has_next_button': False
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


class AssayMatrixMixin(StudyGroupMixin, FormHandlerMixin):
    model = AssayMatrix
    # TODO RENAME RENAME RENAME
    template_name = 'assays/matrix_modification.html'
    form_class = AssayMatrixForm

    def get_context_data(self, **kwargs):
        context = super(AssayMatrixMixin, self).get_context_data(**kwargs)

        context.update({
            'item_prefix': 'matrix_item',
            'cell_prefix': 'cell',
            'setting_prefix': 'setting',
            'compound_prefix': 'compound',
            # Get all cell samples
            'cellsamples': CellSample.objects.all().prefetch_related(
                'cell_type__organ',
                'supplier',
                'cell_subtype__cell_type'
            )
        })

        return context

    # Get the study and user (TODO REVISE)
    def get_form(self, form_class=None):
        form_class = self.get_form_class()

        if self.object:
            # Get the study
            study = self.object.study
        else:
            study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, instance=self.object, study=study, user=self.request.user)
        # If GET
        else:
            return form_class(instance=self.object, study=study, user=self.request.user)


class AssayMatrixAddPrototype(AssayMatrixMixin, CreateView):
    pass


class AssayMatrixUpdatePrototype(AssayMatrixMixin, UpdateView):
    pass


# TODO REFACTOR
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

    def get_context_data(self, **kwargs):
        context = super(AssayStudySetDataPlots, self).get_context_data(**kwargs)

        # NOT DRY
        # FILTER OUT STUDIES WITH NO ASSAYS
        # PLEASE NOTE FILTER HERE
        # WE ASSUME THE USER OUGHT TO SEE ALL THE STUDIES (via permission mixin)
        # combined = get_user_accessible_studies(self.request.user).filter(
        #     assaystudyassay__isnull=False
        # )
        combined = self.object.studies.all()

        get_queryset_with_organ_model_map(combined)
        get_queryset_with_number_of_data_points(combined)
        get_queryset_with_stakeholder_sign_off(combined)
        get_queryset_with_group_center_dictionary(combined)

        context['studies'] = combined

        return context


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


def get_summary_data(set_name, queryset, on_or_after_date=None):
    if on_or_after_date:
        queryset = queryset.filter(created_on__lt=on_or_after_date)

    organ_models = len(set(queryset.values_list('organ_model_id', flat=True)))
    studies = len(set(queryset.values_list('study_id', flat=True)))
    chips = queryset.count()

    if on_or_after_date:
        data_points = AssayDataPoint.objects.filter(
            matrix_item_id__in=queryset,
            replaced=False,
            excluded=False,
            data_file_upload__created_on__lt=on_or_after_date
        ).exclude(
            value__isnull=True,
        ).count()
    else:
        data_points = AssayDataPoint.objects.filter(
            matrix_item_id__in=queryset,
            replaced=False,
            excluded=False
        ).exclude(
            value__isnull=True
        ).count()

    # NOT DRY
    video_formats = {x: True for x in [
        'webm',
        'avi',
        'ogv',
        'mov',
        'wmv',
        'mp4',
        '3gp',
    ]}

    all_media = AssayImage.objects.filter(matrix_item_id__in=queryset)

    images = 0
    videos = 0

    for media in all_media:
        is_video = media.file_name.split('.')[-1].lower() in video_formats
        if is_video:
            videos += 1
        else:
            images += 1

    return [
        set_name,
        organ_models,
        studies,
        chips,
        data_points,
        images,
        videos
    ]


class TCTCSummary(SuperuserRequiredMixin, TemplateView):
    template_name = 'assays/tctc_summary.html'

    def get_context_data(self, **kwargs):
        context = super(TCTCSummary, self).get_context_data(**kwargs)

        if self.request.GET.get('delta', ''):
            on_or_after_date = datetime.strptime(self.request.GET.get('delta'), '%Y-%m-%d')
        else:
            on_or_after_date = None

        queryset = AssayMatrixItem.objects.all()

        all_group_ids = [41, 46]

        missing_stakeholder_blacklist = list(set(
            AssayStudyStakeholder.objects.filter(
                signed_off_by_id=None,
                sign_off_required=True
            ).values_list('study_id', flat=True)
        ))

        mit_studies = AssayStudy.objects.filter(
            group_id__in=[46]
        )
        tamu_studies = AssayStudy.objects.filter(
            group_id__in=[41]
        )
        level_1 = AssayStudy.objects.filter(
            group_id__in=all_group_ids,
            signed_off_by=None
        ) | AssayStudy.objects.filter(
            group_id__in=all_group_ids,
            id__in=missing_stakeholder_blacklist
        )
        level_2 = AssayStudy.objects.filter(
            group_id__in=all_group_ids,
            restricted=True
        ).exclude(
            signed_off_by=None
        ).exclude(
            id__in=missing_stakeholder_blacklist
        )
        level_3 = AssayStudy.objects.filter(
            group_id__in=all_group_ids,
            restricted=False
        ).exclude(
            signed_off_by=None
        ).exclude(
            id__in=missing_stakeholder_blacklist
        )

        data_of_interest = (
            ('MIT-3D', queryset.filter(
                study_id__in=mit_studies,
                organ_model__model_type__in=['F3', 'S3']
            )),
            ('MIT-2D', queryset.filter(
                study_id__in=mit_studies,
                organ_model__model_type__in=['F2', 'S2']
            )),
            ('TAMU-3D', queryset.filter(
                study_id__in=tamu_studies,
                organ_model__model_type__in=['F3', 'S3']
            )),
            ('TAMU-2D', queryset.filter(
                study_id__in=tamu_studies,
                organ_model__model_type__in=['F2', 'S2']
            )),
            ('Level 1', queryset.filter(
                study_id__in=level_1
            )),
            ('Level 2', queryset.filter(
                study_id__in=level_2
            )),
            ('Level 3', queryset.filter(
                study_id__in=level_3
            )),
        )

        rows = []

        for data in data_of_interest:
            rows.append(get_summary_data(data[0], data[1]))

        context['rows'] = rows

        if on_or_after_date:
            stakeholder_sign_off_too_new_blacklist = AssayStudyStakeholder.objects.filter(
                sign_off_required=True,
                signed_off_date__gte=on_or_after_date
            ).values_list('study_id', flat=True)

            if stakeholder_sign_off_too_new_blacklist:
                missing_stakeholder_blacklist = list(set(missing_stakeholder_blacklist.extend(stakeholder_sign_off_too_new_blacklist)))

            studies_before_date = AssayStudy.objects.filter(
                created_on__lt=on_or_after_date,
                group_id__in=[46, 41]
            )

            mit_studies = studies_before_date.filter(
                group_id__in=[46]
            )
            tamu_studies = studies_before_date.filter(
                group_id__in=[41]
            )

            level_1 = studies_before_date.filter(
                group_id__in=all_group_ids,
                signed_off_by=None
            ) | AssayStudy.objects.filter(
                group_id__in=all_group_ids,
                id__in=missing_stakeholder_blacklist
            ) | AssayStudy.objects.filter(
                signed_off_date__gte=on_or_after_date
            )
            level_2 = studies_before_date.filter(
                group_id__in=all_group_ids,
                restricted=True
            ).exclude(
                signed_off_by=None
            ).exclude(
                id__in=missing_stakeholder_blacklist
            ).exclude(
                id__in=level_1
            ) | studies_before_date.filter(
                group_id__in=all_group_ids,
                restricted=True
            ).exclude(
                signed_off_date__gte=on_or_after_date
            ).exclude(
                id__in=missing_stakeholder_blacklist
            ).exclude(
                id__in=level_1
            )
            level_3 = studies_before_date.filter(
                group_id__in=all_group_ids,
                restricted=False
            ).exclude(
                signed_off_by=None
            ).exclude(
                id__in=missing_stakeholder_blacklist
            ).exclude(
                signed_off_date__gte=on_or_after_date
            )

            data_of_interest = (
                ('MIT-3D', queryset.filter(
                    study_id__in=mit_studies,
                    organ_model__model_type__in=['F3', 'S3']
                )),
                ('MIT-2D', queryset.filter(
                    study_id__in=mit_studies,
                    organ_model__model_type__in=['F2', 'S2']
                )),
                ('TAMU-3D', queryset.filter(
                    study_id__in=tamu_studies,
                    organ_model__model_type__in=['F3', 'S3']
                )),
                ('TAMU-2D', queryset.filter(
                    study_id__in=tamu_studies,
                    organ_model__model_type__in=['F2', 'S2']
                )),
                ('Level 1', queryset.filter(
                    study_id__in=level_1
                )),
                ('Level 2', queryset.filter(
                    study_id__in=level_2
                )),
                ('Level 3', queryset.filter(
                    study_id__in=level_3
                )),
            )

            delta_rows = []

            for index, data in enumerate(data_of_interest):
                delta_row = get_summary_data(data[0], data[1], on_or_after_date)
                new_row = [delta_row[0]]

                for i in range(1, len(delta_row)):
                    new_row.append(rows[index][i] - delta_row[i])

                delta_rows.append(new_row)

            context['delta_rows'] = delta_rows

        return context


# TODO ADD PERMISSION MIXINS
class AssayStudyIndexNew(StudyViewerMixin, DetailView):
    """Show all chip and plate models associated with the given study"""
    model = AssayStudy
    context_object_name = 'study_index'
    template_name = 'assays/assaystudy_index.html'

    # For permission mixin
    def get_object(self, queryset=None):
        self.study = super(AssayStudyIndex, self).get_object()
        return self.study

    def get_context_data(self, **kwargs):
        context = super(AssayStudyIndex, self).get_context_data(**kwargs)

        matrices = AssayMatrix.objects.filter(
            study_id=self.object.id
        ).prefetch_related(
            'assaymatrixitem_set',
            'created_by',
        )

        items = AssayMatrixItem.objects.filter(
            matrix_id__in=matrices
        ).prefetch_related(
            'device',
            'created_by',
            'matrix',
            'organ_model',
            'assaysetupcompound_set__compound_instance__compound',
            'assaysetupcompound_set__concentration_unit',
            'assaysetupcompound_set__addition_location',
            'assaysetupcell_set__cell_sample__cell_type__organ',
            'assaysetupcell_set__cell_sample__cell_subtype',
            'assaysetupcell_set__cell_sample__supplier',
            'assaysetupcell_set__addition_location',
            'assaysetupcell_set__density_unit',
            'assaysetupsetting_set__setting',
            'assaysetupsetting_set__unit',
            'assaysetupsetting_set__addition_location',
        )

        # Cellsamples will always be the same
        context['matrices'] = matrices
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

        return context


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


class AssayStudyPowerAnalysisStudy(StudyViewerMixin, DetailView):
    """Displays the power analysis interface for the current study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_power_analysis_study.html'


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


##### ASSAY PLATE MAP START
##### Plate map list, add, update, view and delete section
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

###### END Plate reader file list, add, update, view and HOLD section


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
