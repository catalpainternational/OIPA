from __future__ import absolute_import
from rest_framework import generics
import iati
from . import serializers


class ActivityList(generics.ListAPIView):
    queryset = iati.models.Activity.objects.all()
    serializer_class = serializers.ActivityListSerializer
