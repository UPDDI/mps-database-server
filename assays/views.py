# coding=utf-8
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    TemplateView,
    DeleteView
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
)
from assays.forms import (
    AssayStudyConfigurationForm,
    ReadyForSignOffForm,
    AssayStudyForm,
    AssayStudyFormNew,
    AssayStudySupportingDataFormSetFactory,
    AssayStudyAssayFormSetFactory,
    AssayStudyReferenceFormSetFactory,
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
    AssayMethodForm,
    AssayMeasurementTypeForm,
    AssaySettingForm,
    PhysicalUnitsForm,
    AssaySampleLocationForm,
    AssaySupplierForm,
    AssayPlateReaderMapForm,
    AssayPlateReaderMapItemFormSetFactory,
    AssayPlateReaderMapItemValueFormSetFactory,
    AssayPlateReadMapAdditionalInfoForm,
    AssayPlateReaderMapDataFileAddForm,
)
from microdevices.models import MicrophysiologyCenter
from django import forms

# TODO REVISE SPAGHETTI CODE
from assays.ajax import get_data_as_csv, fetch_data_points_from_filters
from assays.utils import (
    AssayFileProcessor,
    PlateReaderMapDataFileAdd,
    get_user_accessible_studies
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

from mps.mixins import (
    LoginRequiredMixin,
    OneGroupRequiredMixin,
    ObjectGroupRequiredMixin,
    DeletionMixin,
    user_is_active,
    PermissionDenied,
    StudyGroupMixin,
    StudyViewerMixin,
    CreatorOrSuperuserRequiredMixin,
    SuperuserRequiredMixin,
    FormHandlerMixin,
    FormHandlerMixin,
    ListHandlerMixin,
    CreatorOrSuperuserRequiredMixin
)

from mps.base.models import save_forms_with_tracking
from django.contrib.auth.models import User, Group
from mps.settings import DEFAULT_FROM_EMAIL

import ujson as json
import os

from mps.settings import MEDIA_ROOT

from django.template.loader import render_to_string, TemplateDoesNotExist

from datetime import datetime, timedelta
import pytz

from django.apps import apps

# File writing
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

import reversion


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
        study.center = group_center_map[study.group_id]


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


class AssayStudyAdd(OneGroupRequiredMixin, AssayStudyMixin, CreateView):
    pass


class AssayStudyUpdate(ObjectGroupRequiredMixin, AssayStudyMixin, UpdateView):
    pass


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


class AssayStudyIndex(StudyViewerMixin, DetailView):
    """Show all chip and plate models associated with the given study"""
    model = AssayStudy
    context_object_name = 'study_index'
    template_name = 'assays/assaystudy_index.html'

    # For permission mixin NOT AS USELESS AS IT SEEMS
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
class AssayStudySignOff(UpdateView):
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


class AssayStudyDataUpload(ObjectGroupRequiredMixin, UpdateView):
    """Upload an Excel Sheet for storing multiple sets of Readout data at one"""
    model = AssayStudy
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
        context['version'] = len(os.listdir(MEDIA_ROOT + '/excel_templates/'))

        context['data_file_uploads'] = get_data_file_uploads(study=self.object)

        if self.request.POST:
            if 'supporting_data_formset' not in context:
                context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(instance=self.object)

        context['update'] = True

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


class AssayStudyDelete(DeletionMixin, DeleteView):
    """Delete a Setup"""
    model = AssayStudy
    template_name = 'assays/assaystudy_delete.html'
    success_url = '/assays/assaystudy/'


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
            value_units = PhysicalUnits.objects.filter(
                availability__contains='readout'
            ).order_by(
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
class AssayMatrixUpdate(StudyGroupMixin, UpdateView):
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


class AssayMatrixDelete(DeletionMixin, DeleteView):
    """Delete a Setup"""
    model = AssayMatrix
    template_name = 'assays/assaymatrix_delete.html'

    def get_success_url(self):
        return self.object.study.get_absolute_url()


# TODO PROBABLY WILL REMOVE EVENTUALLY
class AssayMatrixItemUpdate(StudyGroupMixin, UpdateView):
    model = AssayMatrixItem
    template_name = 'assays/assaymatrixitem_add.html'
    form_class = AssayMatrixItemFullForm

    def get_context_data(self, **kwargs):
        context = super(AssayMatrixItemUpdate, self).get_context_data(**kwargs)

        if self.request.POST:
            context['compound_formset'] = AssaySetupCompoundInlineFormSetFactory(
                self.request.POST,
                instance=self.object,
                # matrix=self.object.matrix
            )
            context['cell_formset'] = AssaySetupCellInlineFormSetFactory(
                self.request.POST,
                instance=self.object,
                # matrix=self.object
            )
            context['setting_formset'] = AssaySetupSettingInlineFormSetFactory(
                self.request.POST,
                instance=self.object,
                # matrix=self.object
            )
        else:
            context['compound_formset'] = AssaySetupCompoundInlineFormSetFactory(
                instance=self.object,
                # matrix=self.object.matrix
            )
            context['cell_formset'] = AssaySetupCellInlineFormSetFactory(
                instance=self.object,
                # matrix=self.object
            )
            context['setting_formset'] = AssaySetupSettingInlineFormSetFactory(
                instance=self.object,
                # matrix=self.object
            )

        # cellsamples = get_cell_samples_for_selection(self.request.user)

        # Cellsamples will always be the same
        context['cellsamples'] = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        context['update'] = True

        return context

    def form_valid(self, form):
        compound_formset = AssaySetupCompoundInlineFormSetFactory(
            self.request.POST,
            instance=self.object,
            # matrix=self.object.matrix
        )
        cell_formset = AssaySetupCellInlineFormSetFactory(
            self.request.POST,
            instance=self.object,
            # matrix=self.object
        )
        setting_formset = AssaySetupSettingInlineFormSetFactory(
            self.request.POST,
            instance=self.object,
            # matrix=self.object
        )

        all_formsets = [
            compound_formset,
            cell_formset,
            setting_formset,
        ]

        all_formsets_valid =  True

        for current_formset in all_formsets:
            if not current_formset.is_valid():
                all_formsets_valid = False

        if form.is_valid() and all_formsets_valid:
            save_forms_with_tracking(self, form, update=True, formset=all_formsets)

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

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form
            ))


class AssayMatrixItemDetail(StudyGroupMixin, DetailView):
    """Details for a Chip Setup"""
    template_name = 'assays/assaymatrixitem_detail.html'
    model = AssayMatrixItem
    detail = True


class AssayMatrixItemDelete(DeletionMixin, DeleteView):
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

        ordered_study_images = AssayImage.objects.filter(
            setting_id__in=study_image_settings
        ).order_by('time').values_list('id', flat=True)

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

            if len(current_filters) > 3 and current_filters[3]:
                compound_ids = [int(id) for id in current_filters[3].split(',') if id]

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

            if len(current_filters) > 2 and current_filters[2]:
                target_ids = [int(id) for id in current_filters[2].split(',') if id]

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

    def extra_form_processing(self):
        # Update the base model to be self-referential if it is missing
        form = self.all_forms.get('form')
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
# class AssayStudySetUpdate(CreatorOrSuperuserRequiredMixin, UpdateView):
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


class AssayStudyAddNew(OneGroupRequiredMixin, AssayStudyMixin, CreateView):
    template_name = 'assays/assaystudy_add_new.html'
    form_class = AssayStudyFormNew

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


# class AssayReferenceUpdate(CreatorOrSuperuserRequiredMixin, UpdateView):
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


class AssayReferenceDelete(DeletionMixin, DeleteView):
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


class AssayMatrixNew(StudyGroupMixin, UpdateView):
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
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AssayStudyPowerAnalysisStudy(StudyViewerMixin, DetailView):
    """Displays the power analysis interface for the current study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_power_analysis_study.html'


# REVIEW PERMISSIONS
class AssayTargetMixin(FormHandlerMixin):
    model = AssayTarget
    form_class = AssayTargetForm


class AssayTargetAdd(OneGroupRequiredMixin, AssayTargetMixin, CreateView):
    pass


class AssayTargetUpdate(CreatorOrSuperuserRequiredMixin, AssayTargetMixin, UpdateView):
    pass


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


class AssayMethodAdd(OneGroupRequiredMixin, AssayMethodMixin, CreateView):
    pass


class AssayMethodUpdate(CreatorOrSuperuserRequiredMixin, AssayMethodMixin, UpdateView):
    pass


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


class PhysicalUnitsAdd(OneGroupRequiredMixin, PhysicalUnitsMixin, CreateView):
    pass


class PhysicalUnitsUpdate(CreatorOrSuperuserRequiredMixin, PhysicalUnitsMixin, UpdateView):
    pass


class PhysicalUnitsDetail(DetailView):
    pass


class PhysicalUnitsList(ListView):
    model = PhysicalUnits
    template_name = 'assays/assayunit_list.html'

    def get_queryset(self):
        queryset = PhysicalUnits.objects.all().prefetch_related(
            'unit_type',
        )

        return queryset


class AssayMeasurementTypeMixin(FormHandlerMixin):
    model = AssayMeasurementType
    form_class = AssayMeasurementTypeForm


class AssayMeasurementTypeAdd(OneGroupRequiredMixin, AssayMeasurementTypeMixin, CreateView):
    pass


class AssayMeasurementTypeUpdate(CreatorOrSuperuserRequiredMixin, AssayMeasurementTypeMixin, UpdateView):
    pass


class AssayMeasurementTypeDetail(AssayMeasurementTypeMixin, DetailView):
    pass


class AssayMeasurementTypeList(ListHandlerMixin, ListView):
    model = AssayMeasurementType


class AssaySampleLocationMixin(FormHandlerMixin):
    model = AssaySampleLocation
    form_class = AssaySampleLocationForm


class AssaySampleLocationAdd(OneGroupRequiredMixin, AssaySampleLocationMixin, CreateView):
    pass


class AssaySampleLocationUpdate(CreatorOrSuperuserRequiredMixin, AssaySampleLocationMixin, UpdateView):
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


class AssaySettingUpdate(CreatorOrSuperuserRequiredMixin, AssaySettingMixin, UpdateView):
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


class AssaySupplierUpdate(CreatorOrSuperuserRequiredMixin, AssaySupplierMixin, UpdateView):
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
class AssayPlateReaderMapIndex(StudyViewerMixin, DetailView):
    """Assay plate map"""
    model = AssayStudy
    context_object_name = 'assayplatereadermap_index'
    template_name = 'assays/assayplatereadermap_index.html'

    def get_object(self, queryset=None):
        self.study = super(AssayPlateReaderMapIndex, self).get_object()
        return self.study

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapIndex, self).get_context_data(**kwargs)

        assayplatereadermaps = AssayPlateReaderMap.objects.filter(
            study=self.object.id
        ).prefetch_related(
            'assayplatereadermapitem_set',
            #'created_by',
        )
        context['assayplatereadermaps'] = assayplatereadermaps

        assayplatereadermapitems = AssayPlateReaderMapItem.objects.filter(
            assayplatereadermap__in=assayplatereadermaps
        )

        context['assayplatereaderitems'] = assayplatereadermapitems
        #####
        context['index'] = True
        context['page_called'] = 'index'
        #####

        # #followed example in other part of code...dictionary and list of lists of same information
        # keep for now in case go back to something like this
        # distinct_base_plate_map = {}
        # reduce_distinct_base_name = []
        #
        # for record in assayplatereadermaps:
        #     distinct_base_plate_map[(record.base_name, record.device, record.plate_use, record.study_assay)] = distinct_base_plate_map.setdefault(
        #         (record.base_name, record.device, record.plate_use, record.study_assay), 0
        #     ) + 1
        #
        # for current_tuple, count in distinct_base_plate_map.items():
        #     reduce_distinct_base_name.append([current_tuple[0], current_tuple[1], current_tuple[2], current_tuple[3], count])
        #
        # context['distinct_base_plate_map'] = distinct_base_plate_map
        # context['reduce_distinct_base_name'] = reduce_distinct_base_name

        return context


class AssayPlateReaderMapAdd(StudyGroupMixin, CreateView):
    """Assay plate map add"""
    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_add.html'
    form_class = AssayPlateReaderMapForm

    # used in ADD, not in UPDATE - check carefully if copy
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
        #passing the study_id to the form to get back the matrix items list for this study
        context['assay_map_additional_info'] = AssayPlateReadMapAdditionalInfoForm(study_id=self.kwargs['study_id'])

        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])
        # the items (one for each well in the plate)
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
        # the values (0 to many for each item)
        if 'value_formset' not in context:
            if self.request.POST:
                context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
                        self.request.POST,
                        study=study,
                        user=self.request.user
                )
            else:
                context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
                    study=study,
                    user=self.request.user
                )

        return_list = get_matrix_items_with_setup(self.kwargs['study_id'])
        matrix_items_in_study = return_list[0]
        matrix_list_size = return_list[1]
        matrix_list_pk = return_list[2]
        context['matrix_items_in_study'] = matrix_items_in_study
        context['matrix_list_size'] = matrix_list_size
        context['matrix_list_pk'] = matrix_list_pk
        return context

    def form_valid(self, form):
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])
        formset = AssayPlateReaderMapItemFormSetFactory(
            self.request.POST,
            instance=form.instance,
            study=study
        )
        value_formset = AssayPlateReaderMapItemValueFormSetFactory(
            self.request.POST,
            instance=form.instance,
            study=study
        )
        formsets = [formset, value_formset, ]
        formsets_are_valid = True

        for formset in formsets:
            if not formset.is_valid():
                formsets_are_valid = False
        if form.is_valid() and formsets_are_valid:
            save_forms_with_tracking(self, form, formset=formsets, update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            # watch if copy to update (note bottom is view and update)
            return self.render_to_response(self.get_context_data(form=form))
            #return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayPlateReaderMapUpdate(StudyGroupMixin, UpdateView):
    """Assay plate map update"""
    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_add.html'
    form_class = AssayPlateReaderMapForm

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapUpdate, self).get_context_data(**kwargs)
        #####
        context['update'] = True
        context['page_called'] = 'update'
        #####
        context['assay_map_additional_info'] = AssayPlateReadMapAdditionalInfoForm(study_id=self.object.study_id)

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

        if 'value_formset' not in context:
            if self.request.POST:
                context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
                        self.request.POST,
                        instance=self.object,
                        user=self.request.user
                )
            else:
                context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
                    instance=self.object,
                    user=self.request.user
                )

        return_list = get_matrix_items_with_setup(self.object.study_id)
        matrix_items_in_study = return_list[0]
        matrix_list_size = return_list[1]
        matrix_list_pk = return_list[2]
        context['matrix_items_in_study'] = matrix_items_in_study
        context['matrix_list_size'] = matrix_list_size
        context['matrix_list_pk'] = matrix_list_pk
        return context

    def form_valid(self, form):
        formset = AssayPlateReaderMapItemFormSetFactory(self.request.POST, instance=self.object)
        value_formset = AssayPlateReaderMapItemValueFormSetFactory(self.request.POST, instance=self.object)

        formsets = [formset, value_formset, ]
        formsets_are_valid = True

        for formset in formsets:
            if not formset.is_valid():
                formsets_are_valid = False

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formsets, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayPlateReaderMapView(StudyGroupMixin, UpdateView):
    """Assay plate map view"""
    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_add.html'
    form_class = AssayPlateReaderMapForm

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapView, self).get_context_data(**kwargs)
        #####
        context['review'] = True
        context['page_called'] = 'review'
        #####
        context['assay_map_additional_info'] = AssayPlateReadMapAdditionalInfoForm(study_id=self.object.study_id)

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

        if 'value_formset' not in context:
            if self.request.POST:
                context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
                        self.request.POST,
                        instance=self.object,
                        user=self.request.user
                )
            else:
                context['value_formset'] = AssayPlateReaderMapItemValueFormSetFactory(
                    instance=self.object,
                    user=self.request.user
                )

        return_list = get_matrix_items_with_setup(self.object.study_id)
        matrix_items_in_study = return_list[0]
        matrix_list_size = return_list[1]
        matrix_list_pk = return_list[2]
        context['matrix_items_in_study'] = matrix_items_in_study
        context['matrix_list_size'] = matrix_list_size
        context['matrix_list_pk'] = matrix_list_pk
        return context

    def form_valid(self, form):
        formset = AssayPlateReaderMapItemFormSetFactory(self.request.POST, instance=self.object)
        value_formset = AssayPlateReaderMapItemValueFormSetFactory(self.request.POST, instance=self.object)

        formsets = [formset, value_formset, ]
        formsets_are_valid = True

        for formset in formsets:
            if not formset.is_valid():
                formsets_are_valid = False

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formsets, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayPlateReaderMapDelete(StudyViewerMixin, DeleteView):
    model = AssayPlateReaderMap
    template_name = 'assays/assayplatereadermap_delete.html'

    def get_success_url(self):
        # goes to the M&I list (main study) page.... returns self.object.study.get_absolute_url()
        return self.object.get_post_submission_url()

# function used in plate reader app (add, view, and update) to get associated matrix item setup for display
def get_matrix_items_with_setup(study_id):
    matrix_items_with_setup = AssayMatrixItem.objects.filter(
        study_id=study_id
    ).prefetch_related(
        #    'device',
        #    'created_by',
        'matrix',
        #    'organ_model',
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
    ).order_by('matrix__name', 'name',)

    # distinct_matrix = {}
    # reduce_distinct_matrix = []
    #
    # for record in matrix_items_with_setup:
    #     distinct_matrix[(record.matrix.id, record.matrix, record.matrix.number_of_rows, record.matrix.number_of_columns)] = distinct_matrix.setdefault(
    #         (record.matrix.id, record.matrix, record.matrix.number_of_rows, record.matrix.number_of_columns), 0
    #     ) + 1
    #
    # for current_tuple, count in distinct_matrix.items():
    #     reduce_distinct_matrix.append([current_tuple[0], current_tuple[1], current_tuple[2], current_tuple[3], count])

    # distinct_matrix = {}
    # reduce_distinct_matrix = []
    #
    # for record in matrix_items_with_setup:
    #     distinct_matrix[(record.matrix.id, record.matrix.name, record.matrix.number_of_rows, record.matrix.number_of_columns, record.id, record.name, record.row_index, record.column_index)] = distinct_matrix.setdefault(
    #         (record.matrix.id, record.matrix.name, record.matrix.number_of_rows, record.matrix.number_of_columns, record.id, record.name, record.row_index, record.column_index), 0
    #     ) + 1
    #
    # for current_tuple, count in distinct_matrix.items():
    #     reduce_distinct_matrix.append([current_tuple[0], current_tuple[1], current_tuple[2], current_tuple[3], current_tuple[4], current_tuple[5], current_tuple[6], current_tuple[7] ])

    matrix_list_for_size = AssayMatrix.objects.filter(
            study_id=study_id
        ).order_by('name',)

    matrix_list_size = []
    matrix_list_pk = []
    for record in matrix_list_for_size:
        if record.number_of_rows <= 4 and record.number_of_columns <= 6:
            matrix_list_size.append(24)
            matrix_list_pk.append(record.id)
        elif record.number_of_rows <= 8 and record.number_of_columns <= 12:
            matrix_list_size.append(96)
            matrix_list_pk.append(record.id)
        else:
            matrix_list_size.append(384)
            matrix_list_pk.append(record.id)

    return matrix_items_with_setup, matrix_list_size, matrix_list_pk

##### Plate reader file list, add, update, view and delete section
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
        context['index'] = True
        context['page_called'] = 'index'

        assayplatereadermapdatafiles = AssayPlateReaderMapDataFile.objects.filter(
            study=self.object.id
        ).prefetch_related(
            'assayplatereaderassayfileblock_set',
        )
        context['assayplatereaderdatafile'] = assayplatereadermapdatafiles

        assayplatereadermapdatafileblocks = AssayPlateReaderMapDataFileBlock.objects.filter(
            assayplatereadermapdatafile__in=assayplatereadermapdatafiles
        )

        context['assayplatereadermapdatafiles'] = assayplatereadermapdatafileblocks

        # TODO sck modify to get the list or count of the file data blocks to show in the table
        # use something like this:
        #
        # distinct_base_plate_map = {}
        # reduce_distinct_base_name = []
        #
        # for record in assayplatereadermaps:
        #     distinct_base_plate_map[(record.base_name, record.device, record.plate_use, record.study_assay)] = distinct_base_plate_map.setdefault(
        #         (record.base_name, record.device, record.plate_use, record.study_assay), 0
        #     ) + 1
        #
        # for current_tuple, count in distinct_base_plate_map.items():
        #     reduce_distinct_base_name.append([current_tuple[0], current_tuple[1], current_tuple[2], current_tuple[3], count])
        #
        # context['distinct_base_plate_map'] = distinct_base_plate_map
        # context['reduce_distinct_base_name'] = reduce_distinct_base_name

        return context

# TODO sck build these
class AssayPlateReaderMapDataFileUpdate(StudyGroupMixin, UpdateView):
    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_update.html'

class AssayPlateReaderMapDataFileView(StudyGroupMixin, UpdateView):
    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_view.html'

class AssayPlateReaderMapDataFileDelete(StudyViewerMixin, DeleteView):
    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_delete.html'

##### in process
class AssayPlateReaderMapDataFileAdd(StudyGroupMixin, CreateView):
    """Upload an plate reader data file"""
    model = AssayPlateReaderMapDataFile
    template_name = 'assays/assayplatereaderfile_add.html'
    form_class = AssayPlateReaderMapDataFileAddForm

    #In add, do not need in update - some other differences due to no forms
    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, study=study)
        # If GET
        else:
            return form_class(study=study)

    def get_context_data(self, **kwargs):
        context = super(AssayPlateReaderMapDataFileAdd, self).get_context_data(**kwargs)
        ##############################
        context['add'] = True
        context['page_called'] = 'add'
        return context

    def form_valid(self, form):
        if form.is_valid():
            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
