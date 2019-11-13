from django.conf.urls import url
from .views import (
    CompoundsList,
    CompoundsAdd,
    CompoundsReport,
    CompoundsDetail,
    CompoundsUpdate
)
import compounds.ajax

urlpatterns = [
    url(r'^compounds/$', CompoundsList.as_view(), name='compounds-compound-list'),
    url(r'^compounds/add/$', CompoundsAdd.as_view(), name='compounds-compound-add'),
    url(r'^compounds/report/$', CompoundsReport.as_view(), name='compounds-compound-report'),
    url(r'^compounds/(?P<pk>[0-9]+)/$', CompoundsDetail.as_view(), name='compounds-compound-detail'),
    url(r'^compounds/(?P<pk>[0-9]+)/update/$', CompoundsUpdate.as_view(), name='compounds-compound-update'),
    url(r'^compounds_ajax/$', compounds.ajax.ajax),
]
