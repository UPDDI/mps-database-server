from django.conf.urls import url
# TODO NO WILDCARDS PLEASE
from assays.views import *
import assays.ajax

urlpatterns = [
    # User can view their studies
    # User can view all Editable Studies
    url(r'^assays/assaystudy/editable_studies/$', AssayStudyEditableList.as_view(), name='editable_study_list'),
    # The main page for a study
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/$', AssayStudyIndex.as_view(), name='assay_study_index'),
    # Update page for studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/update/$', AssayStudyUpdate.as_view(), name='asssay_study_update'),
    # Delete view for studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/delete/$', AssayStudyDelete.as_view(), name='assay_study_delete'),
    # Summary view for studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/summary/$', AssayStudySummary.as_view(), name='assay_study_summary'),
    # # All data for a study
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/data/$', AssayStudyData.as_view(), name='assay_study_data'),
    # # Bulk Readout Upload for Studies
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/upload/$', AssayStudyDataUpload.as_view(), name='assay_study_upload'),
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
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/sign_off/$', AssayStudySignOff.as_view(), name='assay_study_sign_off'),

    url(r'^assays/studyconfiguration/$', AssayStudyConfigurationList.as_view(), name='studyconfiguration_list'),
    url(r'^assays/studyconfiguration/add/$', AssayStudyConfigurationAdd.as_view(), name='studyconfiguration_add'),
    url(r'^assays/studyconfiguration/(?P<pk>[0-9]+)/$', AssayStudyConfigurationUpdate.as_view(), name='studyconfiguration_update'),

    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/reproducibility/$', AssayStudyReproducibility.as_view(), name='assay_study_reproducibility'),

    # Images
    url(r'^assays/assaystudy/(?P<pk>[0-9]+)/images/$', AssayStudyImages.as_view(), name='study-images'),

    # Ajax
    url(r'^assays_ajax/$', assays.ajax.ajax),
]
