"""
    This script tallies the intrastudy reproducibility counts for all
    studies that have been signed off on, and saves a vbar delimited string of
    these totals to the studies' models in the "repro_nums" field.
"""
from assays.models import AssayStudy, AssayMatrixItem, AssayDataPoint, tuple_attrgetter
from assays.utils import get_repro_data
from assays.ajax import get_data_as_list_of_lists, get_item_groups
def run():
    """Main function that runs the script"""
    study_list = AssayStudy.objects.filter(
        repro_nums='',
        # ONLY INCLUDE UN-ARCHIVED
        archived=False
    ).exclude(
        signed_off_by_id=None
    )

    data = {}

    # print(study_list)

    # If chip data
    for study in study_list:
        matrix_items = AssayMatrixItem.objects.filter(
            study_id=study.id
        )

        data_points = AssayDataPoint.objects.filter(
            study_id=study.id
        ).prefetch_related(
        # TODO optimize prefetch!
            'study__group',
            'study_assay__target',
            'study_assay__method',
            'study_assay__unit__base_unit',
            'sample_location',
            'matrix_item__matrix',
            'matrix_item__organ_model',
            'subtarget'
        ).filter(
            replaced=False,
            excluded=False,
            value__isnull=False
        )

        criteria = {
            'cell': [
                'cell_sample.cell_type_id',
                'addition_location_id'
            ],
            'compound': [
                'compound_instance.compound_id',
                'concentration',
                'concentration_unit_id',
                'addition_location_id'
            ],
            'special': [
                'sample_location'
            ]
        }

        treatment_group_representatives, setup_to_treatment_group, treatment_header_keys = get_item_groups(
            None,
            criteria,
            matrix_items
        )

        repro_data = []

        base_tuple = (
            'study_assay.target_id',
            # 'study_assay.method_id',
            'study_assay.unit.base_unit_id',
            'sample_location_id'
        )

        current_tuple = (
            'study_assay.target_id',
            # 'study_assay.method_id',
            'study_assay.unit_id',
            'sample_location_id'
        )

        data_point_treatment_groups = {}
        treatment_group_table = {}

        # ASSUME _id termination
        base_value_tuple = tuple([x.replace('_id', '') for x in base_tuple])
        current_value_tuple = tuple([x.replace('_id', '') for x in current_tuple])

        # TODO TODO TODO TODO
        data_point_attribute_getter_base = tuple_attrgetter(*base_tuple)
        data_point_attribute_getter_current = tuple_attrgetter(*current_tuple)

        data_point_attribute_getter_base_values = tuple_attrgetter(*base_value_tuple)
        data_point_attribute_getter_current_values = tuple_attrgetter(*current_value_tuple)

        for point in data_points:
            point.standard_value = point.value
            item_id = point.matrix_item_id
            if point.study_assay.unit.base_unit_id:
                data_point_tuple = data_point_attribute_getter_base(point)
                point.standard_value *= point.study_assay.unit.scale_factor
            else:
                data_point_tuple = data_point_attribute_getter_current(point)
            current_group = data_point_treatment_groups.setdefault(
                (
                    data_point_tuple,
                    # setup_to_treatment_group.get(item_id).get('id')
                    setup_to_treatment_group.get(item_id).get('index')
                ),
                # 'Group {}'.format(len(data_point_treatment_groups) + 1)
                '{}'.format(len(data_point_treatment_groups) + 1)
            )
            point.data_group = current_group
            if current_group not in treatment_group_table:
                if point.study_assay.unit.base_unit_id:
                    treatment_group_table.update({
                        current_group: [str(x) for x in list(
                            data_point_attribute_getter_base_values(point)
                        ) + [setup_to_treatment_group.get(item_id).get('index')]]
                    })
                else:
                    treatment_group_table.update({
                        current_group: [str(x) for x in list(
                            data_point_attribute_getter_current_values(point)
                        ) + [setup_to_treatment_group.get(item_id).get('index')]]
                    })

        repro_data.append([
            'Study ID',
            'Chip ID',
            'Time',
            'Value',
            # NAME THIS SOMETHING ELSE
            'Treatment Group'
        ])

        for point in data_points:
            repro_data.append([
                point.study.name,
                point.matrix_item.name,
                point.time,
                point.standard_value,
                point.data_group
            ])

        # TODO REVISE
        intra_data_table = get_repro_data(
            len(treatment_group_table),
            repro_data
        )

        gas_list = intra_data_table['reproducibility_results_table']['data']
        # ODD
        data['gas_list'] = gas_list

        excellentCounter = acceptableCounter = poorCounter = 0

        for x in range(0, len(data['gas_list'])):
            if data['gas_list'][x][7][0] == 'E':
                excellentCounter += 1
            elif data['gas_list'][x][7][0] == 'A':
                acceptableCounter += 1
            elif data['gas_list'][x][7][0] == 'P':
                poorCounter += 1

        study.repro_nums = "{}|{}|{}".format(excellentCounter, acceptableCounter, poorCounter)
        study.save()
