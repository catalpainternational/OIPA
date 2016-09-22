from builtins import object
from rest_framework import serializers
import iati


class ActivityListSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = iati.models.Activity
        fields = ('id',)
