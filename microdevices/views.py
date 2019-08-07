from django.views.generic import DetailView, CreateView, UpdateView, ListView, TemplateView
from django.shortcuts import redirect
from django import forms

# Really it probably would have been better to have just used namespaces
from .forms import (
    MicrodeviceForm,
    OrganModelForm,
    OrganModelProtocolFormsetFactory,
    OrganModelLocationFormsetFactory,
    OrganModelReferenceFormSetFactory,
    OrganModelProtocolForm,
    OrganModelCellFormsetFactory,
    OrganModelProtocolCellFormsetFactory,
    OrganModelProtocolSettingFormsetFactory,
    MicrodeviceReferenceFormSetFactory
)
from .models import (
    Microdevice,
    OrganModel,
    ValidatedAssay,
    OrganModelProtocol,
    MicrophysiologyCenter,
    OrganModelCell,
    OrganModelProtocolCell,
    OrganModelProtocolSetting,
)

from cellsamples.models import CellSample

from mps.mixins import SpecificGroupRequiredMixin, PermissionDenied, user_is_active
from mps.base.models import save_forms_with_tracking
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from assays.models import AssayReference


class OrganModelList(ListView):
    """Displays list of Organ Models"""
    template_name = 'microdevices/organmodel_list.html'

    def get_queryset(self):
        return OrganModel.objects.prefetch_related(
            'organ',
            'center',
            'device',
            'base_model',
            'organmodelprotocol_set'
        ).all()


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

    def get_context_data(self, **kwargs):
        context = super(MicrodeviceAdd, self).get_context_data(**kwargs)
        if self.request.POST:
            if 'reference_formset' not in context:
                context['reference_formset'] = MicrodeviceReferenceFormSetFactory(self.request.POST)
        else:
            context['reference_formset'] = MicrodeviceReferenceFormSetFactory()

        context['reference_queryset'] = AssayReference.objects.all()

        return context

    def form_valid(self, form):
        reference_formset = MicrodeviceReferenceFormSetFactory(
            self.request.POST,
            instance=form.instance
        )
        if form.is_valid() and reference_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[reference_formset], update=False)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, reference_formset=reference_formset))


class MicrodeviceUpdate(SpecificGroupRequiredMixin, UpdateView):
    """Allows Devices to be updated"""
    model = Microdevice
    template_name = 'microdevices/microdevice_add.html'
    form_class = MicrodeviceForm

    required_group_name = 'Change Microdevices Front'

    def get_context_data(self, **kwargs):
        context = super(MicrodeviceUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            if 'reference_formset' not in context:
                context['reference_formset'] = MicrodeviceReferenceFormSetFactory(self.request.POST, instance=self.object)
        else:
            context['reference_formset'] = MicrodeviceReferenceFormSetFactory(instance=self.object)

        context['reference_queryset'] = AssayReference.objects.all()
        context['update'] = True

        return context

    def form_valid(self, form):
        reference_formset = MicrodeviceReferenceFormSetFactory(
            self.request.POST,
            instance=self.object
        )
        if form.is_valid() and reference_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[reference_formset], update=True)
            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, reference_formset=reference_formset))


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
                context['location_formset'] = OrganModelLocationFormsetFactory(self.request.POST)
                context['cell_formset'] = OrganModelCellFormsetFactory(self.request.POST)
                context['reference_formset'] = OrganModelReferenceFormSetFactory(self.request.POST)

            else:
                context['protocol_formset'] = OrganModelProtocolFormsetFactory()
                context['location_formset'] = OrganModelLocationFormsetFactory()
                context['cell_formset'] = OrganModelCellFormsetFactory()
                context['reference_formset'] = OrganModelReferenceFormSetFactory()

        context['reference_queryset'] = AssayReference.objects.all()

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
        reference_formset = OrganModelReferenceFormSetFactory(
            self.request.POST,
            instance=form.instance
        )
        cell_formset = OrganModelCellFormsetFactory(
            self.request.POST,
            instance=form.instance
        )

        if form.is_valid() and protocol_formset.is_valid() and location_formset.is_valid() and cell_formset.is_valid() and reference_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[protocol_formset, location_formset, cell_formset, reference_formset], update=False)

            # Update the base model to be self-referential if it is missing
            if not form.instance.base_model_id:
                form.instance.base_model_id = form.instance.id
                form.instance.save()

            # Redirect back to edit if protcol_formset has changed
            if protocol_formset.has_changed():
                return redirect('{}update/'.format(self.object.get_absolute_url()))

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                protocol_formset=protocol_formset,
                location_formset=location_formset,
                reference_formset=reference_formset,
                cell_formset=cell_formset,
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

        # Get a dic of groups
        groups_to_check = {}
        for current_group in self.object.center.groups.all():
            groups_to_check.update({
                current_group.id: True
            })

        if self.request.user.groups.all().count() == 0 or self.object.center and not any(
            current_group.id in groups_to_check for current_group in self.request.user.groups.all()
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
                context['reference_formset'] = OrganModelReferenceFormSetFactory(
                    self.request.POST,
                    instance=self.object
                )
                context['cell_formset'] = OrganModelCellFormsetFactory(
                    self.request.POST,
                    instance=self.object
                )
            else:
                context['protocol_formset'] = OrganModelProtocolFormsetFactory(instance=self.object)
                context['location_formset'] = OrganModelLocationFormsetFactory(instance=self.object)
                context['reference_formset'] = OrganModelReferenceFormSetFactory(instance=self.object)
                context['cell_formset'] = OrganModelCellFormsetFactory(instance=self.object)

        context['reference_queryset'] = AssayReference.objects.all()
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
        reference_formset = OrganModelReferenceFormSetFactory(
            self.request.POST,
            instance=form.instance
        )
        cell_formset = OrganModelCellFormsetFactory(
            self.request.POST,
            instance=form.instance
        )

        if form.is_valid() and protocol_formset.is_valid() and location_formset.is_valid() and cell_formset.is_valid() and reference_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[protocol_formset, location_formset, cell_formset, reference_formset], update=True)

            # Update the base model to be self-referential if it is missing
            if not form.instance.base_model_id:
                form.instance.base_model_id = form.instance.id
                form.instance.save()

            # Redirect back to edit if protcol_formset has changed
            if protocol_formset.has_changed():
                return redirect('{}update/'.format(self.object.get_absolute_url()))

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                protocol_formset=protocol_formset,
                location_formset=location_formset,
                reference_formset=reference_formset,
                cell_formset=cell_formset,
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


class OrganModelProtocolUpdate(UpdateView):
    """Allows Organ Models to be updated"""
    model = OrganModelProtocol
    template_name = 'microdevices/organmodelprotocol_add.html'
    form_class = OrganModelProtocolForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        """Special dispatch for Organ Model Protocol

        Rejects users with no groups and then rejects users without groups matching the center
        (if there is a center listed)
        """
        self.object = self.get_object()
        if self.request.user.groups.all().count() == 0 or self.object.organ_model.center and not any(
            i in self.object.organ_model.center.groups.all() for i in self.request.user.groups.all()
        ):
            return PermissionDenied(self.request, 'You must be a member of the center ' + str(self.object.center))
        return super(OrganModelProtocolUpdate, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrganModelProtocolUpdate, self).get_context_data(**kwargs)

        # Cellsamples will always be the same
        context['cellsamples'] = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        if 'cell_formset' not in context:
            if self.request.POST:
                context['cell_formset'] = OrganModelProtocolCellFormsetFactory(
                    self.request.POST,
                    instance=self.object
                )
                context['setting_formset'] = OrganModelProtocolSettingFormsetFactory(
                    self.request.POST,
                    instance=self.object
                )
            else:
                context['cell_formset'] = OrganModelProtocolCellFormsetFactory(instance=self.object)
                context['setting_formset'] = OrganModelProtocolSettingFormsetFactory(instance=self.object)

        context['update'] = True

        return context

    def form_valid(self, form):
        cell_formset = OrganModelProtocolCellFormsetFactory(
            self.request.POST,
            instance=form.instance
        )
        setting_formset = OrganModelProtocolSettingFormsetFactory(
            self.request.POST,
            instance=form.instance
        )
        if form.is_valid() and cell_formset.is_valid() and setting_formset.is_valid():
            save_forms_with_tracking(self, form, formset=[cell_formset, setting_formset], update=True)

            return redirect(self.object.get_post_submission_url())
        else:
            return self.render_to_response(self.get_context_data(
                form=form,
                cell_formset=cell_formset,
                setting_formset=setting_formset
            ))
