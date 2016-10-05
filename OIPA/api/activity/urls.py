from __future__ import absolute_import
from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns(
    '',
    url('^activities/$', views.ActivityList.as_view(), name='activity-list'),
)
