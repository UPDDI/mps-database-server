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
    AssayStudyDetails,
    AssayStudyGroups,
    AssayStudyChips,
    AssayStudyChipsDetail,
    AssayStudyPlates,
    AssayStudyPlateAdd,
    AssayStudyPlateUpdate,
    AssayStudyPlateDetail,
    AssayStudyAssays,
    AssayStudyDataIndex,
    AssayStudyAccess,
    AssayGroupDetail,
    AssayDataFileUploadDetail,
    AssayDataFileUploadList,
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
    GraphingReproducibilityFilterView,
    AssayDataFromFilters,
    AssayInterStudyReproducibility,
    AssayStudyDataPlots,
    AssayStudyPowerAnalysisStudy,
    AssayDataFromFilters,
    AssayStudySetAdd,
    AssayStudySetUpdate,
    AssayStudySetDataPlots,
    AssayStudySetReproducibility,
    AssayStudySetList,
    AssayStudySetData,
    AssayReferenceList,
    AssayReferenceAdd,
    AssayReferenceUpdate,
    AssayReferenceDetail,
    AssayReferenceDelete,
    AssayStudyAddNew,
    AssayMatrixNew,
    AssayTargetAdd,
    AssayTargetList,
    AssayTargetDetail,
    AssayTargetUpdate,
    AssayTargetUpdateRestricted,
    AssayMethodAdd,
    AssayMethodList,
    AssayMethodDetail,
    AssayMethodUpdate,
    AssayMethodUpdateRestricted,
    PhysicalUnitsAdd,
    PhysicalUnitsList,
    PhysicalUnitsDetail,
    PhysicalUnitsUpdate,
    AssaySettingAdd,
    AssaySettingList,
    AssaySettingDetail,
    AssaySettingUpdate,
    AssaySampleLocationAdd,
    AssaySampleLocationUpdate,
    AssaySampleLocationList,
    AssaySupplierAdd,
    AssaySupplierUpdate,
    AssaySupplierList,
    AssayMeasurementTypeAdd,
    AssayMeasurementTypeUpdate,
    AssayMeasurementTypeList,
    AssayStudyComponents,
    get_current_upload_template,
    PBPKFilterView,
    PBPKView,
    AssayPlateReaderMapUpdate,
    AssayPlateReaderMapAdd,
    AssayPlateReaderMapIndex,
    AssayPlateReaderMapView,
    AssayPlateReaderMapDelete,
    AssayPlateReaderMapDataFileUpdate,
    AssayPlateReaderMapDataFileAdd,
    AssayPlateReaderMapDataFileIndex,
    AssayPlateReaderMapDataFileView,
    AssayPlateReaderMapDataFileDelete,
    AssayOmicDataFileUploadIndex,
    AssayOmicDataFileUploadAdd,
    AssayOmicDataFileUploadView,
    AssayOmicDataFileUploadUpdate,
    AssayOmicDataFileUploadDelete,
    AssayStudyOmics,
    AssayStudyTemplate,
    AssayStudyOmicsDownload
)
import assays.ajax

from django.views.generic import RedirectView


# TODO: WHY ARE THERE TWO DIFFERENT APPROACHES TO NAMES
urlpatterns = [
    # User can view all Editable Studies
    url(r'^assays/assaystudy/editable_studies/$', AssayStudyEditableList.as_view(), name='assays-editable-study-list'),
    # The main page for a study
    # TODO TO BE DEPRECATED
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/$', AssayStudyIndex.as_view(), name='assays-assaystudy-index'),
    # Update page for studies
    # TO BE DEPRECATED
    # url(r'^assays/assaystudy/(?P<pk>[0-9]+)/update/$', AssayStudyUpdate.as_view(), name='assays-assaystudy-update'),

    # Delete view for studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/delete/$', AssayStudyDelete.as_view(), name='assays-assaystudy-delete'),
    # Summary view for studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/summary/$', AssayStudySummary.as_view(), name='assays-assaystudy-summary'),
    # # All data for a study
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/data/$', AssayStudyData.as_view(), name='assays-assaystudy-data'),
    # # Bulk Readout Upload for Studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/upload/$', AssayStudyDataUpload.as_view(), name='assays-assaystudy-upload'),

    # Template for upload
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/upload/template/$', AssayStudyTemplate.as_view(), name='assays-assaystudy-upload-template'),

    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/sign_off/$', AssayStudySignOff.as_view(), name='assays-assaystudy-sign-off'),

    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/reproducibility/$', AssayStudyReproducibility.as_view(), name='assays-assaystudy-reproducibility'),

    # Images
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/images/$', AssayStudyImages.as_view(), name='assays-assaystudy-images'),

    # The multiple study forms
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/details/$', AssayStudyDetails.as_view(), name='assays-assaystudy-update-details'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/groups/$', AssayStudyGroups.as_view(), name='assays-assaystudy-update-groups'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/chips/$', AssayStudyChips.as_view(), name='assays-assaystudy-update-chips'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/plates/$', AssayStudyPlates.as_view(), name='assays-assaystudy-update-plates'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/assays/$', AssayStudyAssays.as_view(), name='assays-assaystudy-update-assays'),

    # View the chips
    url(r'^assays/assaychips/(?P<pk>[0-9]+)/$', AssayStudyChipsDetail.as_view(), name='assays-assaymatrix-chips-detail'),

    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/access/$', AssayStudyAccess.as_view(), name='assays-assaystudy-update-access'),

    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/data_index/$', AssayStudyDataIndex.as_view(), name='assays-assaystudy-data-index'),

    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/data_files/$', AssayDataFileUploadList.as_view(), name='assays-assaydatafileupload-list'),

    url(r'^assays/assaydatafileupload/(?P<pk>[0-9]+)/$', AssayDataFileUploadDetail.as_view(), name='assays-assaydatafileupload-detail'),

    # Just redirect for now
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/update/$', RedirectView.as_view(pattern_name='assays-assaystudy-update-details', permanent=True), name='assays-assaystudy-update'),

    url(r'^assays/assaystudy/(?P<study_id>[0-9]+)/plate/add/$', AssayStudyPlateAdd.as_view(), name='assays-assaymatrix-plate-add'),
    url(r'^assays/assayplate/(?P<pk>[0-9]+)/plate/$', AssayStudyPlateDetail.as_view(), name='assays-assaymatrix-plate-detail'),
    url(r'^assays/assayplate/(?P<pk>[0-9]+)/plate/update/$', AssayStudyPlateUpdate.as_view(), name='assays-assaymatrix-plate-update'),
    url(r'^assays/assayplate/(?P<pk>[0-9]+)/plate/delete/$', AssayMatrixDelete.as_view(), name='assays-assaymatrix-plate-delete'),

    # Group detail
    url(r'^assays/assaygroup/(?P<pk>[0-9]+)/$', AssayGroupDetail.as_view(), name='assays-assaygroup-detail'),

    # NEW_TO_BE_REVISED
    url(r'^assays/assaystudy/$', AssayStudyList.as_view(), name='assays-assaystudy-list'),
    url(r'^assays/assaystudy/add/$', AssayStudyAdd.as_view(), name='assays-assaystudy-add'),

    url(r'^assays/assaymatrixitem/(?P<pk>[0-9]+)/$', AssayMatrixItemDetail.as_view(), name='assays-assaymatrixitem-detail'),
    url(r'^assays/assaymatrixitem/(?P<pk>[0-9]+)/update/$', AssayMatrixItemUpdate.as_view(), name='assays-assaymatrixitem-update'),
    url(r'^assays/assaymatrixitem/(?P<pk>[0-9]+)/delete/$', AssayMatrixItemDelete.as_view(), name='assays-assaymatrixitem-delete'),

    url(r'^assays/studyconfiguration/$', AssayStudyConfigurationList.as_view(), name='assays-assays-assaystudyconfiguration-list'),
    url(r'^assays/studyconfiguration/add/$', AssayStudyConfigurationAdd.as_view(), name='assays-assaystudyconfiguration-add'),
    url(r'^assays/studyconfiguration/(?P<pk>[0-9]+)/$', AssayStudyConfigurationUpdate.as_view(), name='assays-assaystudyconfiguration-update'),

    # TO BE DEPRECATED
    # Add a matrix
    # url(r'^assays/assaystudy/(?P<study_id>[0-9]+)/assaymatrix/add/$', AssayMatrixAdd.as_view(), name='assays-assaymatrix-add'),
    # url(r'^assays/assaymatrix/(?P<pk>[0-9]+)/$', AssayMatrixDetail.as_view(), name='assays-assaymatrix-detail'),
    # url(r'^assays/assaymatrix/(?P<pk>[0-9]+)/update/$', AssayMatrixUpdate.as_view(), name='assays-assaymatrix-update'),
    # url(r'^assays/assaymatrix/(?P<pk>[0-9]+)/delete/$', AssayMatrixDelete.as_view(), name='assays-assaymatrix-delete'),

    # url(r'^assays/assaymatrix/(?P<pk>[0-9]+)/new/$', AssayMatrixNew.as_view(), name='assays-assaymatrix-new'),

    # Location for assay filter
    url(r'^assays/graphing_reproducibility/$', GraphingReproducibilityFilterView.as_view(), name='assays-graphing-reproducibility'),

    # Separate URLs for plots and repro
    url(r'^assays/assay_interstudy_reproducibility/$', AssayInterStudyReproducibility.as_view(), name='assays-interstudy-reproducibility'),
    url(r'^assays/assaystudy_data_plots/$', AssayStudyDataPlots.as_view(), name='assays-assaystudy-data-plots'),

    # Study Set urls
    url(
        r'^assays/assaystudyset/add/$',
        AssayStudySetAdd.as_view(),
        name='assays-assaystudyset-add'
    ),
    url(
        r'^assays/assaystudyset/(?P<pk>[0-9]+)/update/$',
        AssayStudySetUpdate.as_view(),
        name='assays-assaystudyset-update'
    ),
    url(
        r'^assays/assaystudyset/(?P<pk>[0-9]+)/$',
        AssayStudySetDataPlots.as_view(),
        name='assays-assaystudyset-data-plots'
    ),
    url(
        r'^assays/assaystudyset/(?P<pk>[0-9]+)/reproducibility/$',
        AssayStudySetReproducibility.as_view(),
        name='assays-assaystudyset-reproducibility'
    ),
    url(
        r'^assays/assaystudyset/$',
        AssayStudySetList.as_view(),
        name='assays-assaystudyset-list'
    ),

    url(
        r'^assays/assaystudyset/(?P<pk>[0-9]+)/data/$',
        AssayStudySetData.as_view(),
        name='assays-assaystudyset-data'
    ),

    # Data from filters
    url(r'^assays/data_from_filters/$', AssayDataFromFilters.as_view(), name='assays-data-from-filters'),

    # Power Analysis
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/power_analysis/$', AssayStudyPowerAnalysisStudy.as_view(), name='assays-power-analysis-study'),

    # Omics Interface + Download Filtered Data
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/omics/$', AssayStudyOmics.as_view(), name='assays-assaystudy-omics'),
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/omics/download/$', AssayStudyOmicsDownload.as_view(), name='assays-assaystudy-omics-download'),

    # PBPK filter
    url(r'^assays/pbpk_filter/$', PBPKFilterView.as_view(), name='assays-pbpk-filter'),
    # PBPK
    url(r'^assays/pbpk/$', PBPKView.as_view(), name='assays-pbpk'),

    # References
    url(r'^assays/assayreference/$', AssayReferenceList.as_view(), name='assays-assayreference-list'),
    url(r'^assays/assayreference/add/$', AssayReferenceAdd.as_view(), name='assays-assayreference-add'),
    url(r'^assays/assayreference/(?P<pk>[0-9]+)/$', AssayReferenceDetail.as_view(), name='assays-assayreference-detail'),
    url(r'^assays/assayreference/(?P<pk>[0-9]+)/update/$', AssayReferenceUpdate.as_view(), name='assays-assayreference-update'),
    url(r'^assays/assayreference/(?P<pk>[0-9]+)/delete/$', AssayReferenceDelete.as_view(), name='assays-assayreference-delete'),

    # Target
    url(r'^assays/target/$', AssayTargetList.as_view(), name='assays-assaytarget-list'),
    url(r'^assays/target/(?P<pk>[0-9]+)/$', AssayTargetDetail.as_view(), name='assays-assaytarget-detail'),
    url(r'^assays/target/(?P<pk>[0-9]+)/update/$', AssayTargetUpdate.as_view(), name='assays-assaytarget-update'),
    url(r'^assays/target/(?P<pk>[0-9]+)/update/restricted/$', AssayTargetUpdateRestricted.as_view(), name='assays-assaytarget-restricted'),
    url(r'^assays/target/add/$', AssayTargetAdd.as_view(), name='assays-assaytarget-add'),

    # Methods
    url(r'^assays/method/$', AssayMethodList.as_view(), name='assays-assaymethod-list'),
    url(r'^assays/method/(?P<pk>[0-9]+)/$', AssayMethodDetail.as_view(), name='assays-assaymethod-detail'),
    url(r'^assays/method/(?P<pk>[0-9]+)/update/$', AssayMethodUpdate.as_view(), name='assays-assaymethod-update'),
    url(r'^assays/method/(?P<pk>[0-9]+)/update/restricted/$', AssayMethodUpdateRestricted.as_view(), name='assays-assaymethod-restricted'),
    url(r'^assays/method/add/$', AssayMethodAdd.as_view(), name='assays-assaymethod-add'),

    # Setting
    url(r'^assays/setting/$', AssaySettingList.as_view(), name='assays-assaysetting-list'),
    url(r'^assays/setting/(?P<pk>[0-9]+)/$', AssaySettingDetail.as_view(), name='assays-assaysetting-detail'),
    url(r'^assays/setting/(?P<pk>[0-9]+)/update/$', AssaySettingUpdate.as_view(), name='assays-assaysetting-update'),
    url(r'^assays/setting/add/$', AssaySettingAdd.as_view(), name='assays-assaysetting-add'),

    # Units
    url(r'^assays/unit/$', PhysicalUnitsList.as_view(), name='assays-physicalunits-list'),
    # url(r'^assays/unit/(?P<pk>[0-9]+)/$', PhysicalUnitsDetail.as_view(), name='assays-physicalunits-detail'),
    url(r'^assays/unit/(?P<pk>[0-9]+)/update/$', PhysicalUnitsUpdate.as_view(), name='assays-physicalunits-update'),
    url(r'^assays/unit/add/$', PhysicalUnitsAdd.as_view(), name='assays-physicalunits-add'),

    # Sample Locations
    url(r'^assays/location/$', AssaySampleLocationList.as_view(), name='assays-assaysamplelocation-list'),
    # url(r'^assays/location/(?P<pk>[0-9]+)/$', AssaySampleLocationDetail.as_view(), name='assays-assaysamplelocation-detail'),
    url(r'^assays/location/(?P<pk>[0-9]+)/update/$', AssaySampleLocationUpdate.as_view(), name='assays-assaysamplelocation-update'),
    url(r'^assays/location/add/$', AssaySampleLocationAdd.as_view(), name='assays-assaysamplelocation-add'),

    # Supplier
    url(r'^assays/supplier/$', AssaySupplierList.as_view(), name='assays-assaysupplier-list'),
    # url(r'^assays/supplier/(?P<pk>[0-9]+)/$', AssaySupplierDetail.as_view(), name='assays-assaysupplier-detail'),
    url(r'^assays/supplier/(?P<pk>[0-9]+)/update/$', AssaySupplierUpdate.as_view(), name='assays-assaysupplier-update'),
    url(r'^assays/supplier/add/$', AssaySupplierAdd.as_view(), name='assays-assaysupplier-add'),

    # Measurement Type
    url(r'^assays/measurementtype/$', AssayMeasurementTypeList.as_view(), name='assays-assaymeasurementtype-list'),
    # url(r'^assays/measurementtype/(?P<pk>[0-9]+)/$', AssayMeasurementTypeDetail.as_view(), name='assays-assaymeasurementtype-detail'),
    url(r'^assays/measurementtype/(?P<pk>[0-9]+)/update/$', AssayMeasurementTypeUpdate.as_view(), name='assays-assaymeasurementtype-update'),
    url(r'^assays/measurementtype/add/$', AssayMeasurementTypeAdd.as_view(), name='assays-assaymeasurementtype-add'),

    # Should this be here?
    url(r'^studycomponents/$', AssayStudyComponents.as_view(), name='assays-studycomponents'),

    # Get the current upload template
    url(r'^assays/current_upload_template/$', get_current_upload_template, name='assays-currentuploadtemplate'),

    # Ajax
    url(r'^assays_ajax/$', assays.ajax.ajax),

    # Maybe we ought to change the name for consistency?
    # Plate Map (add and update will go to the same page, content = True for one of them...)
    # Note pk vs. study_id
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/assayplatereadermap/$', AssayPlateReaderMapIndex.as_view(), name='assayplatereadermap-index'),
    url(r'^assays/assaystudy/(?P<study_id>[0-9]+)/assayplatereadermap/add/$', AssayPlateReaderMapAdd.as_view(), name='assayplatereadermap-add'),
    url(r'^assays/assayplatereadermap/(?P<pk>[0-9]+)/view/$', AssayPlateReaderMapView.as_view(), name='assayplatereadermap-view'),
    url(r'^assays/assayplatereadermap/(?P<pk>[0-9]+)/update/$', AssayPlateReaderMapUpdate.as_view(), name='assayplatereadermap-update'),
    url(r'^assays/assayplatereadermap/(?P<pk>[0-9]+)/delete/$', AssayPlateReaderMapDelete.as_view(), name='assayplatereadermap-delete'),

    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/assayplatereaderfile/$', AssayPlateReaderMapDataFileIndex.as_view(), name='assayplatereaderfile-index'),
    url(r'^assays/assaystudy/(?P<study_id>[0-9]+)/assayplatereaderfile/add/$', AssayPlateReaderMapDataFileAdd.as_view(), name='assayplatereaderfile-add'),
    url(r'^assays/assayplatereaderfile/(?P<pk>[0-9]+)/view/$', AssayPlateReaderMapDataFileView.as_view(), name='assayplatereaderfile-view'),
    url(r'^assays/assayplatereaderfile/(?P<pk>[0-9]+)/update/$', AssayPlateReaderMapDataFileUpdate.as_view(), name='assayplatereaderfile-update'),
    url(r'^assays/assayplatereaderfile/(?P<pk>[0-9]+)/delete/$', AssayPlateReaderMapDataFileDelete.as_view(), name='assayplatereaderfile-delete'),

    # Omic Data
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/assayomicdatafileupload/$', AssayOmicDataFileUploadIndex.as_view(), name='assayomicdatafileupload-index'),
    url(r'^assays/assaystudy/(?P<study_id>[0-9]+)/assayomicdatafileupload/add/$', AssayOmicDataFileUploadAdd.as_view(), name='assayomicdatafileupload-add'),
    url(r'^assays/assayomicdatafileupload/(?P<pk>[0-9]+)/view/$', AssayOmicDataFileUploadView.as_view(), name='assayomicdatafileupload-view'),
    url(r'^assays/assayomicdatafileupload/(?P<pk>[0-9]+)/update/$', AssayOmicDataFileUploadUpdate.as_view(), name='assayomicdatafileupload-update'),
    url(r'^assays/assayomicdatafileupload/(?P<pk>[0-9]+)/delete/$', AssayOmicDataFileUploadDelete.as_view(), name='assayomicdatafileupload-delete'),

]
