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
    OrganModelProtocolUpdate
)

urlpatterns = [
    # User can view their studies
    url(r'^microdevices/device/$', MicrodeviceList.as_view(), name='microdevice-list'),
    url(r'^microdevices/device/(?P<pk>[0-9]+)/$', MicrodeviceDetail.as_view(), name='microdevice-detail'),
    url(r'^microdevices/model/$', OrganModelList.as_view(), name='model-list'),
    url(r'^microdevices/model/(?P<pk>[0-9]+)/$', OrganModelDetail.as_view(), name='model-detail'),
    url(r'^microdevices/device/add/$', MicrodeviceAdd.as_view(), name='microdevice-add'),
    url(r'^microdevices/model/add/$', OrganModelAdd.as_view(), name='model-add'),
    url(r'^microdevices/device/(?P<pk>[0-9]+)/update/$', MicrodeviceUpdate.as_view(), name='microdevice-update'),
    url(r'^microdevices/model/(?P<pk>[0-9]+)/update/$', OrganModelUpdate.as_view(), name='model-update'),
    url(r'^microdevices/protocol/(?P<pk>[0-9]+)/update/$', OrganModelProtocolUpdate.as_view(), name='protocol-update'),
    url(r'^microdevices/center/(?P<pk>[0-9]+)/$', MicrophysiologyCenterDetail.as_view(), name='center-detail'),
]
