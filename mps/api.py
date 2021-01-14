from rest_framework import routers, serializers, viewsets
# Lazy
from assays.models import(
    AssayStudy,
    AssayDataPoint,
    AssayMatrixItem,
    AssayGroup,
    AssayGroupCompound,
    AssayGroupCell,
    AssayGroupSetting,
    AssayStudyAssay,
    AssaySampleLocation,
    AssayTarget,
    AssayMethod,
    PhysicalUnits
)
from django.contrib.auth.models import Group
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import ListSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SkipField
from rest_framework.settings import api_settings

# Via https://github.com/claytondaley/drf-keyed-list
class KeyedListSerializer(ListSerializer):
    default_error_messages = {
        'not_a_dict': _('Expected a dict of items but got type "{input_type}".'),
        'empty': _('This dict may not be empty.')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meta = getattr(self.child, 'Meta', None)
        assert hasattr(meta, 'keyed_list_serializer_field'), \
            "Must provide a field name at keyed_list_serializer_field when using KeyedListSerializer"
        self._keyed_field = meta.keyed_list_serializer_field

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            message = self.error_messages['not_a_dict'].format(
                input_type=type(data).__name__
            )
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='not_a_dict')
        if not self.allow_empty and len(data) == 0:
            if self.parent and self.partial:
                raise SkipField()

            message = self.error_messages['empty']
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='empty')
        data = [{**v, **{self._keyed_field: k}} for k, v in data.items()]
        return super().to_internal_value(data)

    def to_representation(self, data):
        response = super().to_representation(data)
        return {v.pop(self._keyed_field): v for v in response}


# Maybe we ought to have serializers in a different file?
class AssayDataPointSerializer(serializers.ModelSerializer):
    # An exception is thrown when repeating the source... for some reason?
    # If it defaults to the attribute name, why complain about passing source extraneously?
    sample_location = serializers.StringRelatedField()
    # Alias
    assay_id = serializers.StringRelatedField(source='study_assay_id', read_only=True)

    item_id = serializers.StringRelatedField(source='matrix_item_id', read_only=True)

    time = serializers.StringRelatedField(source='get_time_string')
    time_in_minutes = serializers.IntegerField(source='time')

    class Meta:
        model = AssayDataPoint
        fields = [
            'item_id',
            'assay_id',
            'sample_location',
            'value',
            'cross_reference',
            'time',
            'time_in_minutes',
            'notes',
            'assay_plate_id',
            'assay_well_id',
            'replicate',
            'excluded',
            'replaced',
            'update_number',
        ]


# Where things get a bit messy
# Unfortunately will need quite a few serializers
class AssayGroupCompoundSerializer(serializers.ModelSerializer):
    compound = serializers.StringRelatedField(source='compound_instance')
    concentration_unit = serializers.StringRelatedField()

    addition_location = serializers.StringRelatedField()

    addition_time = serializers.StringRelatedField(source='get_addition_time_string')
    duration = serializers.StringRelatedField(source='get_duration_string')

    addition_time_in_minutes = serializers.IntegerField(source='addition_time')
    duration_in_minutes = serializers.IntegerField(source='duration')

    class Meta:
        model = AssayGroupCompound
        fields = [
            'compound',
            'concentration',
            'concentration_unit',
            'addition_time',
            'addition_time_in_minutes',
            'duration',
            'duration_in_minutes',
            'addition_location',
        ]


class AssayGroupCellSerializer(serializers.ModelSerializer):
    # Unless we, you know, want this as another layer
    cell_sample = serializers.StringRelatedField()
    biosensor = serializers.StringRelatedField()
    density_unit = serializers.StringRelatedField()

    addition_location = serializers.StringRelatedField()

    addition_time = serializers.StringRelatedField(source='get_addition_time_string')

    addition_time_in_minutes = serializers.IntegerField(source='addition_time')

    class Meta:
        model = AssayGroupCell
        fields = [
            'cell_sample',
            'biosensor',
            'density',
            'density_unit',
            'passage',
            'addition_time',
            'addition_time_in_minutes',
            'addition_location',
        ]


class AssayGroupSettingSerializer(serializers.ModelSerializer):
    setting = serializers.StringRelatedField()
    unit = serializers.StringRelatedField()

    addition_location = serializers.StringRelatedField()

    addition_time = serializers.StringRelatedField(source='get_addition_time_string')
    duration = serializers.StringRelatedField(source='get_duration_string')

    addition_time_in_minutes = serializers.IntegerField(source='addition_time')
    duration_in_minutes = serializers.IntegerField(source='duration')

    class Meta:
        model = AssayGroupSetting
        fields = [
            'setting',
            'value',
            'unit',
            'addition_time',
            'addition_time_in_minutes',
            'duration',
            'duration_in_minutes',
            'addition_location',
        ]


class AssayGroupSerializer(serializers.ModelSerializer):
    # Aliases
    mps_model = serializers.StringRelatedField(source='organ_model')
    mps_model_version = serializers.StringRelatedField(source='organ_model_protocol')

    # Backwards relations
    compounds = AssayGroupCompoundSerializer(source='assaygroupcompound_set', read_only=True, many=True)
    cells = AssayGroupCellSerializer(source='assaygroupcell_set', read_only=True, many=True)
    settings = AssayGroupSettingSerializer(source='assaygroupsetting_set', read_only=True, many=True)

    class Meta:
        model = AssayGroup
        fields = [
            # Need the id for matching
            # It will be part of the representation
            'id',
            'name',
            'mps_model',
            'mps_model_version',
            'compounds',
            'cells',
            'settings',
        ]

        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'id'


class AssayStudyAssaySerializer(serializers.ModelSerializer):
    target = serializers.StringRelatedField()
    method = serializers.StringRelatedField()
    unit = serializers.StringRelatedField()

    class Meta:
        model = AssayStudyAssay
        fields = [
            # Need the id for matching
            'id',
            'target',
            'method',
            'unit',
        ]

        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'id'


class AssayMatrixItemSerializer(serializers.ModelSerializer):
    # Force string ID
    group_id = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AssayMatrixItem
        fields = [
            # Need the id for matching
            'id',
            'group_id',
            'name',
            # Setup date generally is the same as study's...
            # Error on the side of more?
            'scientist',
            'notebook',
            'notebook_page',
            'notes',
        ]

        list_serializer_class = KeyedListSerializer
        keyed_list_serializer_field = 'id'


# Want a fast url
class AssayStudySerializer(serializers.HyperlinkedModelSerializer):
    # Force string ID
    id = serializers.StringRelatedField(read_only=True)

    study_types = serializers.StringRelatedField(source='get_study_types_string')
    data_group = serializers.StringRelatedField(source='group')

    class Meta:
        model = AssayStudy
        fields = [
            'id',
            'url',
            'name',
            'data_group',
            'study_types',
            'start_date',
            'description',
        ]


class AssayStudyDataSerializer(serializers.ModelSerializer):
    # Force string ID
    id = serializers.StringRelatedField(read_only=True)

    study_types = serializers.StringRelatedField(source='get_study_types_string')
    data_group = serializers.StringRelatedField(source='group')

    data = AssayDataPointSerializer(source='assaydatapoint_set', read_only=True, many=True)
    groups = AssayGroupSerializer(source='assaygroup_set', read_only=True, many=True)
    assays = AssayStudyAssaySerializer(source='assaystudyassay_set', read_only=True, many=True)
    # Are we sticking with this nomenclature?
    items = AssayMatrixItemSerializer(source='assaymatrixitem_set', read_only=True, many=True)

    class Meta:
        model = AssayStudy
        depth = 1
        fields = [
            # Redundant, but for clarity
            'id',
            # Study fields
            # Stringification gives study types etc.
            # Do we want the stringification or split up?
            # '__str__',
            'name',
            'data_group',
            'study_types',
            'start_date',
            'description',
            'groups',
            'items',
            'assays',
            'data',
        ]


# ViewSets define the view behavior.

# Mixin for differentiating list and detail
class DetailSerializerMixin(object):
    def get_serializer_class(self):
        if self.action == 'retrieve':
            if hasattr(self, 'detail_serializer_class'):
                return self.detail_serializer_class

        return super(DetailSerializerMixin, self).get_serializer_class()


# Maybe we ought to have ViewSets in a different file?
class AssayStudyViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    # Contrived
    queryset = AssayStudy.objects.filter(
        restricted=False,
    ).exclude(
        signed_off_by__isnull=True,
    )

    http_method_names = ['get']

    # WE CANNOT USE THE SAME QUERYSET FOR BOTH
    # We also need to use different serializers
    def list(self, request):
        queryset = AssayStudy.objects.filter(
            restricted=False,
        ).exclude(
            signed_off_by__isnull=True,
        )
        # NOTICE CONTEXT FOR HOST
        serializer = AssayStudySerializer(
            queryset,
            many=True,
            context={'request': request}
        )

        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        # Only public data
        queryset = AssayStudy.objects.filter(
            restricted=False,
        ).exclude(
            signed_off_by__isnull=True,
        ).prefetch_related(
            # Subject to change!
            'assaygroup_set__assaygroupcompound_set__compound_instance__compound',
            'assaygroup_set__assaygroupcompound_set__compound_instance__supplier',
            'assaygroup_set__assaygroupcompound_set__concentration_unit',
            'assaygroup_set__assaygroupcompound_set__addition_location',
            'assaygroup_set__assaygroupcell_set__cell_sample__cell_type__organ',
            'assaygroup_set__assaygroupcell_set__cell_sample__cell_subtype',
            'assaygroup_set__assaygroupcell_set__cell_sample__supplier',
            'assaygroup_set__assaygroupcell_set__addition_location',
            'assaygroup_set__assaygroupcell_set__density_unit',
            'assaygroup_set__assaygroupcell_set__biosensor',
            'assaygroup_set__assaygroupsetting_set__setting',
            'assaygroup_set__assaygroupsetting_set__unit',
            'assaygroup_set__assaygroupsetting_set__addition_location',
            'assaygroup_set__organ_model__device',
            'assaystudyassay_set__target',
            'assaystudyassay_set__method',
            'assaystudyassay_set__unit',
            'assaydatapoint_set__sample_location',
            'assaydatapoint_set__subtarget'
        )
        study = get_object_or_404(queryset, pk=pk)
        serializer = AssayStudyDataSerializer(study)

        return Response(serializer.data)

# Routers provide an easy way of automatically determining the URL conf.
# Be sure to import this into mps.urls
api_router = routers.DefaultRouter()
api_router.register(r'api/studies', AssayStudyViewSet)


# COMPONENTS
class AssayTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssayTarget
        fields = [
            'id',
            'name',
            'short_name',
            'description',
        ]


class AssayTargetViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AssayTarget.objects.all()
    serializer_class = AssayTargetSerializer

    http_method_names = ['get']

api_router.register(r'api/targets', AssayTargetViewSet)


class AssayMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssayMethod
        fields = [
            'id',
            'name',
            'description',
        ]


class AssayMethodViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AssayMethod.objects.all()
    serializer_class = AssayMethodSerializer

    http_method_names = ['get']

api_router.register(r'api/methods', AssayMethodViewSet)


class AssaySampleLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssaySampleLocation
        fields = [
            'id',
            'name',
            'description',
        ]


class AssaySampleLocationViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AssaySampleLocation.objects.all()
    serializer_class = AssaySampleLocationSerializer

    http_method_names = ['get']

api_router.register(r'api/locations', AssaySampleLocationViewSet)


# NOTICE BREAK FROM CONVENTION
class PhysicalUnitsSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(source='unit')
    unit_type = serializers.StringRelatedField()

    class Meta:
        model = PhysicalUnits
        fields = [
            'id',
            'name',
            'unit_type',
            'description',
        ]


class PhysicalUnitsViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PhysicalUnits.objects.all()
    serializer_class = PhysicalUnitsSerializer

    http_method_names = ['get']

api_router.register(r'api/units', PhysicalUnitsViewSet)
