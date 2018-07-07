# coding=utf-8
# IF YOU WANT TO SEE PAST VIEWS, DO NOT RELY ON THE COMMENTED CODE HEREIN
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
# TODO TRIM THIS IMPORT
# Temporary wildcard
from assays.models import *
from assays.forms import (
    AssayStudyConfigurationForm,
    ReadyForSignOffForm,
    AssayStudyForm,
    AssayStudySupportingDataFormSetFactory,
    AssayStudyAssayFormSetFactory,
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
    AssayImage,
    AssayImageSetting
)
from django import forms

# TODO REVISE SPAGHETTI CODE
from assays.ajax import get_data_as_csv
from assays.utils import (
    AssayFileProcessor
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
    StudyViewerMixin
)

from mps.base.models import save_forms_with_tracking
from django.contrib.auth.models import User
from mps.settings import DEFAULT_FROM_EMAIL

import ujson as json
import os

from mps.settings import MEDIA_ROOT

from django.template.loader import render_to_string, TemplateDoesNotExist

from datetime import datetime, timedelta
import pytz

# TODO Refactor imports
# TODO REFACTOR CERTAIN WHITTLING TO BE IN FORM AS OPPOSED TO VIEW
# TODO Rename get_absolute_url when the function does not actually return the model's URL
# TODO It is probably more semantic to overwrite get_context_data and form_valid in lieu of post and get for updates
# TODO ^ Update Views should be refactored soon
# NOTE THAT YOU NEED TO MODIFY INLINES HERE, NOT IN FORMS


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
        data_file_uploads = AssayDataFileUpload.objects.none()
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


# Class-based views for study configuration
class AssayStudyConfigurationList(LoginRequiredMixin, ListView):
    """Display a list of Study Configurations"""
    model = AssayStudyConfiguration
    template_name = 'assays/studyconfiguration_list.html'


# FormSet for Study Models
AssayStudyModelFormSet = inlineformset_factory(
    AssayStudyConfiguration,
    AssayStudyModel,
    extra=1,
    exclude=[],
    widgets={
        'label': forms.TextInput(attrs={'size': 2}),
        'sequence_number': forms.TextInput(attrs={'size': 2})
    }
)


class AssayStudyConfigurationAdd(OneGroupRequiredMixin, CreateView):
    """Add a Study Configuration with inline for Associtated Models"""
    template_name = 'assays/studyconfiguration_add.html'
    form_class = AssayStudyConfigurationForm

    def get_context_data(self, **kwargs):
        context = super(AssayStudyConfigurationAdd, self).get_context_data(**kwargs)

        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = AssayStudyModelFormSet(self.request.POST)
            else:
                context['formset'] = AssayStudyModelFormSet()

        return context

    def form_valid(self, form):
        formset = AssayStudyModelFormSet(self.request.POST, instance=form.instance)

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class AssayStudyConfigurationUpdate(OneGroupRequiredMixin, UpdateView):
    """Update a Study Configuration with inline for Associtated Models"""
    model = AssayStudyConfiguration
    template_name = 'assays/studyconfiguration_add.html'
    form_class = AssayStudyConfigurationForm

    def get_context_data(self, **kwargs):
        context = super(AssayStudyConfigurationUpdate, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = AssayStudyModelFormSet(self.request.POST, instance=self.object)
            else:
                context['formset'] = AssayStudyModelFormSet(instance=self.object)

        context['update'] = True

        return context

    def form_valid(self, form):
        formset = AssayStudyModelFormSet(self.request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


def get_queryset_with_organ_model_map(queryset):
    """Takes a queryset and returns it with a organ model map"""
    setups = AssayMatrixItem.objects.filter(
        organ_model__isnull=False
    ).prefetch_related(
        'matrix__study',
        'device',
        'organ_model',
        'organ_model_protocol'
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
    data_points = AssayDataPoint.objects.filter(
        replaced=False
    )

    data_points_map = {}

    for data_point in data_points:
        current_value = data_points_map.setdefault(
            data_point.study_id, 0
        )
        data_points_map.update({
            data_point.study_id: current_value + 1
        })

    images = AssayImage.objects.all().prefetch_related(
        'matrix_item'
    )

    images_map = {}

    for image in images:
        current_value = images_map.setdefault(
            image.matrix_item.study_id, 0
        )
        images_map.update({
            image.matrix_item.study_id: current_value + 1
        })

    for study in queryset:
        study.data_points = data_points_map.get(study.id, 0)
        study.images = images_map.get(study.id, 0)


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
        # DOESN'T MATTER, ANYTHING THAT IS SIGNED OFF CAN'T BE EDITED
        # get_queryset_with_stakeholder_sign_off(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(AssayStudyEditableList, self).get_context_data(**kwargs)

        # Adds the word "editable" to the page
        context['editable'] = 'Editable '

        return context


class AssayStudyList(LoginRequiredMixin, ListView):
    """A list of all studies"""
    template_name = 'assays/assaystudy_list.html'
    model = AssayStudy

    def get_queryset(self):
        queryset = AssayStudy.objects.all().prefetch_related(
            'created_by',
            'group',
            'signed_off_by'
        )

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
            AssayStudyStakeholder.objects.filter(
                group__name__in=user_group_names
            ).values_list('study_id', flat=True)
        ))

        missing_stakeholder_blacklist = list(set(
            AssayStudyStakeholder.objects.filter(
                signed_off_by_id=None,
                sign_off_required=True
            ).values_list('study_id', flat=True)
        ))

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

        # Show if:
        # 1: Study has group matching user_group_names
        # 2: Study has Stakeholder group matching user_group_name AND is signed off on
        # 3: Study has access group matching user_group_names AND is signed off on AND all Stakeholders have signed off
        # 4: Study is unrestricted AND is signed off on AND all Stakeholders have signed off
        combined = queryset.filter(**data_group_filter) | \
                   queryset.filter(**stakeholder_group_filter).exclude(**unsigned_off_filter) | \
                   queryset.filter(**access_group_filter).exclude(**unsigned_off_filter).exclude(
                       **missing_stakeholder_filter) | \
                   queryset.filter(**unrestricted_filter).exclude(**unsigned_off_filter).exclude(
                       **missing_stakeholder_filter)

        combined = combined.distinct()

        get_queryset_with_organ_model_map(combined)
        get_queryset_with_number_of_data_points(combined)
        get_queryset_with_stakeholder_sign_off(combined)

        return combined


class AssayStudyAdd(OneGroupRequiredMixin, CreateView):
    """Add a study"""
    template_name = 'assays/assaystudy_add.html'
    form_class = AssayStudyForm

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # Get group selection possibilities
        groups = filter_groups(self.request.user)

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, groups=groups)
        # If GET
        else:
            return form_class(groups=groups)

    def get_context_data(self, **kwargs):
        context = super(AssayStudyAdd, self).get_context_data(**kwargs)
        if self.request.POST:
            if 'study_assay_formset' not in context:
                context['study_assay_formset'] = AssayStudyAssayFormSetFactory(self.request.POST)
            if 'supporting_data_formset' not in context:
                context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(self.request.POST, self.request.FILES)
        else:
            context['study_assay_formset'] = AssayStudyAssayFormSetFactory()
            context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory()

        return context

    def form_valid(self, form):
        study_assay_formset = AssayStudyAssayFormSetFactory(
            self.request.POST,
            instance=form.instance
        )
        supporting_data_formset = AssayStudySupportingDataFormSetFactory(
            self.request.POST,
            self.request.FILES,
            instance=form.instance
        )
        if form.is_valid() and study_assay_formset.is_valid() and supporting_data_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[study_assay_formset, supporting_data_formset], update=False)
            return redirect(
                self.object.get_absolute_url()
            )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    study_assay_formset=study_assay_formset,
                    supporting_data_formset=supporting_data_formset
                )
            )


# TODO CHANGE
class AssayStudyUpdate(ObjectGroupRequiredMixin, UpdateView):
    """Update the fields of a Study"""
    model = AssayStudy
    template_name = 'assays/assaystudy_add.html'
    form_class = AssayStudyForm

    def get_form(self, form_class=None):
        form_class = self.get_form_class()
        # Get group selection possibilities
        groups = filter_groups(self.request.user)

        # If POST
        if self.request.method == 'POST':
            return form_class(self.request.POST, self.request.FILES, instance=self.object, groups=groups)
        # If GET
        else:
            return form_class(instance=self.object, groups=groups)

    def get_context_data(self, **kwargs):
        context = super(AssayStudyUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            if 'study_assay_formset' not in context:
                context['study_assay_formset'] = AssayStudyAssayFormSetFactory(self.request.POST, instance=self.object)
            if 'supporting_data_formset' not in context:
                context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['study_assay_formset'] = AssayStudyAssayFormSetFactory(instance=self.object)
            context['supporting_data_formset'] = AssayStudySupportingDataFormSetFactory(instance=self.object)

        context['update'] = True

        return context

    def form_valid(self, form):
        study_assay_formset = AssayStudyAssayFormSetFactory(
            self.request.POST,
            instance=form.instance
        )
        supporting_data_formset = AssayStudySupportingDataFormSetFactory(
            self.request.POST,
            self.request.FILES,
            instance=form.instance
        )

        # TODO TODO TODO TODO
        if form.is_valid() and study_assay_formset.is_valid() and supporting_data_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[study_assay_formset, supporting_data_formset], update=True)

            return redirect(
                self.object.get_absolute_url()
            )
        else:
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    study_assay_formset=study_assay_formset,
                    supporting_data_formset=supporting_data_formset
                )
            )


# TODO ADD PERMISSION MIXINS
class AssayStudyIndex(StudyViewerMixin, DetailView):
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
            study=self.object
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
            study=self.object,
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
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = 'attachment;filename=' + unicode(self.object) + '.csv'

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
                study=self.object,
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
                    AssayStudyStakeholder.objects.filter(
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
                        'stakeholders': AssayStudyStakeholder.objects.filter(study=self.object).order_by('-signed_off_date')
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
                        'stakeholders': AssayStudyStakeholder.objects.filter(study=self.object).order_by('-signed_off_date')
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

        return context

    def form_valid(self, form):
        if form.is_valid():
            data = form.cleaned_data
            overwrite_option = data.get('overwrite_option')

            study_id = str(self.object.id)

            # Add user to Study's modified by
            # TODO
            if self.request and self.request.FILES:
                self.object.bulk_file = data.get('bulk_file')
                self.object.modified_by = self.request.user
                self.object.save()

                file_processor = AssayFileProcessor(self.object.bulk_file, self.object, self.request.user, save=True)
                # Process the file
                file_processor.process_file()
                # parse_file_and_save(self.object.bulk_file, self.object.modified_by, study_id, overwrite_option, 'Bulk', form=None)

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
                            data_file_upload = AssayDataFileUpload.objects.filter(study=self.object, id=current_id)
                            if data_file_upload:
                                data_points_to_replace = AssayDataPoint.objects.filter(data_file_upload=data_file_upload).exclude(replaced=True)
                                data_points_to_replace.update(replaced=True)

            return redirect(self.object.get_absolute_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AssayStudyDelete(DeletionMixin, DeleteView):
    """Delete a Setup"""
    model = AssayStudy
    template_name = 'assays/assaystudy_delete.html'
    success_url = '/assays/assaystudy/'


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
                prefix='item',
                study=study,
                user=self.request.user
            )
        else:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                prefix='item',
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
            prefix='item',
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
        ).order_by(
            'addition_time',
            'compound_instance'
        )

        cell_queryset = AssaySetupCell.objects.filter(
            matrix_item__in=matrix_item_queryset
        ).order_by(
            'addition_time',
            'cell_sample',
        )

        setting_queryset = AssaySetupSetting.objects.filter(
            matrix_item__in=matrix_item_queryset
        ).order_by(
            'addition_time',
            'setting',
            'unit'
        )

        if self.request.POST:
            context['item_formset'] = AssayMatrixItemFormSetFactory(
                self.request.POST,
                instance=self.object,
                queryset=matrix_item_queryset,
                prefix='item',
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
                prefix='item',
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
            prefix='item',
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
        ).order_by(
            'addition_time',
            'compound_instance'
        )

        cell_queryset = AssaySetupCell.objects.filter(
            matrix_item__in=matrix_item_queryset
        ).order_by(
            'addition_time',
            'cell_sample',
        )

        setting_queryset = AssaySetupSetting.objects.filter(
            matrix_item__in=matrix_item_queryset
        ).order_by(
            'addition_time',
            'setting',
            'unit'
        )

        context['item_formset'] = AssayMatrixItemFormSetFactory(
            instance=self.object,
            queryset=matrix_item_queryset,
            prefix='item'
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

        cellsamples = get_cell_samples_for_selection(self.request.user)

        # Cellsamples will always be the same
        context['cellsamples'] = cellsamples

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
        if form.is_valid() and compound_formset.is_valid() and cell_formset.is_valid() and setting_formset.is_valid():
            save_forms_with_tracking(self, form, update=True, formset=[
                compound_formset,
                cell_formset,
                setting_formset
            ])

            try:
                data_point_ids_to_update_raw = json.loads(form.data.get('dynamic_exclusion', '{}'))
                data_point_ids_to_mark_excluded = [
                    int(id) for id, value in data_point_ids_to_update_raw.items() if value
                ]
                data_point_ids_to_mark_included = [
                    int(id) for id, value in data_point_ids_to_update_raw.items() if not value
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

        # Maybe useful later
        # get_user_status_context(self, context)

        return context
