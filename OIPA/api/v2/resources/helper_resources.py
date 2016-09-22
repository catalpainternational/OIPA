from builtins import object
# Tastypie specific
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.constants import ALL
# Data specific
from iati.models import *


class LanguageResource(ModelResource):
    class Meta(object):
        queryset = Language.objects.all()
        include_resource_uri = False
        excludes = ['id']


class TitleResource(ModelResource):
    language = fields.ToOneField(LanguageResource, 'language', full=True, null=True)
    class Meta(object):
        queryset = Title.objects.all()
        include_resource_uri = False
        excludes = ['id']


class DescriptionResource(ModelResource):
    language = fields.ToOneField(LanguageResource, 'language', full=True, null=True)
    class Meta(object):
        queryset = Description.objects.all()
        include_resource_uri = False
        excludes = ['id']


class OrganisationTypeResource(ModelResource):

    class Meta(object):
        queryset = OrganisationType.objects.all()
        include_resource_uri = False


class ParticipatingOrganisationResource(ModelResource):

    class Meta(object):
        queryset = ActivityParticipatingOrganisation.objects.all()
        include_resource_uri = False
        excludes = ['type', 'reported_by_organisation', 'abbreviation']


class ActivityStatusResource(ModelResource):
    class Meta(object):
        queryset = ActivityStatus.objects.all()
        include_resource_uri = False


class CollaborationTypeResource(ModelResource):
    class Meta(object):
        queryset = CollaborationType.objects.all()
        include_resource_uri = False


class FlowTypeResource(ModelResource):
    class Meta(object):
        queryset = FlowType.objects.all()
        include_resource_uri = False


class AidTypeResource(ModelResource):
    class Meta(object):
        queryset = AidType.objects.all()
        include_resource_uri = False


class FinanceTypeResource(ModelResource):
    class Meta(object):
        queryset = FinanceType.objects.all()
        include_resource_uri = False


class TiedStatusResource(ModelResource):
    class Meta(object):
        queryset = TiedStatus.objects.all()
        include_resource_uri = False

class ActivityBudgetResource(ModelResource):
    class Meta(object):
        queryset = Budget.objects.all()
        include_resource_uri = False
        excludes = ['id']


class TransactionResource(ModelResource):
    class Meta(object):
        queryset = Transaction.objects.all()
        include_resource_uri = False
        filtering = {
            'value': ALL,
            }

class DocumentResource(ModelResource):
    class Meta(object):
        queryset = DocumentLink.objects.all()
        include_resource_uri = False
        excludes = ['id']


class RecipientCountryResource(ModelResource):
    class Meta(object):
        queryset = ActivityRecipientCountry.objects.all()
        include_resource_uri =  False


class RecipientRegionResource(ModelResource):
    class Meta(object):
        queryset = ActivityRecipientRegion.objects.all()
        include_resource_uri = False

