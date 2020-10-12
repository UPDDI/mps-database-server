from rest_framework import routers, serializers, viewsets
# Lazy
from assays.models import *
from django.contrib.auth.models import Group
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


# Mixin for differentiating list and detail
class DetailSerializerMixin(object):
    def get_serializer_class(self):
        if self.action == 'retrieve':
            if hasattr(self, 'detail_serializer_class'):
                return self.detail_serializer_class

        return super(DetailSerializerMixin, self).get_serializer_class()


# Serializers define the API representation.
# Maybe we ought to have serializers in a different file?
# Unfortunately, we more or less have to manually indicate what we want from every constituent component
class AssayStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssayStudy
        fields = ['id', 'name']


class AssayDataPointSerializer(serializers.ModelSerializer):
    # An exception is thrown when repeating the source... for some reason?
    # If it defaults to the attribute name, why complain about passing source extraneously?
    sample_location = serializers.StringRelatedField()
    # Alias
    assay_id = serializers.PrimaryKeyRelatedField(source='study_assay', read_only=True)

    item_id = serializers.PrimaryKeyRelatedField(source='matrix_item', read_only=True)

    time = serializers.StringRelatedField(source='get_time_string')

    class Meta:
        model = AssayDataPoint
        fields = [
            'item_id',
            'assay_id',
            'sample_location',
            'value',
            'cross_reference',
            'time',
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

    addition_time = serializers.StringRelatedField(source='get_addition_time')
    duration = serializers.StringRelatedField(source='get_duration')

    class Meta:
        model = AssayGroupCompound
        fields = [
            'compound',
            'concentration',
            'concentration_unit',
            'addition_time',
            'duration',
            'addition_location',
        ]


class AssayGroupCellSerializer(serializers.ModelSerializer):
    # Unless we, you know, want this as another layer
    cell_sample = serializers.StringRelatedField()
    biosensor = serializers.StringRelatedField()
    density_unit = serializers.StringRelatedField()

    addition_location = serializers.StringRelatedField()

    addition_time = serializers.StringRelatedField(source='get_addition_time')

    class Meta:
        model = AssayGroupCell
        fields = [
            'cell_sample',
            'biosensor',
            'density',
            'density_unit',
            'passage',
            'addition_time',
            'addition_location',
        ]


class AssayGroupSettingSerializer(serializers.ModelSerializer):
    setting = serializers.StringRelatedField()
    unit = serializers.StringRelatedField()

    addition_location = serializers.StringRelatedField()

    addition_time = serializers.StringRelatedField(source='get_addition_time')
    duration = serializers.StringRelatedField(source='get_duration')

    class Meta:
        model = AssayGroupSetting
        fields = [
            'setting',
            'value',
            'unit',
            'addition_time',
            'duration',
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
            'id',
            'mps_model',
            'mps_model_version',
            'compounds',
            'cells',
            'settings',
        ]


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


class AssayMatrixItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssayMatrixItem
        fields = [
            # Need the id for matching
            'id',
            'group_id',
            'name',
        ]



class AssayStudyDataSerializer(serializers.ModelSerializer):
    data = AssayDataPointSerializer(source='assaydatapoint_set', read_only=True, many=True)
    groups = AssayGroupSerializer(source='assaygroup_set', read_only=True, many=True)
    assays = AssayStudyAssaySerializer(source='assaystudyassay_set', read_only=True, many=True)
    # I don't know
    chips_and_wells = AssayMatrixItemSerializer(source='assaymatrixitem_set', read_only=True, many=True)

    class Meta:
        model = AssayStudy
        depth = 1
        fields = [
            'id',
            'data',
            'groups',
            'assays',
            'chips_and_wells',
        ]


# ViewSets define the view behavior.
# Maybe we ought to have ViewSets in a different file?
class AssayStudyViewSet(DetailSerializerMixin, viewsets.ModelViewSet):
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
        serializer = AssayStudySerializer(queryset, many=True)

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
