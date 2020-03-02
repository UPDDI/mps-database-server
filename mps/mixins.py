from mps.templatetags.custom_filters import (
    has_group,
    is_group_viewer,
    is_group_editor,
    is_group_admin
)
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.template import loader
from django.http import HttpResponseForbidden
from assays.models import (
    AssayStudy,
    AssayStudyStakeholder
)
from mps.templatetags.custom_filters import (
    filter_groups,
    VIEWER_SUFFIX,
    ADMIN_SUFFIX
)

from mps.base.models import save_forms_with_tracking

from django.views.generic import UpdateView

import urllib

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE

from django.contrib.admin.utils import (
    construct_change_message
)

from django.contrib.contenttypes.models import ContentType

# Unsemantic! Breaks PEP! BAD!
def PermissionDenied(request, message, log_in_link=True):
    """This function will take a string a render 403.html with that string as context"""
    template = loader.get_template('403.html')
    context = {
        'message': message
    }

    if log_in_link and not request.user.is_authenticated:
        context.update({
            'intended_path': request.get_full_path()
        })

    return HttpResponseForbidden(template.render(context, request))

# def check_if_user_is_active(user):
#     if not user or not user.is_active:
#         return PermissionDenied(
#             self.request,
#             'Your account is not currently active<br>'
#             'If you have recently registered, be sure to check your email for the activation link<br>'
#             'If you suspect this is an error, please contact an administrator'
#         )
#     else:
#         return None


def user_is_active(user):
    """Checks whether the user is active"""
    return user.is_active


def user_is_valid_study_viewer(user, study):
    # Find whether valid viewer by checking group and iterating over all access_groups
    valid_viewer = is_group_viewer(user, study.group.name)

    # ALWAYS CHECK COLLABORATOR GROUPS
    collaborator_group_names = {name: True for name in study.collaborator_groups.all().values_list('name', flat=True)}

    user_group_names = user.groups.all().values_list('name', flat=True)

    if collaborator_group_names:
        for group_name in user_group_names:
            if group_name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') in collaborator_group_names:
                valid_viewer = True
                # Only iterate as many times as is needed
                return valid_viewer

    # Only check access groups if the study IS signed off on
    if not valid_viewer and study.signed_off_by:
        # Check if user is a stakeholder
        stakeholders = AssayStudyStakeholder.objects.filter(
            study_id=study.id
        ).prefetch_related(
            'study',
            'group',
            'signed_off_by'
        )
        stakeholder_group_names = {name: True for name in stakeholders.values_list('group__name', flat=True)}
        for group_name in user_group_names:
            if group_name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') in stakeholder_group_names:
                valid_viewer = True
                # Only iterate as many times as is needed
                return valid_viewer

        # It not, check if all stake holders have signed off
        all_required_stakeholders_have_signed_off = stakeholders.filter(
            sign_off_required=True,
            signed_off_by_id=None
        ).count() == 0

        # Check if user needs to be checked for access groups
        if all_required_stakeholders_have_signed_off:
            access_group_names = {name: True for name in study.access_groups.all().values_list('name', flat=True)}

            if access_group_names:
                for group_name in user_group_names:
                    if group_name.replace(VIEWER_SUFFIX, '').replace(ADMIN_SUFFIX, '') in access_group_names:
                        valid_viewer = True
                        # Only iterate as many times as is needed
                        return valid_viewer

            # FINALLY: Check if the study is unrestricted
            if not study.restricted:
                valid_viewer = True
                return valid_viewer

    return valid_viewer


# Add this mixin via multiple-inheritance and you need not change the dispatch every time
class LoginRequiredMixin(object):
    """This mixin requires the user to log in before continuing"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class OneGroupRequiredMixin(object):
    """This mixin requires the user to have at least one group"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        # if self.request.user.groups.all().count() == 0:
        #     return PermissionDenied(self.request, 'You must be a member of at least one group')
        valid_groups = filter_groups(self.request.user)
        if not valid_groups:
            return PermissionDenied(self.request, 'You must be a member of at least one group')
        return super(OneGroupRequiredMixin, self).dispatch(*args, **kwargs)


class ObjectGroupRequiredMixin(object):
    """This mixin requires group matching object's bound group"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        if not is_group_editor(self.request.user, self.object.group.name):
            return PermissionDenied(self.request, 'You must be a member of the group ' + str(self.object.group))
        if self.object.signed_off_by:
            return PermissionDenied(
                self.request,
                'You cannot edit this because it has been signed off by {0} {1}.'
                ' If something needs to be changed, contact the individual who signed off.'
                ' If you are the individual who signed off, please contact a database administrator.'.format(
                    self.object.signed_off_by.first_name,
                    self.object.signed_off_by.last_name
                )
            )
        return super(ObjectGroupRequiredMixin, self).dispatch(*args, **kwargs)


# CLONING IS NOT CURRENTLY AVAILABLE
# It is ostensibly possible to jam the user's status here so that it need not be acquired again
class StudyGroupMixin(object):
    """This mixin requires the user to have the group matching the study's group

    Attributes:
    detail - indicates that a detail page was initially requested
    update_redirect_url - where to to redirect in the case of detail redirect
    """
    detail = False
    # Default value for url to redirect to
    update_redirect_url = 'update/'

    # @method_decorator(login_required)
    # @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        # This is for adding study components
        if self.kwargs.get('study_id', ''):
            study = get_object_or_404(AssayStudy, pk=self.kwargs['study_id'])

            if not is_group_editor(self.request.user, study.group.name):
                return PermissionDenied(self.request, 'You must be a member of the group ' + str(study.group))

            if study.signed_off_by:
                return PermissionDenied(
                    self.request,
                    'You cannot add this because the study has been signed off by {0} {1}.'
                    ' If something needs to be changed, contact the individual who signed off.'
                    ' If you are the individual who signed off, please contact a database administrator.'.format(
                        study.signed_off_by.first_name,
                        study.signed_off_by.last_name
                    )
                )

        else:
            try:
                current_object = self.get_object()
            except:
                # Evil except here!
                return PermissionDenied(self.request, 'An error has occurred.')

            study = current_object.study

            # Group editors can always see
            if is_group_editor(self.request.user, study.group.name) and not study.signed_off_by:
                # Redirects either to url + update or the specified url + object ID (as an attribute)
                # This is a little tricky if you don't look for {} in update_redirect_url
                if self.detail:
                    return redirect(self.update_redirect_url.format(current_object.id))
                else:
                    return super(StudyGroupMixin, self).dispatch(*args, **kwargs)

            valid_viewer = user_is_valid_study_viewer(self.request.user, study)

            # If the object is not restricted and the user is NOT a listed viewer
            # if study.restricted and not valid_viewer:
            if not valid_viewer:
                return PermissionDenied(self.request, 'You must be a member of the group ' + str(study.group))

            if study.signed_off_by and not self.detail:
                return PermissionDenied(
                    self.request,
                    'You cannot modify this because the study has been signed off by {0} {1}.'
                    ' If something needs to be changed, contact the individual who signed off.'
                    ' If you are the individual who signed off, please contact a database administrator.'.format(
                        study.signed_off_by.first_name,
                        study.signed_off_by.last_name
                    )
                )

            # Otherwise return the detail view
            if self.detail:
                return super(StudyGroupMixin, self).dispatch(*args, **kwargs)
            else:
                return PermissionDenied(self.request, 'You do not have permission to edit this.')

        return super(StudyGroupMixin, self).dispatch(*args, **kwargs)


class StudyViewerMixin(object):
    """This mixin determines whether a user can view the study and its data"""

    # @method_decorator(login_required)
    # @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        # Get the study
        study = get_object_or_404(AssayStudy, pk=self.kwargs['pk'])

        valid_viewer = user_is_valid_study_viewer(self.request.user, study)
        # If the object is not restricted and the user is NOT a listed viewer, deny permission
        # if self.object.restricted and not valid_viewer:
        if not valid_viewer:
            return PermissionDenied(self.request, 'You must be a member of the group ' + str(study.group))
        # Otherwise return the detail view
        return super(StudyViewerMixin, self).dispatch(*args, **kwargs)


# NOT CURRENTLY USED
# Require user to be the creator or a group admin
class CreatorOrAdminRequiredMixin(object):
    """This mixin requires the user to be the creator of the object"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    # Deny access if not the CREATOR
    # Note the call for request.user.is_authenticated
    # Interestingly, Django wraps request.user until it is accessed
    # Thus, to perform this comparison it is necessary to access request.user via authentication
    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        if not self.request.user.is_authenticated or (self.request.user != self.object.created_by and not is_group_admin(self.request.user, self.object.group.name)):
            return PermissionDenied(self.request, 'You do not have permission to view this page. Please contact an administrator if you need assistance.')
        return super(CreatorOrAdminRequiredMixin, self).dispatch(*args, **kwargs)


# Require user to be the creator or a group admin
class CreatorOrSuperuserRequiredMixin(object):
    """This mixin requires the user to be the creator of the object"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    # Deny access if not the CREATOR
    # Note the call for request.user.is_authenticated
    # Interestingly, Django wraps request.user until it is accessed
    # Thus, to perform this comparison it is necessary to access request.user via authentication
    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.signed_off_by:
            return PermissionDenied(
                self.request,
                'You cannot change this entry because it has been signed off on.'
            )
        if not self.request.user.is_authenticated or (self.request.user != self.object.created_by and not self.request.user.is_superuser):
            return PermissionDenied(self.request, 'Only the creator of this entry can view this page.')
        return super(CreatorOrSuperuserRequiredMixin, self).dispatch(*args, **kwargs)


# Require user to be a group admin
class AdminRequiredMixin(object):
    """This mixin requires the user to be a group admin"""

    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        if not is_group_admin(self.request.user, self.object.group.name):
            return PermissionDenied(self.request, 'Only group admins can perform this action. Please contact your group admin.')
        return super(AdminRequiredMixin, self).dispatch(*args, **kwargs)


class StudyDeletionMixin(object):
    """This mixin requires the user to be an admin and also needs the object to have no relations"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        # Superusers always have access
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return super(StudyDeletionMixin, self).dispatch(*args, **kwargs)

        self.object = self.get_object()

        group = getattr(self.object, 'group', None)
        study = getattr(self.object, 'study', None)
        study_sign_off = False

        if not group and study:
            # group = study.group
            study_sign_off = study.signed_off_by

            # group = group.name
            #
            # if not is_group_admin(self.request.user, group):
            #     return PermissionDenied(self.request, 'Only group admins can perform this action. Please contact your group admin.')

            if study_sign_off:
                return PermissionDenied(
                    self.request,
                    'You cannot modify this because the study has been signed off by {0} {1}.'
                    ' If something needs to be changed, contact the individual who signed off.'
                    ' If you are the individual who signed off, please contact a database administrator.'.format(
                        study.signed_off_by.first_name,
                        study.signed_off_by.last_name
                    )
                )

        if self.request.user.id != self.object.created_by_id:
            return PermissionDenied(self.request, 'Only the creator of this entry can perform this action. Please contact an administrator or the creator of this entry.')

        can_be_deleted = True

        # If this view has "ignore_propagation", don't bother with this
        # if not getattr(self, 'ignore_propagation', None):
        #     for current_field in self.object._meta.get_fields():
        #         # TODO MODIFY TO CHECK M2M MANAGERS IN THE FUTURE
        #         # TODO REVISE
        #         if str(type(current_field)) == "<class 'django.db.models.fields.reverse_related.ManyToOneRel'>":
        #             manager = getattr(self.object, current_field.name + '_set')
        #             count = manager.count()
        #             if count > 0:
        #                 can_be_deleted = False
        #                 break

        # Gets rather specific... REFACTOR
        # Check if there are data points, forbid if yes
        if study and getattr(self.object, 'assaydatapoint_set', None):
            # WARNING: The nature of replacement may change
            if self.object.assaydatapoint_set.filter(replaced=False).count() > 0:
                return PermissionDenied(
                    self.request,
                    'Data Points depend on this, so it cannot be deleted.'
                    ' Either delete the linked Data Points or contact a Database Administrator if you would like to delete this.'
                )
        elif study and getattr(self.object, 'assaymatrixitem_set', None):
            # Inefficient
            for matrix_item in self.object.assaymatrixitem_set.all():
                # WARNING: The nature of replacement may change
                if matrix_item.assaydatapoint_set.filter(replaced=False).count() > 0:
                    return PermissionDenied(
                        self.request,
                        'Data Points depend on this, so it cannot be deleted.'
                        ' Either delete the linked Data Points or contact a Database Administrator if you would like to delete this.'
                    )

        if not can_be_deleted:
            return PermissionDenied(
                self.request,
                'Other entries depend on this, so it cannot be deleted.'
                ' Either delete the linked entries or contact a Database Administrator if you would like to delete it.'
            )

        return super(StudyDeletionMixin, self).dispatch(*args, **kwargs)


class CreatorAndNotInUseMixin(object):
    """This mixin requires the user to be the creator and prevents access if the model is in use"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        # Superusers always have access
        if self.request.user.is_authenticated and self.request.user.is_superuser:
            return super(CreatorAndNotInUseMixin, self).dispatch(*args, **kwargs)

        self.object = self.get_object()

        # Make sure this is the creator
        if self.request.user.id != self.object.created_by_id:
            return PermissionDenied(self.request, 'Only the creator of this entry can perform this action. Please contact an administrator or the creator of this entry.')

        can_be_modified = True

        # relations_to_check = {
        #     "<class 'django.db.models.fields.reverse_related.ManyToOneRel'>": True,
        #     "<class 'django.db.models.fields.reverse_related.ManyToOneRel'>": True,
        # }

        for current_field in self.object._meta.get_fields():
            # TODO MODIFY TO CHECK M2M MANAGERS IN THE FUTURE
            # TODO REVISE
            # if str(type(current_field)) in relations_to_check:
            if str(type(current_field)) == "<class 'django.db.models.fields.reverse_related.ManyToOneRel'>":
                manager = getattr(self.object, current_field.name + '_set', '')
                if manager:
                    count = manager.count()
                    if count > 0:
                        can_be_modified = False
                        break

        if not can_be_modified:
            return PermissionDenied(
                self.request,
                'Other entries depend on this, so it cannot be modified.'
                ' Either delete the linked entries (if they belong to you) or contact a Database Administrator if you would like to modify it.'
            )

        return super(CreatorAndNotInUseMixin, self).dispatch(*args, **kwargs)


# DEPRECATED
# Require the specified group or fail
class SpecificGroupRequiredMixin(object):
    """This mixin requires the user to have a specific group

    PLEASE NOTE: you must add the attribute 'required_group_name' to the view in question
    """
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        if has_group(self.request.user, self.required_group_name):
            return super(SpecificGroupRequiredMixin, self).dispatch(*args, **kwargs)
        else:
            return PermissionDenied(
                self.request,
                'Contact an administrator if you would like to gain permission'
            )


class SuperuserRequiredMixin(object):
    """This mixin checks if the user is a superuser"""
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated or not self.request.user.is_superuser:
            return PermissionDenied(self.request, 'Please contact a database administrator if you need to have this entry modified.')
        return super(SuperuserRequiredMixin, self).dispatch(*args, **kwargs)


class HistoryMixin(object):
    def get_context_data(self, **kwargs):
        context = super(HistoryMixin, self).get_context_data(**kwargs)

        object_id = self.kwargs.get('pk', 0)

        if object_id:
            context.update({
                'history': LogEntry.objects.filter(
                    object_id=object_id,
                    content_type_id=ContentType.objects.get_for_model(self.model, for_concrete_model=False).pk,
                ).prefetch_related(
                    'user'
                )
            })

        return context

class FormHandlerMixin(HistoryMixin):
    """Mixin for handling forms, whether they have formsets and/or are popups"""
    formsets = ()
    is_update = False

    # Default to generic_form template
    template_name = 'generic_form.html'

    def __init__(self, *args, **kwargs):
        super(FormHandlerMixin, self).__init__(*args, **kwargs)

        # Initialize dictionary of all forms
        self.all_forms = {}

        # Mark as is_update if UpdateView is one of the bases
        if UpdateView in self.__class__.__bases__:
            self.is_update = True

    # Kind of odd that these shadow the keyword object?
    def log_addition(self, request, object, message):
        """
        Log that an object has been successfully added.

        The default implementation creates an admin LogEntry object.
        """
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(object, for_concrete_model=False).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=ADDITION,
            change_message=message,
        )

    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(object, for_concrete_model=False).pk,
            object_id=object.pk,
            object_repr=str(object),
            action_flag=CHANGE,
            change_message=message,
        )

    def get_form_kwargs(self):
        kwargs = super(FormHandlerMixin, self).get_form_kwargs()

        # Add user as kwarg
        kwargs.update({
            'user': self.request.user
        })

        return kwargs

    def pre_save_processing(self, form):
        """For if there needs to be extra processing before a save"""
        pass

    def extra_form_processing(self):
        """For if there needs to be extra processing after a save"""
        pass

    def get_context_data(self, **kwargs):
        context = super(FormHandlerMixin, self).get_context_data(**kwargs)

        # Add model name
        context.update({
            'model_verbose_name': self.model._meta.verbose_name,
            'model_verbose_name_plural': self.model._meta.verbose_name_plural
        })

        for formset_name, formset_factory in self.formsets:
            data_for_factory = []

            if self.request.POST:
                data_for_factory = [
                    self.request.POST,
                    self.request.FILES
                ]

            if formset_name not in context:
                if data_for_factory:
                    if self.is_update:
                        current_formset = formset_factory(
                            *data_for_factory,
                            instance=self.object
                        )
                    else:
                        current_formset = formset_factory(
                            *data_for_factory
                        )
                else:
                    if self.is_update:
                        current_formset = formset_factory(
                            instance=self.object
                        )
                    else:
                        current_formset = formset_factory()

                context.update({
                    formset_name: current_formset
                })

        if self.is_update:
            context.update({
                'update': self.is_update
            })

        return context

    def form_valid(self, form):
        is_popup = self.request.GET.get('popup', 0) == '1'

        all_formsets = []
        self.all_forms = {
            'form': form
        }
        for formset_name, formset_factory in self.formsets:
            current_formset = formset_factory(
                self.request.POST,
                self.request.FILES,
                instance=form.instance
            )

            all_formsets.append(current_formset)
            self.all_forms.update({
                formset_name: current_formset
            })

        all_formsets_valid = True

        for formset in all_formsets:
            current_is_valid = formset.is_valid()

            if not current_is_valid:
                all_formsets_valid = False

        if form.is_valid() and all_formsets_valid:
            # NEEDS TESTING: SLOPPY SOLUTION TO GETTING new_objects ATTRIBUTE
            for formset in all_formsets:
                formset.save(commit=False)

            # The tricky think about this is that it makes changing stuff for matrices quite unpleasant...
            # Then again, do we need to robustly track the precise changes?
            change_message = construct_change_message(form, all_formsets, not self.is_update)

            # May or may not do anything
            self.pre_save_processing(form)

            save_forms_with_tracking(self, form, formset=all_formsets, update=self.is_update)

            # May or may not do anything
            self.extra_form_processing()

            if not self.is_update:
                self.log_addition(self.request, self.object, change_message)
            else:
                self.log_change(self.request, self.object, change_message)

            if is_popup:
                if self.object.id:
                    if hasattr(self.object, 'get_string_for_processing'):
                        return redirect(
                            '{}?popup=1&close=1&app={}&model={}&new_pk={}&new_name={}'.format(
                                self.object.get_post_submission_url(),
                                self.object._meta.app_label,
                                self.object._meta.object_name,
                                self.object.id,
                                urllib.parse.quote(str(self.object.get_string_for_processing())),
                            )
                        )
                    else:
                        return redirect(
                            '{}?popup=1&close=1&app={}&model={}&new_pk={}&new_name={}'.format(
                                self.object.get_post_submission_url(),
                                self.object._meta.app_label,
                                self.object._meta.object_name,
                                self.object.id,
                                urllib.parse.quote(str(self.object)),
                            )
                        )
                else:
                    return redirect(
                        '{}?popup=1&close=1'.format(
                            self.object.get_post_submission_url()
                        )
                    )
            else:
                return redirect(
                    self.object.get_post_submission_url()
                )
        else:
            # Need to have the forms processed so that they have errors
            return self.render_to_response(
                self.get_context_data(**self.all_forms)
            )


# Possible
class ListHandlerMixin(object):
    template_name = 'generic_list.html'

    def get_context_data(self, **kwargs):
        context = super(ListHandlerMixin, self).get_context_data(**kwargs)

        # Add model name
        context.update({
            'model_verbose_name': self.model._meta.verbose_name,
            'model_verbose_name_plural': self.model._meta.verbose_name_plural
        })

        return context


class DetailHandlerMixin(object):
    template_name = 'generic_detail.html'
