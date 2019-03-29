from django.views.generic import DetailView, CreateView, UpdateView, ListView, TemplateView
from django.shortcuts import redirect
from django import forms

from .forms import MicrodeviceForm, OrganModelForm, OrganModelProtocolFormsetFactory, OrganModelLocationFormsetFactory
from .models import Microdevice, OrganModel, ValidatedAssay, OrganModelProtocol, MicrophysiologyCenter
from mps.mixins import SpecificGroupRequiredMixin, PermissionDenied, user_is_active
from mps.base.models import save_forms_with_tracking
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator


class OrganModelList(ListView):
    """Displays list of Organ Models"""
    template_name = 'microdevices/organmodel_list.html'

    def get_queryset(self):
        return OrganModel.objects.prefetch_related('organ', 'center', 'device', 'base_model').all()


class MicrodeviceList(ListView):
    """Displays list of Microdevices"""
    template_name = 'microdevices/microdevice_list.html'

    def get_queryset(self):
        return Microdevice.objects.prefetch_related('organ', 'center', 'manufacturer').all()


class OrganModelDetail(DetailView):
    """Displays details for an Organ Model"""
    model = OrganModel
    template_name = 'microdevices/organmodel_detail.html'

    def get_context_data(self, **kwargs):
        context = super(OrganModelDetail, self).get_context_data(**kwargs)

        assays = ValidatedAssay.objects.filter(organ_model_id=self.object.id).prefetch_related('assay', 'assay__assay_type')

        if self.object.center and any(i in self.object.center.groups.all() for i in self.request.user.groups.all()):
            protocols = OrganModelProtocol.objects.filter(
                organ_model_id=self.object.id
            ).order_by('-version')
        else:
            protocols = None

        context.update({
            'assays': assays,
            'protocols': protocols,
        })

        return context


class MicrodeviceDetail(DetailView):
    """Displays details for a Device"""
    model = Microdevice
    template_name = 'microdevices/microdevice_detail.html'


class MicrodeviceAdd(SpecificGroupRequiredMixin, CreateView):
    """Allows the addition of Devices"""
    model = Microdevice
    template_name = 'microdevices/microdevice_add.html'
    form_class = MicrodeviceForm

    required_group_name = 'Add Microdevices Front'

    def form_valid(self, form):
        if form.is_valid():
            save_forms_with_tracking(self, form, formset=False, update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class MicrodeviceUpdate(SpecificGroupRequiredMixin, UpdateView):
    """Allows Devices to be updated"""
    model = Microdevice
    template_name = 'microdevices/microdevice_add.html'
    form_class = MicrodeviceForm

    required_group_name = 'Change Microdevices Front'

    def get_context_data(self, **kwargs):
        context = super(MicrodeviceUpdate, self).get_context_data(**kwargs)
        context['update'] = True
        return context

    def form_valid(self, form):
        if form.is_valid():
            save_forms_with_tracking(self, form, formset=False, update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class OrganModelAdd(SpecificGroupRequiredMixin, CreateView):
    """Allows the addition of Organ Models"""
    model = OrganModel
    template_name = 'microdevices/organmodel_add.html'
    form_class = OrganModelForm

    required_group_name = 'Add Microdevices Front'

    def get_context_data(self, **kwargs):
        context = super(OrganModelAdd, self).get_context_data(**kwargs)
        if 'protocol_formset' not in context:
            if self.request.POST:
                context['protocol_formset'] = OrganModelProtocolFormsetFactory(self.request.POST, self.request.FILES)
                context['location_formset'] = OrganModelLocationFormsetFactory(self.request.POST, self.request.FILES)
            else:
                context['protocol_formset'] = OrganModelProtocolFormsetFactory()
                context['location_formset'] = OrganModelLocationFormsetFactory()

        return context

    def form_valid(self, form):
        protocol_formset = OrganModelProtocolFormsetFactory(
            self.request.POST,
            self.request.FILES,
            instance=form.instance
        )
        location_formset = OrganModelLocationFormsetFactory(
            self.request.POST,
            instance=form.instance
        )
        if form.is_valid() and protocol_formset.is_valid() and location_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[protocol_formset, location_formset], update=False)

            # Update the base model to be self-referential if it is missing
            if not form.instance.base_model_id:
                form.instance.base_model_id = form.instance.id
                form.instance.save()

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                protocol_formset=protocol_formset,
                location_formset=location_formset
            ))


# PLEASE NOTE THAT ORGAN MODEL DOES NOT USE A PERMISSION MIXIN
class OrganModelUpdate(UpdateView):
    """Allows Organ Models to be updated"""
    model = OrganModel
    template_name = 'microdevices/organmodel_add.html'
    form_class = OrganModelForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        """Special dispatch for Organ Model

        Rejects users with no groups and then rejects users without groups matching the center
        (if there is a center listed)
        """
        self.object = self.get_object()
        if self.request.user.groups.all().count() == 0 or self.object.center and not any(
            i in self.object.center.groups.all() for i in self.request.user.groups.all()
        ):
            return PermissionDenied(self.request, 'You must be a member of the center ' + str(self.object.center))
        return super(OrganModelUpdate, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrganModelUpdate, self).get_context_data(**kwargs)
        if 'protocol_formset' not in context:
            if self.request.POST:
                context['protocol_formset'] = OrganModelProtocolFormsetFactory(
                    self.request.POST,
                    self.request.FILES,
                    instance=self.object
                )
                context['location_formset'] = OrganModelLocationFormsetFactory(
                    self.request.POST,
                    instance=self.object
                )
            else:
                context['protocol_formset'] = OrganModelProtocolFormsetFactory(instance=self.object)
                context['location_formset'] = OrganModelLocationFormsetFactory(instance=self.object)

        context['update'] = True

        return context

    def form_valid(self, form):
        protocol_formset = OrganModelProtocolFormsetFactory(
            self.request.POST,
            self.request.FILES,
            instance=form.instance
        )
        location_formset = OrganModelLocationFormsetFactory(
            self.request.POST,
            instance=form.instance
        )
        if form.is_valid() and protocol_formset.is_valid() and location_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[protocol_formset, location_formset], update=True)

            # Update the base model to be self-referential if it is missing
            if not form.instance.base_model_id:
                form.instance.base_model_id = form.instance.id
                form.instance.save()

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                protocol_formset=protocol_formset,
                location_formset=location_formset
            ))


class MicrophysiologyCenterDetail(DetailView):
    """Displays details for a Microphysiology Center"""
    model = MicrophysiologyCenter
    template_name = 'microdevices/center_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MicrophysiologyCenterDetail, self).get_context_data(**kwargs)
        context['models'] = OrganModel.objects.filter(center_id=self.object.id).values_list('name', flat=True)
        context['pi_email_parts'] = self.object.pi_email.split("@")
        context['contact_email_parts'] = self.object.contact_email.split("@")

        return context
