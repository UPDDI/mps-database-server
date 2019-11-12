from django.conf.urls import url
from microdevices.views import (
    MicrodeviceList,
    MicrodeviceDetail,
    OrganModelList,
    OrganModelDetail,
    MicrodeviceAdd,
    OrganModelAdd,
    MicrodeviceUpdate,
    OrganModelUpdate,
    MicrophysiologyCenterDetail,
    OrganModelProtocolUpdate,
    ManufacturerList,
    ManufacturerAdd,
    ManufacturerUpdate,
)

urlpatterns = [
    # User can view their studies
    url(r'^microdevices/device/$', MicrodeviceList.as_view(), name='microdevices-microdevice-list'),
    url(r'^microdevices/device/(?P<pk>[0-9]+)/$', MicrodeviceDetail.as_view(), name='microdevices-microdevice-detail'),
    url(r'^microdevices/device/add/$', MicrodeviceAdd.as_view(), name='microdevices-microdevice-add'),
    url(r'^microdevices/device/(?P<pk>[0-9]+)/update/$', MicrodeviceUpdate.as_view(), name='microdevices-microdevice-update'),

    url(r'^microdevices/model/$', OrganModelList.as_view(), name='microdevices-organmodel-list'),
    url(r'^microdevices/model/(?P<pk>[0-9]+)/$', OrganModelDetail.as_view(), name='microdevices-organmodel-detail'),
    url(r'^microdevices/model/add/$', OrganModelAdd.as_view(), name='microdevices-organmodel-add'),
    url(r'^microdevices/model/(?P<pk>[0-9]+)/update/$', OrganModelUpdate.as_view(), name='microdevices-organmodel-update'),

    url(r'^microdevices/protocol/(?P<pk>[0-9]+)/update/$', OrganModelProtocolUpdate.as_view(), name='microdevices-organmodelprotocol-update'),

    url(r'^microdevices/center/(?P<pk>[0-9]+)/$', MicrophysiologyCenterDetail.as_view(), name='microdevices-microphysiologycenter-detail'),

    # manufacturer
    url(r'^microdevices/manufacturer/$', ManufacturerList.as_view(), name='microdevices-manufacturer-list'),
    # url(r'^microdevices/manufacturer/(?P<pk>[0-9]+)/$', ManufacturerDetail.as_view(), name='microdevices-manufacturer-detail'),
    url(r'^microdevices/manufacturer/(?P<pk>[0-9]+)/update/$', ManufacturerUpdate.as_view(), name='microdevices-manufacturer-update'),
    url(r'^microdevices/manufacturer/add/$', ManufacturerAdd.as_view(), name='microdevices-manufacturer-add'),
]
