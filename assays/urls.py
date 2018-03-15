from django.conf.urls import patterns, url
from assays.views import *

urlpatterns = patterns('',
    # User can view their studies
    # url(r'^assays/user_index/$', UserIndex.as_view(), name='user_index'),
    # User can view all Editable Studies
    url(r'^assays/editable_studies/$', GroupIndex.as_view(), name='editable_studies'),
    # The main page for a study
    url(r'^assays/(?P<pk>[0-9]+)/$', StudyIndex.as_view(), name='study_index'),
    # Update page for studies
    url(r'^assays/(?P<pk>[0-9]+)/update/$', AssayRunUpdate.as_view(), name='study-update'),
    # Delete view for studies
    url(r'^assays/(?P<pk>[0-9]+)/delete/$', AssayRunDelete.as_view(), name='study-delete'),
    # Summary view for studies
    url(r'^assays/(?P<pk>[0-9]+)/summary/$', AssayRunSummary.as_view(), name='study-summary'),
    # All data for a study
    url(r'^assays/(?P<pk>[0-9]+)/data/$', ReturnStudyData.as_view(), name='study-data'),
    # Bulk Readout Upload for Studies
    url(r'^assays/(?P<pk>[0-9]+)/bulk/$', ReadoutBulkUpload.as_view(), name='readout-bulk-upload'),
    # Sign off
    url(r'^assays/(?P<pk>[0-9]+)/sign_off/$', AssayRunSignOff.as_view(), name='study-sign_off'),
    # # Change pages for respective models
    url(r'^assays/assaychipsetup/(?P<pk>[0-9]+)/update/$', AssayChipSetupUpdate.as_view(), name='setup_update'),
    url(r'^assays/assaychipreadout/(?P<pk>[0-9]+)/update/$', AssayChipReadoutUpdate.as_view(), name='readout_update'),
    url(r'^assays/assaychiptestresult/(?P<pk>[0-9]+)/update/$', AssayChipTestResultUpdate.as_view(), name='result_update'),

    # # Add pages for respective models
    url(r'^assays/(?P<study_id>[0-9]+)/assaychipsetup/add/$', AssayChipSetupAdd.as_view(), name='setup_add'),
    url(r'^assays/(?P<study_id>[0-9]+)/assaychipreadout/add/$', AssayChipReadoutAdd.as_view(), name='readout_add'),
    url(r'^assays/(?P<study_id>[0-9]+)/assaychiptestresult/add/$', AssayChipTestResultAdd.as_view(), name='result_add'),

    # # Delete pages for respective models
    url(r'^assays/assaychipsetup/(?P<pk>[0-9]+)/delete/$', AssayChipSetupDelete.as_view(), name='setup_delete'),
    url(r'^assays/assaychipreadout/(?P<pk>[0-9]+)/delete/$', AssayChipReadoutDelete.as_view(), name='readout_delete'),
    url(r'^assays/assaychiptestresult/(?P<pk>[0-9]+)/delete/$', AssayChipTestResultDelete.as_view(), name='result_delete'),

    url(r'^assays/studyconfiguration/$', StudyConfigurationList.as_view(), name='studyconfiguration_list'),
    url(r'^assays/studyconfiguration/add/$', StudyConfigurationAdd.as_view(), name='studyconfiguration_add'),
    url(r'^assays/studyconfiguration/(?P<pk>[0-9]+)/$', StudyConfigurationUpdate.as_view(), name='studyconfiguration_update'),

    url(r'^assays/study/$', AssayRunList.as_view(), name='study_list'),
    url(r'^assays/study/add/$', AssayRunAdd.as_view(), name='study_add'),

    url(r'^assays/assaychipsetup/$', AssayChipSetupList.as_view(), name='setup_list'),
    url(r'^assays/assaychipsetup/(?P<pk>[0-9]+)/$', AssayChipSetupDetail.as_view(), name='setup_detail'),

    url(r'^assays/assaychipreadout/$', AssayChipReadoutList.as_view(), name='readout_list'),
    url(r'^assays/assaychipreadout/(?P<pk>[0-9]+)/$', AssayChipReadoutDetail.as_view(), name='readout_detail'),

    url(r'^assays/assaychiptestresult/$', AssayChipTestResultList.as_view(), name='result_list'),
    url(r'^assays/assaychiptestresult/(?P<pk>[0-9]+)/$', AssayChipTestResultDetail.as_view(), name='result_detail'),

    url(r'^assays/(?P<pk>[0-9]+)/reproducibility/$', AssayRunReproducibility.as_view(), name='run-reproducibility')
)
