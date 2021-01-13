from django.views.generic import CreateView, UpdateView
from django.shortcuts import redirect
from django import forms

# Really it probably would have been better to have just used namespaces
from .forms import (
    MicrodeviceForm,
    OrganModelForm,
    OrganModelProtocolFormsetFactory,
    OrganModelLocationFormsetFactory,
    OrganModelProtocolForm,
    OrganModelCellFormsetFactory,
    OrganModelProtocolCellFormsetFactory,
    OrganModelProtocolSettingFormsetFactory,
    OrganModelReferenceFormSetFactory,
    MicrodeviceReferenceFormSetFactory,
    ManufacturerForm
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
    Manufacturer
)

from cellsamples.models import CellSample

from mps.mixins import (
    SpecificGroupRequiredMixin,
    PermissionDenied,
    user_is_active,
    FormHandlerMixin,
    OneGroupRequiredMixin,
    CreatorOrSuperuserRequiredMixin,
    ListHandlerView,
    DetailHandlerView,
    CreatorAndNotInUseMixin
)
from mps.base.models import save_forms_with_tracking
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from assays.models import AssayReference

from mps.templatetags.custom_filters import (
    ADMIN_SUFFIX,
    VIEWER_SUFFIX,
)

class MicrodeviceMixin(FormHandlerMixin):
    model = Microdevice
    template_name = 'microdevices/microdevice_add.html'
    form_class = MicrodeviceForm

    # FormHandler content
    formsets = (
        ('reference_formset', MicrodeviceReferenceFormSetFactory),
    )

    # TODO: WILL BE SCRAPPED IN FAVOR OF AJAX
    def get_context_data(self, **kwargs):
        context = super(MicrodeviceMixin, self).get_context_data(**kwargs)

        context.update({
            'reference_queryset': AssayReference.objects.all()
        })

        return context

class MicrodeviceAdd(OneGroupRequiredMixin, MicrodeviceMixin, CreateView):
    # required_group_name = 'Add Microdevices Front'
    pass


# Exception
class MicrodeviceUpdate(CreatorOrSuperuserRequiredMixin, MicrodeviceMixin, UpdateView):
    # required_group_name = 'Change Microdevices Front'
    pass


class MicrodeviceList(ListHandlerView):
    """Displays list of Microdevices"""
    model = Microdevice
    template_name = 'microdevices/microdevice_list.html'

    def get_queryset(self):
        return Microdevice.objects.prefetch_related('organ', 'center', 'manufacturer').all()


class MicrodeviceDetail(DetailHandlerView):
    """Displays details for a Device"""
    model = Microdevice
    template_name = 'microdevices/microdevice_detail.html'


class OrganModelMixin(FormHandlerMixin):
    model = OrganModel
    template_name = 'microdevices/organmodel_add.html'
    form_class = OrganModelForm

    # FormHandler content
    formsets = (
        ('protocol_formset', OrganModelProtocolFormsetFactory),
        ('location_formset', OrganModelLocationFormsetFactory),
        ('cell_formset', OrganModelCellFormsetFactory),
        ('reference_formset', OrganModelReferenceFormSetFactory),
    )

    # TODO: WILL BE SCRAPPED IN FAVOR OF AJAX
    def get_context_data(self, **kwargs):
        context = super(OrganModelMixin, self).get_context_data(**kwargs)

        context.update({
            'reference_queryset': AssayReference.objects.all(),
            # Crude
            'cellsamples' : CellSample.objects.all().prefetch_related(
                'cell_type__organ',
                'supplier',
                'cell_subtype__cell_type'
            ),
        })

        return context

    def extra_form_processing(self, form):
        # Update the base model to be self-referential if it is missing
        protocol_formset = self.all_forms.get('protocol_formset')

        if not form.instance.base_model_id:
            form.instance.base_model_id = form.instance.id
            form.instance.save()

        if protocol_formset.has_changed():
            # CRUDE change tracking
            for protocol in protocol_formset:
                if protocol.has_changed() and not protocol.cleaned_data.get('DELETE', False):
                    protocol.instance.modified_by_id = self.request.user.id
                    protocol.instance.modified_on = form.instance.modified_on

                    if not protocol.instance.created_by_id:
                        protocol.instance.created_by_id = protocol.instance.modified_by_id
                        protocol.instance.created_on = protocol.instance.modified_on

                    protocol.save()

        # Kind of crazy, we make the form again
        # This time with a kwarg indicating that we want to save protocol stuff
        # Check if the series_data has changed (CRUDE)
        # TODO REVIEW REVIEW REVIEW
        if form.instance.get_group_data_string() != self.request.POST.get('series_data'):
            form_class = self.get_form_class()
            revised_form = form_class(self.request.POST, instance=form.instance, process_protocols=True)
            if revised_form.is_valid():
                revised_form.save()


class OrganModelAdd(OneGroupRequiredMixin, OrganModelMixin, CreateView):
    # required_group_name = 'Add Microdevices Front'
    pass


# PLEASE NOTE THE SPECIAL dispatch
class OrganModelUpdate(OrganModelMixin, UpdateView):
    @method_decorator(login_required)
    @method_decorator(user_passes_test(user_is_active))
    def dispatch(self, *args, **kwargs):
        """Special dispatch for Organ Model

        Rejects users with no groups and then rejects users without groups matching the center
        (if there is a center listed)
        """
        self.object = self.get_object()

        user_group_names = {
            user_group.name.replace(ADMIN_SUFFIX, ''): True for user_group in self.request.user.groups.all()
        }

        if not self.object.user_is_in_center(user_group_names):
            return PermissionDenied(self.request, 'You must be a member of the center ' + str(self.object.center))

        return super(OrganModelUpdate, self).dispatch(*args, **kwargs)


class OrganModelList(ListHandlerView):
    """Displays list of Organ Models"""
    model = OrganModel
    template_name = 'microdevices/organmodel_list.html'

    def get_queryset(self):
        queryset = OrganModel.objects.all().prefetch_related(
            'organ',
            'center',
            'device',
            'base_model',
            'organmodelprotocol_set',
            'center__groups'
        )

        user_group_names = {
            user_group.name.replace(ADMIN_SUFFIX, ''): True for user_group in self.request.user.groups.all()
        }

        for organ_model in queryset:
            organ_model.is_editable = organ_model.user_is_in_center(user_group_names)

        return queryset


class OrganModelDetail(DetailHandlerView):
    """Displays details for an Organ Model"""
    model = OrganModel
    template_name = 'microdevices/organmodel_detail.html'

    def get_context_data(self, **kwargs):
        context = super(OrganModelDetail, self).get_context_data(**kwargs)

        # Deprecated!
        # assays = ValidatedAssay.objects.filter(organ_model_id=self.object.id).prefetch_related('assay', 'assay__assay_type')

        # if self.object.center and any(i in self.object.center.groups.all() for i in self.request.user.groups.all()):
        #     protocols = OrganModelProtocol.objects.filter(
        #         organ_model_id=self.object.id
        #     ).order_by('-version')
        # else:
        #     protocols = None

        user_group_names = {
            user_group.name.replace(ADMIN_SUFFIX, ''): True for user_group in self.request.user.groups.all()
        }

        context.update({
            # 'assays': assays,
            # 'protocols': protocols,
            'protocol_access': self.object.user_is_in_center(user_group_names)
        })

        return context


class MicrophysiologyCenterDetail(DetailHandlerView):
    """Displays details for a Microphysiology Center"""
    model = MicrophysiologyCenter
    template_name = 'microdevices/microphysiologycenter_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MicrophysiologyCenterDetail, self).get_context_data(**kwargs)
        context['models'] = OrganModel.objects.filter(center_id=self.object.id).values_list('name', flat=True)
        context['pi_email_parts'] = self.object.pi_email.split("@")
        context['contact_email_parts'] = self.object.contact_email.split("@")

        return context


class MicrophysiologyCenterList(ListHandlerView):
    model = MicrophysiologyCenter
    template_name = 'microdevices/microphysiologycenter_list.html'


class OrganModelProtocolUpdate(FormHandlerMixin, UpdateView):
    """Allows Organ Model Protocols to be updated"""
    model = OrganModelProtocol
    template_name = 'microdevices/organmodelprotocol_add.html'
    form_class = OrganModelProtocolForm

    formsets = (
        ('cell_formset', OrganModelProtocolCellFormsetFactory),
        ('setting_formset', OrganModelProtocolSettingFormsetFactory),
    )

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
        current_cellsamples = CellSample.objects.all().prefetch_related(
            'cell_type__organ',
            'supplier',
            'cell_subtype__cell_type'
        )

        # TODO SLATED FOR REMOVAL
        context.update({
            'cellsamples': current_cellsamples
        })

        return context


class OrganModelProtocolDetail(DetailHandlerView):
    """Displays details for an Organ Model Protocol"""
    model = OrganModelProtocol
    template_name = 'microdevices/organmodelprotocol_detail.html'

    def get_context_data(self, **kwargs):
        context = super(OrganModelProtocolDetail, self).get_context_data(**kwargs)

        user_group_names = {
            user_group.name.replace(ADMIN_SUFFIX, ''): True for user_group in self.request.user.groups.all()
        }

        context.update({
            'protocol_access': self.object.organ_model.user_is_in_center(user_group_names)
        })

        return context


class ManufacturerMixin(FormHandlerMixin):
    model = Manufacturer
    form_class = ManufacturerForm


class ManufacturerAdd(OneGroupRequiredMixin, ManufacturerMixin, CreateView):
    pass


class ManufacturerUpdate(CreatorAndNotInUseMixin, ManufacturerMixin, UpdateView):
    pass


class ManufacturerDetail(DetailHandlerView):
    pass


class ManufacturerList(ListHandlerView):
    model = Manufacturer
