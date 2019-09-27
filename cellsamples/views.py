# coding=utf-8

from django.views.generic import ListView, CreateView, UpdateView
from .models import CellSample, CellType, CellSubtype
from .forms import CellSampleForm, CellTypeForm, CellSubtypeForm
from mps.mixins import LoginRequiredMixin, OneGroupRequiredMixin, SpecificGroupRequiredMixin, PermissionDenied, user_is_active, FormHandlerMixin
from mps.templatetags.custom_filters import filter_groups
from django.shortcuts import redirect

from mps.base.models import save_forms_with_tracking

from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from mps.templatetags.custom_filters import has_group, is_group_editor


class CellSampleMixin(FormHandlerMixin):
    model = CellSample
    template_name = 'cellsamples/cellsample_add.html'
    form_class = CellSampleForm


class CellSampleAdd(SpecificGroupRequiredMixin, CellSampleMixin, CreateView):
    required_group_name = 'Add Cell Samples Front'


class CellSampleUpdate(CellSampleMixin, UpdateView):
    required_group_name = 'Change Cell Samples Front'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        """Special dispatch for Cell Sample

        Rejects users that lack either the Change Cell Samples group or the Cell Sample's bound group
        """
        self.object = self.get_object()
        if not has_group(self.request.user, self.required_group_name):
            return PermissionDenied(self.request, 'Contact an administrator if you would like to gain permission')
        if not is_group_editor(self.request.user, self.object.group.name):
            return PermissionDenied(self.request, 'You must be a member of the group ' + str(self.object.group))
        return super(CellSampleUpdate, self).dispatch(*args, **kwargs)


class CellSampleList(LoginRequiredMixin, ListView):
    """Displays a list of Cell Samples"""
    template_name = 'cellsamples/cellsample_list.html'

    def get_queryset(self):
        queryset = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'cell_subtype',
            'supplier',
            'group',
            'signed_off_by'
        )
        return queryset


class CellTypeMixin(FormHandlerMixin):
    model = CellType
    template_name = 'cellsamples/celltype_add.html'
    form_class = CellTypeForm


class CellTypeAdd(SpecificGroupRequiredMixin, CellTypeMixin, CreateView):
    required_group_name = 'Add Cell Samples Front'


class CellTypeUpdate(SpecificGroupRequiredMixin, CellTypeMixin, UpdateView):
    required_group_name = 'Change Cell Samples Front'


class CellTypeList(ListView):
    """Display all Cell Types"""
    template_name = 'cellsamples/celltype_list.html'

    def get_queryset(self):
        queryset = CellType.objects.all().prefetch_related('organ')
        return queryset


class CellSubtypeMixin(FormHandlerMixin):
    """Add a Cell Subtype"""
    model = CellSubtype
    template_name = 'cellsamples/cellsubtype_add.html'
    form_class = CellSubtypeForm


class CellSubtypeAdd(SpecificGroupRequiredMixin, CellSubtypeMixin, CreateView):
    required_group_name = 'Add Cell Samples Front'


class CellSubtypeUpdate(SpecificGroupRequiredMixin, CellSubtypeMixin, UpdateView):
    required_group_name = 'Change Cell Samples Front'


class CellSubtypeList(ListView):
    """Display a list of Cell Subtypes"""
    template_name = 'cellsamples/cellsubtype_list.html'

    def get_queryset(self):
        queryset = CellSubtype.objects.all().prefetch_related(
            'cell_type',
            'cell_type__organ'
        )
        return queryset

# OLD
# class CellSampleAdd(SpecificGroupRequiredMixin, CreateView):
#     """Add a Cell Sample"""
#     template_name = 'cellsamples/cellsample_add.html'
#     form_class = CellSampleForm
#
#     required_group_name = 'Add Cell Samples Front'
#
#     def get_form(self, form_class=None):
#         form_class = self.get_form_class()
#         # Get group selection possibilities
#         groups = filter_groups(self.request.user)
#
#         # If POST
#         if self.request.method == 'POST':
#             return form_class(groups, self.request.POST, self.request.FILES)
#         # If GET
#         else:
#             return form_class(groups)
#
#     # Test form validity
#     def form_valid(self, form):
#         # get user via self.request.user
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=None, update=False)
#             return redirect('/cellsamples/cellsample')
#         else:
#             return self.render_to_response(self.get_context_data(form=form))
#
#
# # NOTE THAT CELL SAMPLE DOES NOT USE A PERMISSION MIXIN
# # Note that updating a model clears technically blank fields (exclude in form to avoid this)
# class CellSampleUpdate(UpdateView):
#     """Update a Cell Sample"""
#     model = CellSample
#     template_name = 'cellsamples/cellsample_add.html'
#     form_class = CellSampleForm
#
#     required_group_name = 'Change Cell Samples Front'
#
#     @method_decorator(login_required)
#     @method_decorator(user_passes_test(user_is_active))
#     def dispatch(self, *args, **kwargs):
#         """Special dispatch for Cell Sample
#
#         Rejects users that lack either the Change Cell Samples group or the Cell Sample's bound group
#         """
#         self.object = self.get_object()
#         if not has_group(self.request.user, self.required_group_name):
#             return PermissionDenied(self.request, 'Contact an administrator if you would like to gain permission')
#         if not is_group_editor(self.request.user, self.object.group.name):
#             return PermissionDenied(self.request, 'You must be a member of the group ' + str(self.object.group))
#         return super(CellSampleUpdate, self).dispatch(*args, **kwargs)
#
#     def get_form(self, form_class=None):
#         form_class = self.get_form_class()
#         # Get group selection possibilities
#         groups = filter_groups(self.request.user)
#
#         # If POST
#         if self.request.method == 'POST':
#             return form_class(groups, self.request.POST, self.request.FILES, instance=self.get_object())
#         # If GET
#         else:
#             return form_class(groups, instance=self.get_object())
#
#     def get_context_data(self, **kwargs):
#         context = super(CellSampleUpdate, self).get_context_data(**kwargs)
#         context['update'] = True
#         return context
#
#     # Test form validity
#     def form_valid(self, form):
#         # get user via self.request.user
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=None, update=True)
#             return redirect('/cellsamples/cellsample')
#         else:
#             return self.render_to_response(self.get_context_data(form=form))

# OLD
# class CellTypeAdd(SpecificGroupRequiredMixin, CreateView):
#     """Add a Cell Type"""
#     template_name = 'cellsamples/celltype_add.html'
#     form_class = CellTypeForm
#
#     required_group_name = 'Add Cell Samples Front'
#
#     # Test form validity
#     def form_valid(self, form):
#         # get user via self.request.user
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=None, update=False)
#             return redirect('/cellsamples/celltype')
#         else:
#             return self.render_to_response(self.get_context_data(form=form))
#
#
# # Note that updating a model clears technically blank fields (exclude in form to avoid this)
# class CellTypeUpdate(SpecificGroupRequiredMixin, UpdateView):
#     """Update a Cell Type"""
#     model = CellType
#     template_name = 'cellsamples/celltype_add.html'
#     form_class = CellTypeForm
#
#     required_group_name = 'Change Cell Samples Front'
#
#     def get_context_data(self, **kwargs):
#         context = super(CellTypeUpdate, self).get_context_data(**kwargs)
#         context['update'] = True
#         return context
#
#     # Test form validity
#     def form_valid(self, form):
#         # get user via self.request.user
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=None, update=True)
#             return redirect('/cellsamples/celltype')
#         else:
#             return self.render_to_response(self.get_context_data(form=form))

# OLD
# class CellSubtypeAdd(SpecificGroupRequiredMixin, CreateView):
#     """Add a Cell Subtype"""
#     template_name = 'cellsamples/cellsubtype_add.html'
#     form_class = CellSubtypeForm
#
#     required_group_name = 'Add Cell Samples Front'
#
#     # Test form validity
#     def form_valid(self, form):
#         # get user via self.request.user
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=None, update=False)
#             return redirect('/cellsamples/cellsubtype')
#         else:
#             return self.render_to_response(self.get_context_data(form=form))
#
#
# class CellSubtypeUpdate(SpecificGroupRequiredMixin, UpdateView):
#     """Update a Cell Subtype"""
#     model = CellSubtype
#     template_name = 'cellsamples/cellsubtype_add.html'
#     form_class = CellSubtypeForm
#
#     required_group_name = 'Change Cell Samples Front'
#
#     def get_context_data(self, **kwargs):
#         context = super(CellSubtypeUpdate, self).get_context_data(**kwargs)
#         context['update'] = True
#         return context
#
#     # Test form validity
#     def form_valid(self, form):
#         # get user via self.request.user
#         if form.is_valid():
#             save_forms_with_tracking(self, form, formset=None, update=True)
#             return redirect('/cellsamples/cellsubtype')
#         else:
#             return self.render_to_response(self.get_context_data(form=form))
