"""
    This script tallies the intrastudy reproducibility counts for all
    studies that have been signed off on, and saves a vbar delimited string of
    these totals to the studies' models in the "repro_nums" field.
"""
from assays.models import AssayStudy, AssayMatrixItem
from assays.utils import get_repro_data
from assays.ajax import get_data_as_list_of_lists
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

        chip_data = get_data_as_list_of_lists(matrix_items, include_header=True, include_all=False)

        repro_data = get_repro_data(chip_data)

        gas_list = repro_data['reproducibility_results_table']['data']
        data['gas_list'] = gas_list

        excellentCounter = acceptableCounter = poorCounter = 0

        for x in range(0, len(data['gas_list'])):
            if data['gas_list'][x][10][0] == 'E':
                excellentCounter += 1
            elif data['gas_list'][x][10][0] == 'A':
                acceptableCounter += 1
            elif data['gas_list'][x][10][0] == 'P':
                poorCounter += 1

        study.repro_nums = "{}|{}|{}".format(excellentCounter, acceptableCounter, poorCounter)
        study.save()
