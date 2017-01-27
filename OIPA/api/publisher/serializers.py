from rest_framework.serializers import HyperlinkedIdentityField
from iati_synchroniser.models import Publisher
from iati_synchroniser.models import IatiXmlSource
from api.generics.serializers import DynamicFieldsModelSerializer
from api.dataset.serializers import DatasetSerializer
from rest_framework.serializers import SerializerMethodField

from django.core.urlresolvers import reverse
from iati.models import Activity
from django.db.models import Sum


class PublisherSerializer(DynamicFieldsModelSerializer):

    url = HyperlinkedIdentityField(view_name='publishers:publisher-detail')
    datasets = DatasetSerializer(
        many=True, 
        source="iatixmlsource_set",
        fields=('url', 'ref', 'title', 'type', 'source_url'))
    activity_count = SerializerMethodField()
    note_count = SerializerMethodField()
    activities = SerializerMethodField()

    class Meta:
        model = Publisher
        fields = (
            'url',
            'id',
            'org_id',
            'org_abbreviate',
            'org_name',
            'activities',
            'activity_count',
            'note_count',
            'datasets')

    def get_activities(self, obj):
        request = self.context.get('request')
        url = request.build_absolute_uri(reverse('activities:activity-list'))
        return url + '?reporting_organisation=' + obj.org_id

    def get_activity_count(self, obj):
        return Activity.objects.filter(reporting_organisations__normalized_ref=obj.org_id).count()

    def get_note_count(self, obj):
        sum_queryset = IatiXmlSource.objects.filter(publisher=obj.id).aggregate(Sum('note_count'))
        return sum_queryset.get('note_count__sum')

