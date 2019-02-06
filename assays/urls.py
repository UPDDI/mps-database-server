from django.conf.urls import url
from assays.views import (
    AssayStudyEditableList,
    AssayStudyIndex,
    AssayStudyUpdate,
    AssayStudyDelete,
    AssayStudySummary,
    AssayStudyData,
    AssayStudyDataUpload,
    AssayStudyList,
    AssayStudyAdd,
    AssayMatrixItemDetail,
    AssayMatrixItemUpdate,
    AssayMatrixItemDelete,
    AssayStudyConfigurationList,
    AssayStudyConfigurationAdd,
    AssayStudyConfigurationUpdate,
    AssayMatrixAdd,
    AssayMatrixDetail,
    AssayMatrixUpdate,
    AssayMatrixDelete,
    AssayStudySignOff,
    AssayStudyReproducibility,
    AssayStudyImages,
    AssayTargetList,
    AssayTargetDetail,
    AssayMethodList,
    AssayMethodDetail,
    AssayPhysicalUnitsList,
    AssaySampleLocationList,
    GraphingReproducibilityFilterView,
    AssayDataFromFilters,
    AssayReferenceList
)
import assays.ajax

urlpatterns = [
    # User can view their studies
    # url(r'^assays/user_index/$', UserIndex.as_view(), name='user_index'),
    # User can view all Editable Studies
    # url(r'^assays/editable_studies/$', GroupIndex.as_view(), name='editable_studies'),
    url(r'^assays/assaystudy/editable_studies/$', AssayStudyEditableList.as_view(), name='editable_study_list'),
    # The main page for a study
    # url(r'^assays/(?P<pk>[0-9]+)/$', StudyIndex.as_view(), name='study_index'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/$', AssayStudyIndex.as_view(), name='assay_study_index'),
    # Update page for studies
    # url(r'^assays/(?P<pk>[0-9]+)/update/$', AssayRunUpdate.as_view(), name='study-update'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/update/$', AssayStudyUpdate.as_view(), name='assay_study_update'),
    # Delete view for studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/delete/$', AssayStudyDelete.as_view(), name='study-delete'),
    # Summary view for studies
    # url(r'^assays/(?P<pk>[0-9]+)/summary/$', AssayRunSummary.as_view(), name='study-summary'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/summary/$', AssayStudySummary.as_view(), name='assay_study_summary'),
    # # All data for a study
    # url(r'^assays/(?P<pk>[0-9]+)/data/$', ReturnStudyData.as_view(), name='study-data'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/data/$', AssayStudyData.as_view(), name='assay_study_data'),
    # # Bulk Readout Upload for Studies
    # url(r'^assays/(?P<pk>[0-9]+)/bulk/$', ReadoutBulkUpload.as_view(), name='readout-bulk-upload'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/upload/$', AssayStudyDataUpload.as_view(), name='assay_study_upload'),

    # NEW_TO_BE_REVISED
    url(r'^assays/assaystudy/$', AssayStudyList.as_view(), name='assay_study_list'),
    url(r'^assays/assaystudy/add/$', AssayStudyAdd.as_view(), name='assay_study_add'),

    url(r'^assays/assaymatrixitem/(?P<pk>[0-9]+)/$', AssayMatrixItemDetail.as_view(), name='assay_matrix_item_detail'),
    url(r'^assays/assaymatrixitem/(?P<pk>[0-9]+)/update/$', AssayMatrixItemUpdate.as_view(), name='assay_matrix_item_update'),
    url(r'^assays/assaymatrixitem/(?P<pk>[0-9]+)/delete/$', AssayMatrixItemDelete.as_view(), name='assay_matrix_item_delete'),

    url(r'^assays/studyconfiguration/$', AssayStudyConfigurationList.as_view(), name='studyconfiguration_list'),
    url(r'^assays/studyconfiguration/add/$', AssayStudyConfigurationAdd.as_view(), name='studyconfiguration_add'),
    url(r'^assays/studyconfiguration/(?P<pk>[0-9]+)/$', AssayStudyConfigurationUpdate.as_view(), name='studyconfiguration_update'),

    # Add a matrix
    url(r'^assays/assaystudy/(?P<study_id>[0-9]+)/assaymatrix/add/$', AssayMatrixAdd.as_view(), name='assay_matrix_add'),
    url(r'^assays/assaymatrix/(?P<pk>[0-9]+)/$', AssayMatrixDetail.as_view(), name='assay_matrix_detail'),
    url(r'^assays/assaymatrix/(?P<pk>[0-9]+)/update/$', AssayMatrixUpdate.as_view(), name='assay_matrix_update'),
    url(r'^assays/assaymatrix/(?P<pk>[0-9]+)/delete/$', AssayMatrixDelete.as_view(), name='assay_matrix_delete'),

    # Sign off
    # url(r'^assays/(?P<pk>[0-9]+)/sign_off/$', AssayRunSignOff.as_view(), name='study-sign_off'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/sign_off/$', AssayStudySignOff.as_view(), name='assay_study_sign_off'),
    # # Change pages for respective models
    # url(r'^assays/assaychipsetup/(?P<pk>[0-9]+)/update/$', AssayChipSetupUpdate.as_view(), name='setup_update'),
    # url(r'^assays/assaychipreadout/(?P<pk>[0-9]+)/update/$', AssayChipReadoutUpdate.as_view(), name='readout_update'),
    # url(r'^assays/assaychiptestresult/(?P<pk>[0-9]+)/update/$', AssayChipTestResultUpdate.as_view(), name='result_update'),

    # # Add pages for respective models
    # url(r'^assays/(?P<study_id>[0-9]+)/assaychipsetup/add/$', AssayChipSetupAdd.as_view(), name='setup_add'),
    # url(r'^assays/(?P<study_id>[0-9]+)/assaychipreadout/add/$', AssayChipReadoutAdd.as_view(), name='readout_add'),
    # url(r'^assays/(?P<study_id>[0-9]+)/assaychiptestresult/add/$', AssayChipTestResultAdd.as_view(), name='result_add'),

    # # Delete pages for respective models
    # url(r'^assays/assaychipsetup/(?P<pk>[0-9]+)/delete/$', AssayChipSetupDelete.as_view(), name='setup_delete'),
    # url(r'^assays/assaychipreadout/(?P<pk>[0-9]+)/delete/$', AssayChipReadoutDelete.as_view(), name='readout_delete'),
    # url(r'^assays/assaychiptestresult/(?P<pk>[0-9]+)/delete/$', AssayChipTestResultDelete.as_view(), name='result_delete'),

    url(r'^assays/studyconfiguration/$', AssayStudyConfigurationList.as_view(), name='studyconfiguration_list'),
    url(r'^assays/studyconfiguration/add/$', AssayStudyConfigurationAdd.as_view(), name='studyconfiguration_add'),
    url(r'^assays/studyconfiguration/(?P<pk>[0-9]+)/$', AssayStudyConfigurationUpdate.as_view(), name='studyconfiguration_update'),

    # url(r'^assays/study/$', AssayRunList.as_view(), name='study_list'),
    # url(r'^assays/study/add/$', AssayRunAdd.as_view(), name='study_add'),

    # DEPRECATED >>
    # url(r'^assays/assaychipsetup/$', AssayChipSetupList.as_view(), name='setup_list'),
    # url(r'^assays/assaychipsetup/(?P<pk>[0-9]+)/$', AssayChipSetupDetail.as_view(), name='setup_detail'),
    #
    # url(r'^assays/assaychipreadout/$', AssayChipReadoutList.as_view(), name='readout_list'),
    # url(r'^assays/assaychipreadout/(?P<pk>[0-9]+)/$', AssayChipReadoutDetail.as_view(), name='readout_detail'),
    #
    # url(r'^assays/assaychiptestresult/$', AssayChipTestResultList.as_view(), name='result_list'),
    # url(r'^assays/assaychiptestresult/(?P<pk>[0-9]+)/$', AssayChipTestResultDetail.as_view(), name='result_detail'),
    #
    # # Reproducibility
    # url(r'^assays/reproducibility/$', AssayRunReproducibilityList.as_view(), name='run_reproducibility_list'),
    # url(r'^assays/(?P<pk>[0-9]+)/reproducibility/$', AssayRunReproducibility.as_view(), name='run-reproducibility'),

    # Deprecated
    # url(r'^assays/assaystudy/reproducibility/$', AssayStudyReproducibilityList.as_view(), name='assay_study_reproducibility_list'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/reproducibility/$', AssayStudyReproducibility.as_view(), name='assay_study_reproducibility'),

    # Images
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/images/$', AssayStudyImages.as_view(), name='study-images'),

    # Targets and Methods
    url(r'^assays/targets/$', AssayTargetList.as_view(), name='assay-targets-list'),
    url(r'^assays/targets/(?P<pk>[0-9]+)/$', AssayTargetDetail.as_view(), name='assay-targets-detail'),
    url(r'^assays/methods/$', AssayMethodList.as_view(), name='assay-methods-list'),
    url(r'^assays/methods/(?P<pk>[0-9]+)/$', AssayMethodDetail.as_view(), name='assay-methods-detail'),

    # Units
    url(r'^assays/units/$', AssayPhysicalUnitsList.as_view(), name='assay-units-list'),

    # Sample Locations
    url(r'^assays/locations/$', AssaySampleLocationList.as_view(), name='assay-locations-list'),

    # Location for test filter, for now
    url(r'^assays/graphing_reproducibility/$', GraphingReproducibilityFilterView.as_view(), name='graphing-reproducibility'),

    # Data from filters
    url(r'^assays/data_from_filters/$', AssayDataFromFilters.as_view(), name='data-from-filters'),

    # References
    url(r'^assays/references/$', AssayReferenceList.as_view(), name='assay-reference-list'),

    # Ajax
    url(r'^assays_ajax/$', assays.ajax.ajax),
]
