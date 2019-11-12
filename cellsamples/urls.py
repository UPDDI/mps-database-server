from django.conf.urls import url
from .views import (
    CellSampleAdd,
    CellSampleList,
    CellSampleUpdate,
    CellTypeAdd,
    CellTypeList,
    CellTypeUpdate,
    CellSubtypeAdd,
    CellSubtypeList,
    CellSubtypeUpdate,
    BiosensorAdd,
    BiosensorList,
    BiosensorUpdate,
    SupplierAdd,
    SupplierList,
    SupplierUpdate,
)
import cellsamples.ajax

urlpatterns = [
    # Proposed URLS:
    # specify cellsample if we decide to also let users add cell type etc.
    url(r'^cellsamples/cellsample/add/$', CellSampleAdd.as_view(), name='cellsamples-cellsample-add'),
    url(r'^cellsamples/cellsample/$', CellSampleList.as_view(), name='cellsamples-cellsample-list'),
    url(r'^cellsamples/cellsample/(?P<pk>[0-9]+)/$', CellSampleUpdate.as_view(), name='cellsamples-cellsample-update'),

    url(r'^cellsamples/celltype/add/$', CellTypeAdd.as_view(), name='cellsamples-celltype-add'),
    url(r'^cellsamples/celltype/$', CellTypeList.as_view(), name='cellsamples-celltype-list'),
    url(r'^cellsamples/celltype/(?P<pk>[0-9]+)/$', CellTypeUpdate.as_view(), name='cellsamples-celltype-update'),

    url(r'^cellsamples/cellsubtype/add/$', CellSubtypeAdd.as_view(), name='cellsamples-cellsubtype-add'),
    url(r'^cellsamples/cellsubtype/$', CellSubtypeList.as_view(), name='cellsamples-cellsubtype-list'),
    url(r'^cellsamples/cellsubtype/(?P<pk>[0-9]+)/$', CellSubtypeUpdate.as_view(), name='cellsamples-cellsubtype-update'),

    # Biosensor
    url(r'^cellsamples/biosensor/add/$', BiosensorAdd.as_view(), name='cellsamples-biosensor-add'),
    url(r'^cellsamples/biosensor/$', BiosensorList.as_view(), name='cellsamples-biosensor-list'),
    url(r'^cellsamples/biosensor/(?P<pk>[0-9]+)/$', BiosensorUpdate.as_view(), name='cellsamples-biosensor-update'),

    # Supplier
    url(r'^cellsamples/supplier/add/$', SupplierAdd.as_view(), name='cellsamples-supplier-add'),
    url(r'^cellsamples/supplier/$', SupplierList.as_view(), name='cellsamples-supplier-list'),
    url(r'^cellsamples/supplier/(?P<pk>[0-9]+)/$', SupplierUpdate.as_view(), name='cellsamples-supplier-update'),

    url(r'^cellsamples_ajax/$', cellsamples.ajax.ajax),
]
