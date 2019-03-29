from django import forms
from .models import Compound, CompoundTarget
from django.views.generic import ListView, DetailView, CreateView, UpdateView
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
from mps.mixins import SpecificGroupRequiredMixin
# from django.shortcuts import render_to_response
# from django.template import RequestContext
from .forms import (
    CompoundTargetFormset,
    CompoundForm,
)
from django.shortcuts import redirect
from mps.base.models import save_forms_with_tracking


class CompoundsList(ListView):
    """Display a list of compounds (not to be confused with CompoundReport"""
    model = Compound
    template_name = 'compounds/compounds_list.html'
    # If variable pagination is desired, just jam that into GET too
    # paginate_by = 50
    #
    # def get_queryset(self):
    #     try:
    #         name = self.request.GET['name']
    #     except:
    #         name = ''
    #     if (name != ''):
    #         object_list = self.model.objects.filter(name__icontains = name)
    #     else:
    #         object_list = self.model.objects.all()
    #     return object_list


class CompoundsDetail(DetailView):
    """Show a Compounds details (no editing)"""
    model = Compound
    template_name = 'compounds/compounds_detail.html'

    def get_object(self, queryset=None):
        obj = super(CompoundsDetail, self).get_object(queryset)

        # If there is a compound
        if obj:
            # Get the associated targets
            targets = CompoundTarget.objects.filter(compound_id=obj.id)
            # For each target, split up the actions so they can be individual labels
            for target in targets:
                target.actions = [action for action in target.action.split(', ') if action]
            obj.targets = targets

        return obj

    def get_context_data(self, **kwargs):
        compounds = list(Compound.objects.all().order_by('name').values_list('id', flat=True))
        current = compounds.index(int(self.kwargs.get('pk')))

        if current == 0:
            previous_compound = compounds[-1]
        else:
            previous_compound = compounds[current - 1]
        if current == len(compounds)-1:
            next_compound = compounds[0]
        else:
            next_compound = compounds[current + 1]

        context = super(CompoundsDetail, self).get_context_data(**kwargs)

        context.update({'previous': previous_compound, 'next': next_compound})
        return context


class CompoundsAdd(SpecificGroupRequiredMixin, CreateView):
    """Add a compound"""
    form_class = CompoundForm
    template_name = 'compounds/compounds_add.html'

    required_group_name = 'Add Compounds Front'

    def get_context_data(self, **kwargs):
        context = super(CompoundsAdd, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = CompoundTargetFormset(self.request.POST)
            else:
                context['formset'] = CompoundTargetFormset()

        return context

    def form_valid(self, form):
        formset = CompoundTargetFormset(self.request.POST, instance=form.instance)

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class CompoundsUpdate(SpecificGroupRequiredMixin, UpdateView):
    """Update a Compound"""
    model = Compound
    form_class = CompoundForm
    template_name = 'compounds/compounds_add.html'

    required_group_name = 'Change Compounds Front'

    def get_context_data(self, **kwargs):
        context = super(CompoundsUpdate, self).get_context_data(**kwargs)
        if 'formset' not in context:
            if self.request.POST:
                context['formset'] = CompoundTargetFormset(self.request.POST)
            else:
                context['formset'] = CompoundTargetFormset(instance=self.object)

        context['update'] = True

        return context

    def form_valid(self, form):
        formset = CompoundTargetFormset(self.request.POST, instance=form.instance)

        if form.is_valid() and formset.is_valid():
            save_forms_with_tracking(self, form, formset=formset, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


# Currently, compounds report basically begins as just a compounds list
class CompoundsReport(ListView):
    """Displays page for a Compound Report"""
    model = Compound
    template_name = 'compounds/compounds_report.html'
