# coding=utf-8

"""
Bioactivities URL router
"""

from django.conf.urls import url
import bioactivities.views

urlpatterns = [
    url(
        r'^bioactivities/$',
        # bioactivities.views.bioactivities_list
        bioactivities.views.BioactivitiesList.as_view(),
        name='bioactivities-list',
    ),
    # Old API
    # url(r'^bioactivities/(?P<pk>[0-9]+)/$',
    #     'bioactivities_detail'),
    url(
        r'^bioactivities/all_bioactivities/$',
        bioactivities.views.list_of_all_bioactivities_in_bioactivities
    ),
    url(
        r'^bioactivities/all_targets/$',
        bioactivities.views.list_of_all_targets_in_bioactivities
    ),
    url(
        r'^bioactivities/all_compounds/$',
        bioactivities.views.list_of_all_compounds_in_bioactivities
    ),
    url(
        r'^bioactivities/all_data/$',
        bioactivities.views.list_of_all_data_in_bioactivities
    ),
    url(
        r'^bioactivities/gen_heatmap/$',
        bioactivities.views.gen_heatmap
    ),
    url(
        r'^bioactivities/heatmap/$',
        # bioactivities.views.view_heatmap
        bioactivities.views.ViewHeatmap.as_view(),
        name='bioactivities-heatmap',
    ),
    url(
        r'^bioactivities/gen_cluster/$',
        bioactivities.views.gen_cluster
    ),
    url(
        r'^bioactivities/cluster/$',
        # bioactivities.views.view_cluster,
        bioactivities.views.ViewCluster.as_view(),
        name='bioactivities-cluster',
    ),
    url(
        r'^bioactivities/gen_table/$',
        bioactivities.views.gen_table
    ),
    url(
        r'^bioactivities/table/$',
        # bioactivities.views.view_table
        bioactivities.views.ViewTable.as_view(),
        name='bioactivities-table',
    ),
    url(
        r'^bioactivities/model/$',
        # bioactivities.views.view_model
        bioactivities.views.ViewModel.as_view(),
        name='bioactivities-model',
    )
]
