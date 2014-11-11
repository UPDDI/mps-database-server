from django.conf.urls import patterns, url
from .views import *

urlpatterns = patterns('',
    url(r'^compounds/$', CompoundsList.as_view()),
    url(r'^compounds/(?P<pk>[0-9]+)/$', CompoundsDetails.as_view(), name='compound-detail'),
)
