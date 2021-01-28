from django.conf.urls import url
from .views import (
    DiseaseList,
    # DiseaseOverview,
    DiseaseInformation,
    # DiseaseClinicalData,
    DiseaseBiology,
    # DiseaseModel,
    DiseaseComponents,
    DiseaseModels,
    DiseaseData,
    DiseaseMPS,
)

urlpatterns = [
    url(r'^diseases/$', DiseaseList.as_view()),
    # url(r'^diseases/(?P<pk>[0-9]+)/$', DiseaseOverview.as_view()),
    url(
        r'^diseases/(?P<pk>[0-9]+)/$',
        DiseaseInformation.as_view(),
        name='diseases-disease-information'
    ),
    # url(r'^diseases/(?P<pk>[0-9]+)/clinicaldata/$', DiseaseClinicalData.as_view()),
    url(
        r'^diseases/(?P<pk>[0-9]+)/biology/$',
        DiseaseBiology.as_view(),
        name='diseases-disease-biology'
    ),
    url(
        r'^diseases/(?P<pk>[0-9]+)/models/$',
        DiseaseModels.as_view(),
        name='diseases-disease-models'
    ),
    url(
        r'^diseases/(?P<pk>[0-9]+)/components/$',
        DiseaseComponents.as_view(),
        name='diseases-disease-components'
    ),
    url(
        r'^diseases/(?P<pk>[0-9]+)/data/$',
        DiseaseData.as_view(),
        name='diseases-disease-data'
    ),
    url(
        r'^diseases/(?P<pk>[0-9]+)/mps/$',
        DiseaseMPS.as_view(),
        name='diseases-disease-mps'
    ),
]
