from datetime import datetime

from django.contrib.gis.geos import GEOSGeometry, Point

from iati_parser import IatiParser
from iati import models
from iati.transaction import models as transaction_models
from iati_codelists import models as codelist_models
from iati_vocabulary import models as vocabulary_models
from iati_organisation import models as organisation_models
from geodata.models import Country, Region
from iati.parser import post_save
from currency_convert import convert


class Parse(IatiParser):

    VERSION = '2.01' 

    def __init__(self, *args, **kwargs):
        super(Parse, self).__init__(*args, **kwargs)

    def add_narrative(self, element, parent):
        # set on activity (if set)
        default_lang = self.default_lang
        lang = element.attrib.get('{http://www.w3.org/XML/1998/namespace}lang', default_lang).lower()
        text = element.text

        if lang:
            lang = lang.lower()

        language = self.get_or_none(codelist_models.Language, code=lang)

        if not parent:
            raise self.RequiredFieldError("parent", "Narrative: parent object must be passed")

        register_name = parent.__class__.__name__ + "Narrative"

        if not language:
            raise self.RequiredFieldError(
                "language",
                "{}: must specify default_lang on activities or language on the element itself".format(register_name))
        if not text:
            raise self.RequiredFieldError("text", "{}: must contain text".format(register_name))

        narrative = models.Narrative()
        narrative.language = language
        narrative.content = element.text
        narrative.related_object = parent
        narrative.activity = self.get_model('Activity')

        # TODO: handle this differently (also: breaks tests)
        self.register_model(register_name, narrative)

    def iati_activities__iati_activity(self, element):
        """attributes:
        {http://www.w3.org/XML/1998/namespace}lang:en
        default-currency:USD
        last-updated-datetime:2014-09-10T07:15:37Z
        linked-data-uri:http://data.example.org/123456789
        hierarchy:1

        tag:iati-activity"""

        id = self._normalize(element.xpath('iati-identifier/text()')[0])

        default_lang = element.attrib.get('{http://www.w3.org/XML/1998/namespace}lang').lower()
        hierarchy = element.attrib.get('hierarchy')
        last_updated_datetime = self.validate_date(element.attrib.get('last-updated-datetime'))
        linked_data_uri = element.attrib.get('linked-data-uri')
        default_currency = self.get_or_none(models.Currency, code=element.attrib.get('default-currency'))

        if not id:
            raise self.RequiredFieldError("id", "activity: must contain id")
        
        old_activity = self.get_or_none(models.Activity, id=id)

        if old_activity and not self.force_reparse:
            # update last_updated_model to prevent the activity from being deleted
            # because its not updated (and thereby assumed not found in the source)
            old_activity.save()

            if last_updated_datetime and last_updated_datetime == old_activity.last_updated_datetime:
                raise self.ValidationError(
                    "activity",
                    "current version of activity already exists: no need to update")
            if last_updated_datetime and (last_updated_datetime < old_activity.last_updated_datetime):
                raise self.ValidationError(
                    "activity",
                    "newer version of activity exists: last_updated_time is less than existing activity")
            if not last_updated_datetime and old_activity.last_updated_datetime:
                raise self.ValidationError(
                    "activity",
                    "duplicate activity: last_updated_time is not present, but is present on 'old' activity")
    
            # TODO: test activity is deleted along with related models
            # update on TODO above; only iati_title, TransactionReceiver, TransactionProvider are not deleted atm
            # TODO: do this after activity is parsed along with other saves?

        if old_activity:
            old_activity.delete()

        # TODO: assert title is in xml, for proper OneToOne relation (only on 2.01)

        activity = models.Activity()
        activity.id = id
        activity.default_lang = default_lang
        if hierarchy:
            activity.hierarchy = hierarchy
        activity.xml_source_ref = self.iati_source.ref
        activity.last_updated_datetime = last_updated_datetime
        activity.linked_data_uri = linked_data_uri
        activity.default_currency = default_currency
        activity.iati_standard_version_id = self.VERSION

        # for later reference
        self.default_lang = default_lang

        self.register_model('Activity', activity)
        return element


    def iati_activities__iati_activity__iati_identifier(self, element):
        """
        attributes:

        tag:iati-identifier
        """
        iati_identifier = element.text
            
        if not iati_identifier: raise self.RequiredFieldError("text", "iati_identifier: must contain text")

        activity = self.get_model('Activity')
        activity.iati_identifier = iati_identifier
        # self.register_model('Activity', activity)
        return element

    def iati_activities__iati_activity__reporting_org(self, element):
        """attributes:
        ref:AA-AAA-123456789
        type:40
        secondary-reporter:0

        tag:reporting-org"""
        ref = element.attrib.get('ref')

        if not ref:
            raise self.RequiredFieldError("ref", "reporting-org: ref must be specified")

        normalized_ref = self._normalize(ref)
        org_type = self.get_or_none(codelist_models.OrganisationType, code=element.attrib.get('type'))
        # TODO: should secondary_reporter be false by default?
        secondary_reporter = element.attrib.get('secondary-reporter', False)


        organisation = self.get_or_none(models.Organisation, pk=ref)

        # create an organisation
        if not organisation:

            organisation = organisation_models.Organisation()
            organisation.id = ref
            organisation.organisation_identifier = ref
            organisation.last_updated_datetime = datetime.now()
            organisation.iati_standard_version_id = "2.01"
            organisation.reported_in_iati = False

            organisation_name = organisation_models.OrganisationName()
            organisation_name.organisation = organisation

            self.register_model('Organisation', organisation)
            self.register_model('OrganisationName', organisation_name)

            narratives = element.findall('narrative')
            narratives_text = element.xpath('narrative/text()')

            if len(narratives) > 0:
                for narrative in narratives:
                    self.add_narrative(narrative, organisation_name)
                    organisation.primary_name = self.get_primary_name(narrative, organisation.primary_name)
            else:
                organisation.primary_name = ref


        activity = self.get_model('Activity')
        reporting_organisation = models.ActivityReportingOrganisation()
        reporting_organisation.ref = ref
        reporting_organisation.normalized_ref = normalized_ref
        reporting_organisation.type = org_type  
        reporting_organisation.activity = activity
        reporting_organisation.organisation = organisation
        reporting_organisation.secondary_reporter = self.makeBool(secondary_reporter)

        self.register_model('ActivityReportingOrganisation', reporting_organisation)
    
        return element

    
    def iati_activities__iati_activity__reporting_org__narrative(self, element):
        """attributes:

        tag:narrative
        """
        model = self.get_model('ActivityReportingOrganisation')
        self.add_narrative(element, model)

        return element
    
    def iati_activities__iati_activity__participating_org(self, element):
        """attributes:https://docs.djangoproject.com/en/1.8/topics/migrations/
        ref:BB-BBB-123456789
        role:1
        type:40
    
        tag:participating-org"""
        ref = element.attrib.get('ref', '')
        role = self.get_or_none(codelist_models.OrganisationRole, pk=element.attrib.get('role'))

        # NOTE: strictly taken, the ref should be specified. In practice many reporters don't use them
        # simply because they don't know the ref.
        # if not ref: raise self.RequiredFieldError("ref", "participating-org: ref must be specified")
        if not role:
            raise self.RequiredFieldError("role", "participating-org: role must be specified")

        normalized_ref = self._normalize(ref)
        organisation = self.get_or_none(models.Organisation, pk=ref)
        org_type = self.get_or_none(codelist_models.OrganisationType, code=element.attrib.get('type'))

        activity = self.get_model('Activity')
        participating_organisation = models.ActivityParticipatingOrganisation()
        participating_organisation.ref = ref
        participating_organisation.normalized_ref = normalized_ref
        participating_organisation.type = org_type  
        participating_organisation.activity = activity
        participating_organisation.organisation = organisation
        participating_organisation.role = role

        self.register_model('ActivityParticipatingOrganisation', participating_organisation)

        return element

    
    def iati_activities__iati_activity__participating_org__narrative(self, element):
        """attributes:
    
        tag:narrative"""
        model = self.get_model('ActivityParticipatingOrganisation')
        self.add_narrative(element, model)

        # workaround for IATI ref uniqueness limitation
        model.primary_name = self.get_primary_name(element, model.primary_name)

        return element
    
    def iati_activities__iati_activity__title(self, element):
        """attributes:
    
        tag:title"""
        title_list = self.get_model_list('Title')

        if title_list and len(title_list) > 0:
            raise self.ValidationError("title", "Duplicate titles are not allowed")

        # activity = self.pop_model('Activity')
        activity = self.get_model('Activity')

        title = models.Title()
        title.activity = activity

        # activity.title = title

        # order is important (
        # TODO: change datastructure to handle this case more transparant, like insertBefore or something)
        self.register_model('Title', title)
        # self.register_model('Activity', activity)

    def iati_activities__iati_activity__title__narrative(self, element):
        """attributes:

        tag:narrative"""
        # TODO: make this more clear and not depend on order of things
        # title = self.get_model('Activity', index=-2) # this points to Title
        title = self.get_model('Title') # this points to Title
        self.add_narrative(element, title)
        
        return element

    def iati_activities__iati_activity__description(self, element):
        """attributes:
        type:1
    
        tag:description"""

        description_type_code = element.attrib.get('type', 1)
        description_type = self.get_or_none(codelist_models.Language, code=description_type_code)

        activity = self.get_model('Activity')
        description = models.Description()
        description.activity = activity
        description.type = description_type

        self.register_model('Description', description)
        return element

    def iati_activities__iati_activity__description__narrative(self, element):
        """attributes:
    
        tag:narrative"""
        title = self.get_model('Description')
        self.add_narrative(element, title)
        
        return element

    def iati_activities__iati_activity__other_identifier(self, element):
        """attributes:
        ref:ABC123-XYZ
        type:A1
        tag:other-identifier"""
        identifier = element.attrib.get('ref')
        type = self.get_or_none(models.OtherIdentifierType, code=element.attrib.get('type'))

        if not identifier: raise self.RequiredFieldError("identifier", "other-identifier: identifier is required")
        # TODO: iati docs say type should be required (but can't for backwards compatibility)

        activity = self.get_model('Activity')
        other_identifier = models.OtherIdentifier()
        other_identifier.activity = activity
        other_identifier.identifier=identifier
        other_identifier.type=type

        self.register_model('OtherIdentifier', other_identifier)
        return element

    def iati_activities__iati_activity__other_identifier__owner_org(self, element):
        """attributes:
        ref:AA-AAA-123456789

        tag:owner-org"""
        ref = element.attrib.get('ref')

        if not ref: raise self.RequiredFieldError("identifier", "other-identifier: identifier is required")

        other_identifier = self.get_model('OtherIdentifier')
        other_identifier.owner_ref = ref

        return element

    def iati_activities__iati_activity__other_identifier__owner_org__narrative(self, element):
        """attributes:

        tag:narrative"""
        other_identifier = self.get_model('OtherIdentifier')
        self.add_narrative(element, other_identifier)
        return element

    def iati_activities__iati_activity__activity_status(self, element):
        """attributes:
        code:2

        tag:activity-status"""

        code = element.attrib.get('code')
        activity_status = self.get_or_none(codelist_models.ActivityStatus, code=code)

        if not code: raise self.RequiredFieldError("Code", "activity status: code is required")

        activity = self.get_model('Activity')
        activity.activity_status = activity_status

        return element

    def iati_activities__iati_activity__activity_date(self, element):
        """attributes:
        iso-date:2012-04-15
        type:1

        tag:activity-date"""

        iso_date = self.validate_date(element.attrib.get('iso-date'))
        type_code = self.get_or_none(codelist_models.ActivityDateType, code=element.attrib.get('type'))

        if not iso_date: raise self.RequiredFieldError("iso-date", "activity date: invalid iso-date")
        if not type_code: raise self.RequiredFieldError("Type", "activity date type: type is required")

        activity = self.get_model('Activity')

        activity_date = models.ActivityDate()
        activity_date.iso_date = iso_date
        activity_date.type = type_code
        activity_date.activity = activity

        # to make ordering possible, activity dates are duplicated onto the Activity model
        mapping = {
            '1': 'planned_start',
            '2': 'actual_start',
            '3': 'planned_end',
            '4': 'actual_end'
        }

        if type_code.code in mapping:
            setattr(activity, mapping[type_code.code], iso_date)

        self.register_model('ActivityDate', activity_date)
        return element

    def iati_activities__iati_activity__activity_date__narrative(self, element):
        """attributes:

        tag:narrative"""
        # this is not implemented
        activity_date = self.get_model('ActivityDate')
        self.add_narrative(element, activity_date)
        return element

    def iati_activities__iati_activity__contact_info(self, element):
        """attributes:
        type:1

        tag:contact-info"""
        type_code = self.get_or_none(codelist_models.ContactType, code=element.attrib.get('type'))

        activity = self.get_model('Activity')
        contact_info =  models.ContactInfo()
        contact_info.activity = activity
        contact_info.type = type_code
        self.register_model('ContactInfo', contact_info)

        return element

    def iati_activities__iati_activity__contact_info__organisation(self, element):
        """attributes:

        tag:organisation"""
        contact_info = self.get_model('ContactInfo')
        contact_info_organisation =  models.ContactInfoOrganisation()
        contact_info_organisation.contact_info = contact_info;
        self.register_model('ContactInfoOrganisation', contact_info_organisation)
        return element

    def iati_activities__iati_activity__contact_info__organisation__narrative(self, element):
        """attributes:

        tag:narrative"""
        contact_info_organisation = self.get_model('ContactInfoOrganisation')
        self.add_narrative(element, contact_info_organisation)
        return element

    def iati_activities__iati_activity__contact_info__department(self, element):
        """attributes:

        tag:department"""
        contact_info = self.get_model('ContactInfo')
        contact_info_department =  models.ContactInfoDepartment()
        contact_info_department.contact_info = contact_info

        self.register_model('ContactInfoDepartment', contact_info_department)
         
        return element

    def iati_activities__iati_activity__contact_info__department__narrative(self, element):
        """attributes:

        tag:narrative"""
        contact_info_department = self.get_model('ContactInfoDepartment')
        self.add_narrative(element, contact_info_department)
        return element

    def iati_activities__iati_activity__contact_info__person_name(self, element):
        """attributes:

        tag:person-name"""
        contact_info = self.get_model('ContactInfo')
        contact_info_person_name =  models.ContactInfoPersonName()
        contact_info_person_name.contact_info = contact_info
        self.register_model('ContactInfoPersonName', contact_info_person_name)
         
        return element

    def iati_activities__iati_activity__contact_info__person_name__narrative(self, element):
        """attributes:

        tag:narrative"""
        contact_info_person_name = self.get_model('ContactInfoPersonName')
        self.add_narrative(element, contact_info_person_name)
        return element

    def iati_activities__iati_activity__contact_info__job_title(self, element):
        """attributes:

        tag:job-title"""
        contact_info = self.get_model('ContactInfo')
        contact_info_job_title = models.ContactInfoJobTitle()
        contact_info_job_title.contact_info = contact_info
        self.register_model('ContactInfoJobTitle', contact_info_job_title)
        return element


    def iati_activities__iati_activity__contact_info__job_title__narrative(self, element):
        """attributes:

        tag:narrative"""
        contact_info_job_title = self.get_model('ContactInfoJobTitle')
        self.add_narrative(element, contact_info_job_title)
        return element

    def iati_activities__iati_activity__contact_info__telephone(self, element):
        """attributes:

        tag:telephone"""
        text = element.text

        if not text: raise self.RequiredFieldError("text", "contact_info_telephone: text is required")

        contact_info = self.get_model('ContactInfo')
        contact_info.telephone = text
         
        return element

    def iati_activities__iati_activity__contact_info__email(self, element):
        """attributes:

        tag:email"""
        text = element.text

        if not text: raise self.RequiredFieldError("text", "contact_info_email: text is required")

        contact_info = self.get_model('ContactInfo')
        contact_info.email = text
         
        return element

    def iati_activities__iati_activity__contact_info__website(self, element):
        """attributes:

        tag:website"""
        text = element.text

        if not text: raise self.RequiredFieldError("text", "contact_info_website: text is required")

        contact_info = self.get_model('ContactInfo')
        contact_info.website = text
         
        return element

    def iati_activities__iati_activity__contact_info__mailing_address(self, element):
        """attributes:

        tag:mailing-address"""
        contact_info = self.get_model('ContactInfo')
        contact_info_mailing_address = models.ContactInfoMailingAddress()
        contact_info_mailing_address.contact_info = contact_info
        self.register_model('ContactInfoMailingAddress', contact_info_mailing_address)
         
        return element

    def iati_activities__iati_activity__contact_info__mailing_address__narrative(self, element):
        """attributes:

        tag:narrative"""
        contact_info_mailing_address = self.get_model('ContactInfoMailingAddress')
        self.add_narrative(element, contact_info_mailing_address)
        return element

    def iati_activities__iati_activity__activity_scope(self, element):
        """attributes:
        code:3

        tag:activity-scope"""
        activity_scope = self.get_or_none(codelist_models.ActivityScope, code=element.attrib.get('code'))

        if not activity_scope: raise self.RequiredFieldError("code", "activity_scope: code is required")

        activity = self.get_model('Activity')
        activity.scope = activity_scope
         
        return element

    def iati_activities__iati_activity__recipient_country(self, element):
        """attributes:
        code:AF
        percentage:25

        tag:recipient-country"""

        country = self.get_or_none(Country, code=element.attrib.get('code'))
        percentage = element.attrib.get('percentage')

        if not country: raise self.RequiredFieldError("code", "recipient-country: code is required")

        activity = self.get_model('Activity')
        activity_recipient_country =  models.ActivityRecipientCountry()
        activity_recipient_country.country = country
        activity_recipient_country.activity = activity
        activity_recipient_country.percentage = percentage
         
        self.register_model('ActivityRecipientCountry', activity_recipient_country)

        return element

    def iati_activities__iati_activity__recipient_region(self, element):
        """attributes:
        code:489
        vocabulary:1
        percentage:25

        tag:recipient-region"""
        region = self.get_or_none(Region, code=element.attrib.get('code'))
        vocabulary = self.get_or_none(vocabulary_models.RegionVocabulary, code=element.attrib.get('vocabulary', '1')) # TODO: make defaults more transparant, here: 'OECD-DAC default'
        percentage = element.attrib.get('percentage')

        if not region: raise self.RequiredFieldError("code", "recipient-region: code is required")
        if not vocabulary: raise self.RequiredFieldError("vocabulary", "recipient-region: vocabulary is required")

        activity = self.get_model('Activity')
        activity_recipient_region =  models.ActivityRecipientRegion()
        activity_recipient_region.region = region
        activity_recipient_region.activity = activity
        activity_recipient_region.percentage = percentage
        activity_recipient_region.vocabulary = vocabulary
        self.register_model('ActivityRecipientRegion', activity_recipient_region)
         
        return element

    def iati_activities__iati_activity__location(self, element):
        """attributes:
        ref:AF-KAN

        tag:location"""
        ref = element.attrib.get('ref')

        activity = self.get_model('Activity')
        location =  models.Location()
        location.activity = activity
        location.ref = ref
        # location.adm_code = 'no admin code'

        self.register_model('Location', location)
        return element

    def iati_activities__iati_activity__location__location_reach(self, element):
        """attributes:
        code:1

        tag:location-reach"""
        location_reach = self.get_or_none(codelist_models.GeographicLocationReach, code=element.attrib.get('code'))

        if not location_reach: raise self.RequiredFieldError("code", "location_reach: code is required")

        location = self.get_model('Location')
        location.location_reach = location_reach
         
        return element

    def iati_activities__iati_activity__location__location_id(self, element):
        """attributes:
        vocabulary:G1
        code:1453782

        tag:location-id"""
        code = element.attrib.get('code')
        vocabulary = self.get_or_none(codelist_models.GeographicVocabulary, code=element.attrib.get('vocabulary'))

        if not code: raise self.RequiredFieldError("code", "location_id: code is required")
        if not vocabulary: raise self.RequiredFieldError("vocabulary", "location_id: vocabulary is required")

        location = self.get_model('Location')
        location.location_id_vocabulary = vocabulary
        location.location_id_code = code

        return element

    def iati_activities__iati_activity__location__name(self, element):
        """attributes:

        tag:name"""

        location = self.get_model('Location')
        location_name = models.LocationName()
        location_name.location = location

        self.register_model('LocationName', location_name)
        return element

    def iati_activities__iati_activity__location__name__narrative(self, element):
        """attributes:

        tag:narrative"""
        location_name = self.get_model('LocationName')
        self.add_narrative(element, location_name)
        return element

    def iati_activities__iati_activity__location__description(self, element):
        """attributes:

        tag:description"""
        location = self.get_model('Location')
        location_description = models.LocationDescription()
        location_description.location = location

        self.register_model('LocationDescription', location_description)
        return element

    def iati_activities__iati_activity__location__description__narrative(self, element):
        """attributes:

        tag:narrative"""
        location_description = self.get_model('LocationDescription')
        self.add_narrative(element, location_description)
        return element

    def iati_activities__iati_activity__location__activity_description(self, element):
        """attributes:

        tag:activity-description"""
        location = self.get_model('Location')
        location_activity_description = models.LocationActivityDescription()
        location_activity_description.location = location

        self.register_model('LocationActivityDescription', location_activity_description)
        return element

    def iati_activities__iati_activity__location__activity_description__narrative(self, element):
        """attributes:

        tag:narrative"""
        location_activity_description = self.get_model('LocationActivityDescription')
        self.add_narrative(element, location_activity_description)
        return element

    def iati_activities__iati_activity__location__administrative(self, element):
        """attributes:
        vocabulary:G1
        level:1
        code:1453782

        tag:administrative"""
        # TODO: enforce code is according to specified vocabulary standard?
        # TODO: default level?
        code = element.attrib.get('code')
        vocabulary = self.get_or_none(codelist_models.GeographicVocabulary, code=element.attrib.get('vocabulary'))
        level = element.attrib.get('level')

        if not code: raise self.RequiredFieldError("code", "location_administrative: code is required")
        if not vocabulary: raise self.RequiredFieldError("vocabulary", "location_administrative: vocabulary is required")

        location = self.get_model('Location')
        location_administrative = models.LocationAdministrative()
        location_administrative.location = location
        location_administrative.code = code
        location_administrative.vocabulary = vocabulary
        location_administrative.level = level
         
        self.register_model('LocationAdministrative', location_administrative)

        return element

    def iati_activities__iati_activity__location__point(self, element):
        """attributes:
        srsName:http://www.opengis.net/def/crs/EPSG/0/4326

        tag:point"""
        srs_name = element.attrib.get('srsName')

        # TODO: make this field required?
        # if not srs_name: raise self.RequiredFieldError("srsName", "location_point: srsName is required")
        if not srs_name: srs_name = "http://www.opengis.net/def/crs/EPSG/0/4326"

        location = self.get_model('Location')
        location.point_srs_name = srs_name

        return element

    def iati_activities__iati_activity__location__point__pos(self, element):
        """attributes:

        tag:pos"""
        # TODO: validation of lat/long
        # TODO: Allow for different srid's
        text = element.text

        if not text: raise self.RequiredFieldError("text", "location_point_pos: text is required")

        try: 
            latlong = text.strip().split(' ')
            # geos point = long lat, iati point lat long, hence the latlong[1], latlong[0]
            point = GEOSGeometry(Point(float(latlong[1]), float(latlong[0])), srid=4326)
        except Exception as e:
            raise self.ValidationError("latlong", "either lat or long is not present")

        location = self.get_model('Location')
        location.point_pos = point
        
        return element

    def iati_activities__iati_activity__location__exactness(self, element):
        """attributes:
        code:1

        tag:exactness"""
        code = self.get_or_none(codelist_models.GeographicExactness, code=element.attrib.get('code'))

        if not code: raise self.RequiredFieldError("code", "location_exactness: code is required")

        location = self.get_model('Location')
        location.exactness = code
         
        return element

    def iati_activities__iati_activity__location__location_class(self, element):
        """attributes:
        code:2

        tag:location-class"""
        code = self.get_or_none(codelist_models.GeographicLocationClass, code=element.attrib.get('code'))

        if not code: raise self.RequiredFieldError("code", "location_class: code is required")

        location = self.get_model('Location')
        location.location_class = code
         
        return element

    def iati_activities__iati_activity__location__feature_designation(self, element):
        """attributes:
        code:ADMF

        tag:feature-designation"""
        code = self.get_or_none(codelist_models.LocationType, code=element.attrib.get('code'))

        if not code: raise self.RequiredFieldError("code", "location_feature_designation: code is required")

        location = self.get_model('Location')
        location.feature_designation = code

        return element

    def iati_activities__iati_activity__sector(self, element):
        """attributes:
        code:489
        vocabulary:1
        percentage:25

        tag:recipient-sector"""
        sector = self.get_or_none(models.Sector, code=element.attrib.get('code'))
        vocabulary = self.get_or_none(vocabulary_models.SectorVocabulary, code=element.attrib.get('vocabulary', '1')) # TODO: make defaults more transparant, here: 'OECD-DAC default'
        percentage = element.attrib.get('percentage')

        if not sector: raise self.RequiredFieldError("code", "sector: code is required")
        if not vocabulary: raise self.RequiredFieldError("vocabulary", "sector: vocabulary is required")

        activity = self.get_model('Activity')
        activity_sector =  models.ActivitySector()
        activity_sector.sector = sector
        activity_sector.activity = activity
        activity_sector.percentage = percentage
        activity_sector.vocabulary = vocabulary
        self.register_model('ActivitySector', activity_sector)
         
        return element

    def iati_activities__iati_activity__country_budget_items(self, element):
        """attributes:
        vocabulary:2

        tag:country-budget-items"""
        vocabulary = self.get_or_none(
            vocabulary_models.BudgetIdentifierVocabulary,
            code=element.attrib.get('vocabulary'))

        if not vocabulary: raise self.RequiredFieldError("vocabulary", "country-budget-items: vocabulary is required")

        activity = self.get_model('Activity')
        country_budget_item = models.CountryBudgetItem()
        country_budget_item.activity = activity
        country_budget_item.vocabulary = vocabulary

        self.register_model('CountryBudgetItem', country_budget_item)
        return element

    def iati_activities__iati_activity__country_budget_items__budget_item(self, element):
        """attributes:
        code:1.1.1
        percentage:50

        tag:budget-item"""
        # TODO: Add custom vocabularies
        code = self.get_or_none(codelist_models.BudgetIdentifier, code=element.attrib.get('code')) 
        percentage = element.attrib.get('percentage')

        if not code: raise self.RequiredFieldError("code", "country-budget: code is required")

        country_budget_item = self.get_model('CountryBudgetItem')
        budget_item = models.BudgetItem()
        budget_item.country_budget_item = country_budget_item
        budget_item.code = code
        budget_item.percentage = percentage

        self.register_model('BudgetItem', budget_item)
        return element

    def iati_activities__iati_activity__country_budget_items__budget_item__description(self, element):
        """attributes:

        tag:description"""
        budget_item = self.get_model('BudgetItem')
        budget_item_description = models.BudgetItemDescription()
        budget_item_description.budget_item = budget_item

        self.register_model('BudgetItemDescription', budget_item_description)
        return element

    def iati_activities__iati_activity__country_budget_items__budget_item__description__narrative(self, element):
        """attributes:

        tag:narrative"""
        budget_item_description = self.get_model('BudgetItemDescription')
        self.add_narrative(element, budget_item_description)
        return element

    def iati_activities__iati_activity__policy_marker(self, element):
        """attributes:
        vocabulary:1
        code:2
        significance:3

        tag:policy-marker"""
        # TODO: custom vocabulary (other than 1)
        code = self.get_or_none(codelist_models.PolicyMarker, code=element.attrib.get('code')) 
        vocabulary = self.get_or_none(vocabulary_models.PolicyMarkerVocabulary, code=element.attrib.get('vocabulary')) 
        significance = self.get_or_none(codelist_models.PolicySignificance, code=element.attrib.get('significance')) 

        if not code: raise self.RequiredFieldError("code", "policy-marker: code is required")
        if not vocabulary: raise self.RequiredFieldError("vocabulary", "policy-marker: vocabulary is required")
        if not significance: raise self.RequiredFieldError("significance", "policy-marker: significance is required")

        activity = self.get_model('Activity')
        activity_policy_marker = models.ActivityPolicyMarker()
        activity_policy_marker.activity = activity
        activity_policy_marker.code = code
        activity_policy_marker.vocabulary = vocabulary
        activity_policy_marker.significance = significance

        self.register_model('ActivityPolicyMarker', activity_policy_marker)
        return element

    def iati_activities__iati_activity__policy_marker__narrative(self, element):
        """attributes:

        tag:narrative"""
        activity_policy_marker = self.get_model('ActivityPolicyMarker')
        self.add_narrative(element, activity_policy_marker)
        return element

    def iati_activities__iati_activity__collaboration_type(self, element):
        """attributes:
        code:1

        tag:collaboration-type"""
        code = self.get_or_none(codelist_models.CollaborationType, code=element.attrib.get('code')) 

        if not code: raise self.RequiredFieldError("code", "collaboration-type: code is required")

        activity = self.get_model('Activity')
        activity.collaboration_type = code
         
        return element

    def iati_activities__iati_activity__default_flow_type(self, element):
        """attributes:
        code:10

        tag:default-flow-type"""
        code = self.get_or_none(codelist_models.FlowType, code=element.attrib.get('code')) 

        if not code: raise self.RequiredFieldError("code", "default-flow-type: code is required")

        activity = self.get_model('Activity')
        activity.default_flow_type = code
         
        return element

    def iati_activities__iati_activity__default_finance_type(self, element):
        """attributes:
        code:110

        tag:default-finance-type"""
        code = self.get_or_none(codelist_models.FinanceType, code=element.attrib.get('code')) 

        if not code: raise self.RequiredFieldError("code", "default-flow-type: code is required")

        activity = self.get_model('Activity')
        activity.default_finance_type = code
         
        return element

    def iati_activities__iati_activity__default_aid_type(self, element):
        """attributes:
        code:A01

        tag:default-aid-type"""
        code = self.get_or_none(codelist_models.AidType, code=element.attrib.get('code')) 

        if not code: raise self.RequiredFieldError("code", "default-flow-type: code is required")

        activity = self.get_model('Activity')
        activity.default_aid_type = code
         
        return element

    def iati_activities__iati_activity__default_tied_status(self, element):
        """attributes:
        code:3

        tag:default-tied-status"""
        code = self.get_or_none(codelist_models.TiedStatus, code=element.attrib.get('code')) 

        if not code: raise self.RequiredFieldError("code", "default-tied-status: code is required")

        activity = self.get_model('Activity')
        activity.default_tied_status = code
         
        return element

    def iati_activities__iati_activity__budget(self, element):
        """attributes:
        type:1

        tag:budget"""
        budget_type = self.get_or_none(codelist_models.BudgetType, code=element.attrib.get('type')) 
        activity = self.get_model('Activity')

        # if not budget_type: raise self.RequiredFieldError("type", "budget: type is required")

        budget = models.Budget()
        budget.activity = activity
        budget.type = budget_type

        self.register_model('Budget', budget)
        return element

    def iati_activities__iati_activity__budget__period_start(self, element):
        """attributes:
        iso-date:2014-01-01

        tag:period-start"""
        iso_date = self.validate_date(element.attrib.get('iso-date'))

        if not iso_date: raise self.RequiredFieldError("iso-date", "budget-period-start: iso-date is required")
        budget = self.get_model('Budget')
        budget.period_start = iso_date
         
        return element

    def iati_activities__iati_activity__budget__period_end(self, element):
        """attributes:
        iso-date:2014-12-31

        tag:period-end"""
        iso_date = self.validate_date(element.attrib.get('iso-date'))

        if not iso_date: raise self.RequiredFieldError("iso-date", "budget-period-end: iso-date is required")
        budget = self.get_model('Budget')
        budget.period_end = iso_date
         
        return element

    def iati_activities__iati_activity__budget__value(self, element):
        """attributes:
        currency:EUR
        value-date:2014-01-01

        tag:value"""
        currency = self.get_or_none(models.Currency, code=element.attrib.get('currency'))
        value_date = self.validate_date(element.attrib.get('value-date'))
        value = element.text
        decimal_value = self.guess_number(value)

        if decimal_value is None:
            raise self.RequiredFieldError("value", "budget__value: value is required")

        if value_date is None:
            raise self.RequiredFieldError("value_date", "budget__value_date: value_date is required")

        currency = self._get_currency_or_raise(currency)

        budget = self.get_model('Budget')
        budget.value_string = value
        budget.value = decimal_value
        budget.value_date = value_date
        budget.currency = currency

        budget.xdr_value = convert.currency_from_to(budget.currency_id, 'XDR', budget.value_date, budget.value)
        budget.usd_value = convert.currency_from_to(budget.currency_id, 'USD', budget.value_date, budget.value)
        budget.eur_value = convert.currency_from_to(budget.currency_id, 'EUR', budget.value_date, budget.value)
        budget.gbp_value = convert.currency_from_to(budget.currency_id, 'GBP', budget.value_date, budget.value)
        budget.jpy_value = convert.currency_from_to(budget.currency_id, 'JPY', budget.value_date, budget.value)
        budget.cad_value = convert.currency_from_to(budget.currency_id, 'CAD', budget.value_date, budget.value)

        return element

    def iati_activities__iati_activity__planned_disbursement(self, element):
        """attributes:
        type:1

        tag:planned-disbursement"""
        budget_type = self.get_or_none(codelist_models.BudgetType, code=element.attrib.get('type')) 

        # if not budget_type: raise self.RequiredFieldError("type", "planned-disbursement: type is required")

        activity = self.get_model('Activity')
        planned_disbursement = models.PlannedDisbursement()
        planned_disbursement.activity = activity
        planned_disbursement.budget_type = budget_type

        self.register_model('PlannedDisbursement', planned_disbursement)
         
        return element

    def iati_activities__iati_activity__planned_disbursement__period_start(self, element):
        """attributes:
        iso-date:2014-01-01

        tag:period-start"""
        iso_date = self.validate_date(element.attrib.get('iso-date'))

        if not iso_date:
            raise self.RequiredFieldError("iso-date", "planned-disbursement-period-start:  iso-date is required")

        planned_disbursement = self.get_model('PlannedDisbursement')
        planned_disbursement.period_start = iso_date

        return element

    def iati_activities__iati_activity__planned_disbursement__period_end(self, element):
        """attributes:
        iso-date:2014-12-31

        tag:period-end"""
        iso_date = self.validate_date(element.attrib.get('iso-date'))

        if not iso_date: raise self.RequiredFieldError("iso-date", "planned-disbursement-period-end: iso-date is required")

        planned_disbursement = self.get_model('PlannedDisbursement')
        planned_disbursement.period_end = iso_date

        return element

    def iati_activities__iati_activity__planned_disbursement__value(self, element):
        """attributes:
        currency:EUR
        value-date:2014-01-01

        tag:value"""
        value = element.text

        currency = self.get_or_none(models.Currency, code=element.attrib.get('currency'))
        value_date = self.validate_date(element.attrib.get('value-date'))
        value = element.text
        decimal_value = self.guess_number(value)

        if decimal_value is None:
            raise self.RequiredFieldError("value", "planned_disbursement__value: value is required")

        if value_date is None:
            raise self.RequiredFieldError("value_date", "planned_disbursement__value_date: value_date is required")

        currency = self._get_currency_or_raise(currency)

        planned_disbursement = self.get_model('PlannedDisbursement')
        planned_disbursement.value_string = value
        planned_disbursement.value = decimal_value
        planned_disbursement.value_date = value_date
        planned_disbursement.currency = currency
         
        return element

    def iati_activities__iati_activity__capital_spend(self, element):
        """attributes:
        percentage:88.8

        tag:capital-spend"""
        activity = self.get_model('Activity')
        activity.capital_spend = element.attrib.get('percentage')
         
        return element


    def iati_activities__iati_activity__transaction(self, element):
        """attributes:
        ref:1234

        tag:transaction"""
        ref = element.attrib.get('ref')

        activity = self.get_model('Activity')
        transaction = transaction_models.Transaction()
        transaction.activity = activity
        transaction.ref = ref

        self.register_model('Transaction', transaction)
        return element

    def iati_activities__iati_activity__transaction__transaction_type(self, element):
        """attributes:
        code:1

        tag:transaction-type"""
        transaction_type = self.get_or_none(codelist_models.TransactionType, code=element.attrib.get('code'))

        if not transaction_type:
            raise self.RequiredFieldError("code", "transaction-type: code is required")

        transaction = self.get_model('Transaction')
        transaction.transaction_type = transaction_type

        return element

    def iati_activities__iati_activity__transaction__transaction_date(self, element):
        """attributes:
        iso-date:2012-01-01

        tag:transaction-date"""
        iso_date = self.validate_date(element.attrib.get('iso-date'))

        if not iso_date: raise self.RequiredFieldError("iso-date", "transaction-date: iso-date is required")
        
        transaction = self.get_model('Transaction')
        transaction.transaction_date = iso_date
         
        return element

    def iati_activities__iati_activity__transaction__value(self, element):
        """attributes:
        currency:EUR
        value-date:2012-01-01

        tag:value"""
        currency = self.get_or_none(models.Currency, code=element.attrib.get('currency'))
        value_date = self.validate_date(element.attrib.get('value-date'))
        value = element.text
        decimal_value = self.guess_number(value)

        if decimal_value is None:
            raise self.RequiredFieldError("value", "transaction__value: value is required")

        if value_date is None:
            raise self.RequiredFieldError("value_date", "transaction__value_date: value_date is required")

        currency = self._get_currency_or_raise(currency)

        transaction = self.get_model('Transaction')
        transaction.value_string = value
        transaction.value = decimal_value
        transaction.value_date = value_date
        transaction.currency = currency
        
        transaction.xdr_value = convert.currency_from_to(transaction.currency_id, 'XDR', transaction.value_date, transaction.value)
        transaction.usd_value = convert.currency_from_to(transaction.currency_id, 'USD', transaction.value_date, transaction.value)
        transaction.eur_value = convert.currency_from_to(transaction.currency_id, 'EUR', transaction.value_date, transaction.value)
        transaction.gbp_value = convert.currency_from_to(transaction.currency_id, 'GBP', transaction.value_date, transaction.value)
        transaction.jpy_value = convert.currency_from_to(transaction.currency_id, 'JPY', transaction.value_date, transaction.value)
        transaction.cad_value = convert.currency_from_to(transaction.currency_id, 'CAD', transaction.value_date, transaction.value)

        return element

    def iati_activities__iati_activity__transaction__description(self, element):
        """attributes:

        tag:description"""
        transaction = self.get_model('Transaction')

        description = transaction_models.TransactionDescription()
        description.transaction = transaction

        self.register_model('TransactionDescription', description)

        return element

    def iati_activities__iati_activity__transaction__description__narrative(self, element):
        """attributes:

        tag:narrative"""
        transaction_description = self.get_model('TransactionDescription')
        self.add_narrative(element, transaction_description)
        return element

    def iati_activities__iati_activity__transaction__provider_org(self, element):
        """attributes:
        provider-activity-id:BB-BBB-123456789-1234AA
        ref:BB-BBB-123456789

        tag:provider-org"""
        ref = element.attrib.get('ref', '')
        provider_activity = element.attrib.get('provider-activity-id')

        normalized_ref = self._normalize(ref)
        organisation = self.get_or_none(models.Organisation, pk=ref)

        transaction = self.get_model('Transaction')

        transaction_provider = transaction_models.TransactionProvider()
        transaction_provider.transaction = transaction
        transaction_provider.ref = ref
        transaction_provider.normalized_ref = normalized_ref
        transaction_provider.organisation = organisation
        transaction_provider.provider_activity_ref = provider_activity
        transaction_provider.provider_activity = self.get_or_none(models.Activity, iati_identifier=provider_activity)

        self.register_model('TransactionProvider', transaction_provider)
        return element

    def iati_activities__iati_activity__transaction__provider_org__narrative(self, element):
        """attributes:

        tag:narrative"""
        # TODO: make this more transparant in data structure or handling
        # transaction_provider = self.get_model('Transaction', -2)
        transaction_provider = self.get_model('TransactionProvider')
        self.add_narrative(element, transaction_provider)

        transaction_provider.primary_name = self.get_primary_name(element, transaction_provider.primary_name)

        return element

    def iati_activities__iati_activity__transaction__receiver_org(self, element):
        """attributes:
        receiver-activity-id:AA-AAA-123456789-1234
        ref:AA-AAA-123456789

        tag:receiver-org"""
        ref = element.attrib.get('ref', '')
        receiver_activity = element.attrib.get('receiver-activity-id')

        normalized_ref = self._normalize(ref)
        organisation = self.get_or_none(models.Organisation, pk=ref)

        transaction = self.get_model('Transaction')

        transaction_receiver = transaction_models.TransactionReceiver()
        transaction_receiver.transaction = transaction
        transaction_receiver.ref = ref
        transaction_receiver.normalized_ref = normalized_ref
        transaction_receiver.organisation = organisation
        transaction_receiver.receiver_activity_ref = receiver_activity
        transaction_receiver.receiver_activity = self.get_or_none(models.Activity, iati_identifier=receiver_activity) 

        # update existing  transaction receiver-activity foreign keys happens post_save

        self.register_model('TransactionReceiver', transaction_receiver)
        return element


    def iati_activities__iati_activity__transaction__receiver_org__narrative(self, element):
        """attributes:

        tag:narrative
        """
        # TODO: make this more transparent by changing data structure
        # transaction_receiver = self.get_model('Transaction', -2)
        transaction_receiver = self.get_model('TransactionReceiver')
        self.add_narrative(element, transaction_receiver)

        transaction_receiver.primary_name = self.get_primary_name(element, transaction_receiver.primary_name)

        return element

    def iati_activities__iati_activity__transaction__disbursement_channel(self, element):
        """attributes:
        code:1

        tag:disbursement-channel"""
        disbursement_channel = self.get_or_none(codelist_models.DisbursementChannel, code=element.attrib.get('code'))

        if not disbursement_channel: raise self.RequiredFieldError("code", "disbursement-channel: code must be specified")

        transaction = self.get_model('Transaction')
        transaction.disbursement_channel = disbursement_channel

        return element

    def iati_activities__iati_activity__transaction__sector(self, element):
        """attributes:
        vocabulary:2
        code:111

        tag:sector"""
        sector = self.get_or_none(models.Sector, code=element.attrib.get('code'))
        vocabulary = self.get_or_none(vocabulary_models.SectorVocabulary, code=element.attrib.get('vocabulary', '1')) # TODO: make defaults more transparant, here: 'OECD-DAC default'

        if not sector: raise self.RequiredFieldError("code", "transaction-sector: code is required")
        if not vocabulary: raise self.RequiredFieldError("vocabulary", "transaction-sector: vocabulary is required")

        transaction = self.get_model('Transaction')
        transaction_sector = transaction_models.TransactionSector()
        transaction_sector.transaction = transaction
        transaction_sector.sector = sector
        transaction_sector.vocabulary = vocabulary
        transaction_sector.percentage = 100
        transaction_sector.reported_on_transaction = True

        self.register_model('TransactionSector', transaction_sector)
        return element

    def iati_activities__iati_activity__transaction__recipient_country(self, element):
        """attributes:
        code:AF

        tag:recipient-country"""
        country = self.get_or_none(Country, code=element.attrib.get('code'))

        if not country: raise self.RequiredFieldError("code", "transaction-recipient-country: code is required")

        transaction = self.get_model('Transaction')
        transaction_country = transaction_models.TransactionRecipientCountry()
        transaction_country.transaction = transaction
        transaction_country.country = country
        transaction_country.percentage = 100
        transaction_country.reported_on_transaction = True

        self.register_model('TransactionRecipientCountry', transaction_country)
        return element

    def iati_activities__iati_activity__transaction__recipient_region(self, element):
        """attributes:
        code:456
        vocabulary:1

        tag:recipient-region"""

        region = self.get_or_none(Region, code=element.attrib.get('code'))
        # TODO: make defaults more transparant, here: 'OECD-DAC default'
        vocabulary = self.get_or_none(vocabulary_models.RegionVocabulary, code=element.attrib.get('vocabulary', '1'))

        if not region: raise self.RequiredFieldError("code", "recipient-region: code is required")
        if not vocabulary: raise self.RequiredFieldError("vocabulary", "recipient-region: vocabulary is required")

        transaction = self.get_model('Transaction')
        transaction_recipient_region = transaction_models.TransactionRecipientRegion()
        transaction_recipient_region.transaction = transaction
        transaction_recipient_region.region = region
        transaction_recipient_region.vocabulary = vocabulary
        transaction_recipient_region.percentage = 100
        transaction_recipient_region.reported_on_transaction = True

        transaction = self.register_model('TransactionRecipientRegion', transaction_recipient_region)
        return element

    def iati_activities__iati_activity__transaction__flow_type(self, element):
        """attributes:
        code:10

        tag:flow-type"""
        flow_type = self.get_or_none(codelist_models.FlowType, code=element.attrib.get('code'))

        if not flow_type:
            flow_type = self.get_model('Activity').flow_type
            if not flow_type: raise self.RequiredFieldError("code", "transaction-flow-type: code is required")

        transaction = self.get_model('Transaction')
        transaction.flow_type = flow_type
        return element

    def iati_activities__iati_activity__transaction__finance_type(self, element):
        """attributes:
        code:110

        tag:finance-type"""
        finance_type = self.get_or_none(codelist_models.FinanceType, code=element.attrib.get('code'))

        if not finance_type:
            finance_type = self.get_model('Activity').finance_type
            if not finance_type: raise self.RequiredFieldError("code", "transaction-finance-type: code is required")

        transaction = self.get_model('Transaction')
        transaction.finance_type = finance_type

        return element

    def iati_activities__iati_activity__transaction__aid_type(self, element):
        """attributes:
        code:A01

        tag:aid-type"""
        aid_type = self.get_or_none(codelist_models.AidType, code=element.attrib.get('code'))

        if not aid_type:
            aid_type = self.get_model('Activity').aid_type
            if not aid_type: raise self.RequiredFieldError("code", "transaction-aid-type: code is required")

        transaction = self.get_model('Transaction')
        transaction.aid_type = aid_type

        return element

    def iati_activities__iati_activity__transaction__tied_status(self, element):
        """attributes:
        code:3

        tag:tied-status"""
        tied_status = self.get_or_none(codelist_models.TiedStatus, code=element.attrib.get('code'))

        if not tied_status:
            tied_status = self.get_model('Activity').tied_status
            if not tied_status: raise self.RequiredFieldError("code", "transaction-tied-status: code is required")

        transaction = self.get_model('Transaction')
        transaction.tied_status = tied_status
        return element

    def iati_activities__iati_activity__document_link(self, element):
        """attributes:
        format:application/vnd.oasis.opendocument.text
        url:http:www.example.org/docs/report_en.odt

        tag:document-link"""
        url = element.attrib.get('url')
        file_format = self.get_or_none(codelist_models.FileFormat, code=element.attrib.get('format'))

        if not url: raise self.RequiredFieldError("url", "document_link: url is required")

        activity = self.get_model('Activity')
        document_link = models.DocumentLink()
        document_link.activity = activity
        document_link.url = url
        document_link.file_format = file_format

        self.register_model('DocumentLink', document_link)
        return element


    def iati_activities__iati_activity__document_link__title(self, element):
        """attributes:

        tag:title"""
        document_link = self.get_model('DocumentLink')
        document_link_title = models.DocumentLinkTitle()
        document_link_title.document_link = document_link

        self.register_model('DocumentLinkTitle', document_link_title)
         
        return element

    def iati_activities__iati_activity__document_link__title__narrative(self, element):
        """attributes:

        tag:narrative"""
        document_link_title = self.get_model('DocumentLinkTitle')
        self.add_narrative(element, document_link_title)
        return element

    def iati_activities__iati_activity__document_link__category(self, element):
        """attributes:
        code:A01

        tag:category"""
        category = self.get_or_none(codelist_models.DocumentCategory, code=element.attrib.get('code')) 

        if not category: raise self.RequiredFieldError("code", "document-link-category: code is required")

        document_link = self.get_model('DocumentLink')
        document_link_category = models.DocumentLinkCategory()
        document_link_category.document_link = document_link
        document_link_category.category = category

        self.register_model('DocumentLinkCategory', document_link_category)
        return element

    def iati_activities__iati_activity__document_link__language(self, element):
        """attributes:
        code:en

        tag:language"""
        language = self.get_or_none(codelist_models.Language, code=element.attrib.get('code'))

        if not language: raise self.RequiredFieldError("language", "document-link: code is required")

        document_link = self.get_model('DocumentLink')
        document_link_language = models.DocumentLinkLanguage()
        document_link_language.document_link = document_link
        document_link_language.language = language

        self.register_model('DocumentLinkLanguage', document_link_language)
        return element

    def iati_activities__iati_activity__related_activity(self, element):
        """attributes:
        ref:AA-AAA-123456789-6789
        type:1

        tag:related-activity"""
        related_activity_type = self.get_or_none(codelist_models.RelatedActivityType, code=element.attrib.get('type')) 
        ref = element.attrib.get('ref')

        if not related_activity_type: raise self.RequiredFieldError("type", "related-activity: type is required")
        if not ref: raise self.RequiredFieldError("ref", "related-activity: ref is required")

        activity = self.get_model('Activity')
        related_activity = models.RelatedActivity()
        related_activity.current_activity = activity # TODO: remove this field?
        related_activity.ref_activity = self.get_or_none(models.Activity, iati_identifier=ref)
        related_activity.ref = ref
        related_activity.type = related_activity_type

        # update existing related activity foreign keys, happens post save

        self.register_model('RelatedActivity', related_activity)
        return element

    # """attributes:
    # name:Project Status
    # value:7
    # iati-equivalent:activity-status

    # tag:legacy-data"""
    # def iati_activities__iati_activity__legacy_data(self, element):
    #     model = self.get_func_parent_model()
    #     legacy_data = models.LegacyData()
    #     legacy_data.activity = model
    #     legacy_data.name = element.attrib.get('name')
    #     legacy_data.value = element.attrib.get('value')
    #     legacy_data.iati_equivalent = element.attrib.get('iati-equivalent')
    #     legacy_data.save()
    #     return element

    # """attributes:
    # attached:1

    # tag:conditions"""
    # def iati_activities__iati_activity__conditions(self, element):
    #     activity = self.get_model('Activity')
    #     activity.has_conditions = self.makeBool(element.attrib.get('attached'))

    #     return element

    # """attributes:
    # type:1

    # tag:condition"""
    # def iati_activities__iati_activity__conditions__condition(self, element):
    #     model = self.get_func_parent_model()
    #     condition = models.Condition()
    #     condition.activity = model
    #     condition.type = self.cached_db_call(models.ConditionType,element.attrib.get('type'))
    #     self.set_func_model(condition)
    #     return element

    # """attributes:

    # tag:narrative"""
    # def iati_activities__iati_activity__conditions__condition__narrative(self, element):
    #     activity_date = self.get_model('ActivityDate')
    #     self.add_narrative(element, activity_date)
    #     return element

    # """attributes:
    # type:1
    # aggregation-status:1

    # tag:result"""
    def iati_activities__iati_activity__result(self, element):
        result_type = self.get_or_none(codelist_models.ResultType, code=element.attrib.get('type')) 
        aggregation_status = element.attrib.get('aggregation-status')

        if not result_type: raise self.RequiredFieldError("result_type", "result: result_type is required")

        activity = self.get_model('Activity')
        result = models.Result()
        result.activity = activity
        result.type = result_type
        result.aggregation_status = self.makeBool(aggregation_status)

        self.register_model('Result', result)
        return element

    # """attributes:

    # tag:title"""
    def iati_activities__iati_activity__result__title(self, element):
        result = self.get_model('Result')
        result_title = models.ResultTitle()
        result_title.result = result

        self.register_model('ResultTitle', result_title)
        return element

    def iati_activities__iati_activity__result__title__narrative(self, element):
        title = self.get_model('ResultTitle') # this points to Title
        self.add_narrative(element, title)

        return element

    # """attributes:

    # tag:description"""
    def iati_activities__iati_activity__result__description(self, element):
        result = self.get_model('Result')
        result_description = models.ResultDescription()
        result_description.result = result

        self.register_model('ResultDescription', result_description)
        return element

    # """attributes:

    # tag:narrative"""
    def iati_activities__iati_activity__result__description__narrative(self, element):
        description = self.get_model('ResultDescription') # this points to Description
        self.add_narrative(element, description)

        return element

    # """attributes:
    # measure:1
    # ascending:1

    # tag:indicator"""
    def iati_activities__iati_activity__result__indicator(self, element):
        measure = self.get_or_none(codelist_models.IndicatorMeasure, code=element.attrib.get('measure')) 
        ascending = element.attrib.get('ascending', '1')

        if not measure: raise self.RequiredFieldError("measure", "result_indicator: measure is required")

        result = self.get_model('Result')
        result_indicator = models.ResultIndicator()
        result_indicator.result = result
        result_indicator.measure = measure
        result_indicator.ascending = self.makeBool(ascending)

        self.register_model('ResultIndicator', result_indicator)
        return element

    # """attributes:

    # tag:title"""
    def iati_activities__iati_activity__result__indicator__title(self, element):
        result_indicator = self.get_model('ResultIndicator')
        result_indicator_title = models.ResultIndicatorTitle()
        result_indicator_title.result_indicator = result_indicator

        self.register_model('ResultIndicatorTitle', result_indicator_title)
        return element

    # """attributes:

    # tag:narrative"""
    def iati_activities__iati_activity__result__indicator__title__narrative(self, element):
        title = self.get_model('ResultIndicatorTitle') # this points to Title
        self.add_narrative(element, title)

        return element

    # """attributes:

    # tag:description"""
    def iati_activities__iati_activity__result__indicator__description(self, element):
        result_indicator = self.get_model('ResultIndicator')
        result_indicator_description = models.ResultIndicatorDescription()
        result_indicator_description.result_indicator = result_indicator

        self.register_model('ResultIndicatorDescription', result_indicator_description)
        return element

    # """attributes:

    # tag:narrative"""
    def iati_activities__iati_activity__result__indicator__description__narrative(self, element):
        description = self.get_model('ResultIndicatorDescription')
        self.add_narrative(element, description)

        return element

    # """attributes:
    # year:2012
    # value:10

    # tag:baseline"""
    def iati_activities__iati_activity__result__indicator__baseline(self, element):
        year = element.attrib.get('year')
        value = element.attrib.get('value')

        if not year: raise self.RequiredFieldError("year", "result_indicator_baseline: year is required")
        if not value: raise self.RequiredFieldError("value", "result_indicator_baseline: value is required")

        result_indicator = self.pop_model('ResultIndicator')
        result_indicator.baseline_year = int(year)
        result_indicator.baseline_value = value

        self.register_model('ResultIndicator', result_indicator)
        return element

    # """attributes:

    # tag:comment"""
    def iati_activities__iati_activity__result__indicator__baseline__comment(self, element):
        result_indicator = self.get_model('ResultIndicator')
        result_indicator_baseline_comment = models.ResultIndicatorBaselineComment()
        result_indicator_baseline_comment.result_indicator = result_indicator

        self.register_model('ResultIndicatorBaselineComment', result_indicator_baseline_comment)
        return element

    # """attributes:

    # tag:narrative"""
    def iati_activities__iati_activity__result__indicator__baseline__comment__narrative(self, element):
        baseline_comment = self.get_model('ResultIndicatorBaselineComment')
        self.add_narrative(element, baseline_comment)

        return element

    # """attributes:

    # tag:period"""
    def iati_activities__iati_activity__result__indicator__period(self, element):
        result_indicator = self.get_model('ResultIndicator')
        result_indicator_period = models.ResultIndicatorPeriod()
        result_indicator_period.result_indicator = result_indicator

        self.register_model('ResultIndicatorPeriod', result_indicator_period)
        return element

    # """attributes:
    # iso-date:2013-01-01

    # tag:period-start"""
    def iati_activities__iati_activity__result__indicator__period__period_start(self, element):
        iso_date = self.validate_date(element.attrib.get('iso-date'))

        if not iso_date: raise self.RequiredFieldError("iso-date", "result_indicator_period_period_start: iso-date is required")

        result_indicator_period = self.pop_model('ResultIndicatorPeriod')
        result_indicator_period.period_start = iso_date

        self.register_model('ResultIndicatorPeriod', result_indicator_period)
        return element

    # """attributes:
    # iso-date:2013-03-31

    # tag:period-end"""
    def iati_activities__iati_activity__result__indicator__period__period_end(self, element):
        iso_date = self.validate_date(element.attrib.get('iso-date'))

        if not iso_date: raise self.RequiredFieldError("iso-date", "result_indicator_period_period_end: iso-date is required")

        result_indicator_period = self.pop_model('ResultIndicatorPeriod')
        result_indicator_period.period_end = iso_date

        self.register_model('ResultIndicatorPeriod', result_indicator_period)
        return element

    # """attributes:
    # value:10

    # tag:target"""
    def iati_activities__iati_activity__result__indicator__period__target(self, element):
        value = element.attrib.get('value')

        if not value: raise self.RequiredFieldError("value", "result_indicator_period_target: value is required")

        result_indicator_period = self.pop_model('ResultIndicatorPeriod')
        result_indicator_period.target = value

        self.register_model('ResultIndicatorPeriod', result_indicator_period)
        return element

    # """attributes:

    # tag:comment"""
    def iati_activities__iati_activity__result__indicator__period__target__comment(self, element):
        result_indicator_period = self.get_model('ResultIndicatorPeriod')
        result_indicator_period_target_comment = models.ResultIndicatorPeriodTargetComment()
        result_indicator_period_target_comment.result_indicator_period = result_indicator_period

        self.register_model('ResultIndicatorPeriodTargetComment', result_indicator_period_target_comment)
        return element

    # """attributes:

    # tag:narrative"""
    def iati_activities__iati_activity__result__indicator__period__target__comment__narrative(self, element):
        period_target_comment = self.get_model('ResultIndicatorPeriodTargetComment')
        self.add_narrative(element, period_target_comment)

        return element

    # """attributes:
    # value:11

    # tag:actual"""
    def iati_activities__iati_activity__result__indicator__period__actual(self, element):
        value = element.attrib.get('value')

        if not value: raise self.RequiredFieldError("value", "result_indicator_period_actual: value is required")

        result_indicator_period = self.pop_model('ResultIndicatorPeriod')
        result_indicator_period.actual = value

        self.register_model('ResultIndicatorPeriod', result_indicator_period)
        return element

    # """attributes:

    # tag:comment"""
    def iati_activities__iati_activity__result__indicator__period__actual__comment(self, element):
        result_indicator_period = self.get_model('ResultIndicatorPeriod')
        result_indicator_period_actual_comment = models.ResultIndicatorPeriodActualComment()
        result_indicator_period_actual_comment.result_indicator_period = result_indicator_period

        self.register_model('ResultIndicatorPeriodActualComment', result_indicator_period_actual_comment)
        return element

    # """attributes:

    # tag:narrative"""
    def iati_activities__iati_activity__result__indicator__period__actual__comment__narrative(self, element):
        period_actual_comment = self.get_model('ResultIndicatorPeriodActualComment')
        self.add_narrative(element, period_actual_comment)

        return element

    # """attributes:

    # tag:crs-add"""
    # def iati_activities__iati_activity__crs_add(self, element):
    #     model = self.get_func_parent_model()
    #     crs_add = models.CrsAdd()
    #     crs_add.activity = model
    #     self.set_func_model(crs_add)
         
    #     return element

    # """attributes:
    # code:1
    # significance:1

    # tag:other-flags"""
    # def iati_activities__iati_activity__crs_add__other_flags(self, element):
    #     model = self.get_func_parent_model()
    #     crs_other_flags = models.CrsAddOtherFlags()
    #     crs_other_flags.crs_add = model
    #     crs_other_flags.other_flags =  self.cached_db_call(models.OtherFlags,element.attrib.get('code'))
    #     crs_other_flags.significance = element.attrib.get('significance')
    #     crs_other_flags.save()
    #     return element

    # """attributes:
    # rate-1:4
    # rate-2:3

    # tag:loan-terms"""
    # def iati_activities__iati_activity__crs_add__loan_terms(self, element):
    #     model = self.get_func_parent_model()
    #     add_loan_terms = models.CrsAddLoanTerms()
    #     add_loan_terms.crs_add = model
    #     add_loan_terms.rate_1 = element.attrib.get('rate-1')
    #     add_loan_terms.rate_2 = element.attrib.get('rate-2')
    #     self.set_func_model(add_loan_terms)
    #     return element

    # """attributes:
    # code:1

    # tag:repayment-type"""
    # def iati_activities__iati_activity__crs_add__loan_terms__repayment_type(self, element):
    #     model = self.get_func_parent_model()
    #     model.repayment_type = self.cached_db_call(models.LoanRepaymentType,element.attrib.get('code'))

         
    #     return element

    # """attributes:
    # code:4

    # tag:repayment-plan"""
    # def iati_activities__iati_activity__crs_add__loan_terms__repayment_plan(self, element):
    #     model = self.get_func_parent_model()
    #     model.repayment_plan = self.cached_db_call(models.LoanRepaymentPeriod,element.attrib.get('code'))

    #     return element

    # """attributes:
    # iso-date:2013-09-01

    # tag:commitment-date"""
    # def iati_activities__iati_activity__crs_add__loan_terms__commitment_date(self, element):
    #     model = self.get_func_parent_model()
    #     model.commitment_date = self.validate_date(element.attrib.get('iso-date'))
    #     return element

    # """attributes:
    # iso-date:2014-01-01

    # tag:repayment-first-date"""
    # def iati_activities__iati_activity__crs_add__loan_terms__repayment_first_date(self, element):
    #     model = self.get_func_parent_model()
    #     model.repayment_first_date = self.validate_date(element.attrib.get('iso-date'))

    # """attributes:
    # iso-date:2020-12-31

    # tag:repayment-final-date"""
    # def iati_activities__iati_activity__crs_add__loan_terms__repayment_final_date(self, element):
    #     model = self.get_func_parent_model()
    #     model.repayment_final_date = self.validate_date(element.attrib.get('iso-date'))
    #     return element

    # """attributes:
    # year:2014
    # currency:GBP
    # value-date:2013-05-24

    # tag:loan-status"""
    # def iati_activities__iati_activity__crs_add__loan_status(self, element):
    #     model = self.get_func_parent_model()
    #     crs_loan_status = models.CrsAddLoanStatus()
    #     crs_loan_status.crs_add = model
    #     crs_loan_status.year = element.attrib.get('year')
    #     crs_loan_status.currency = self.cached_db_call(models.Currency,element.attrib.get('currency'))
    #     crs_loan_status.value_date =  self.validate_date(element.attrib.get('value-date'))
    #     self.set_func_model(crs_loan_status)
    #     return element

    # """attributes:

    # tag:interest-received"""
    # def iati_activities__iati_activity__crs_add__loan_status__interest_received(self, element):
    #     model = self.get_func_parent_model()
    #     model.interest_received = element.text
    #     return element

    # """attributes:

    # tag:principal-outstanding"""
    # def iati_activities__iati_activity__crs_add__loan_status__principal_outstanding(self, element):
    #     model = self.get_func_parent_model()
    #     model.principal_outstanding = element.text
    #     return element

    # """attributes:

    # tag:principal-arrears"""
    # def iati_activities__iati_activity__crs_add__loan_status__principal_arrears(self, element):
    #     model = self.get_func_parent_model()
    #     model.principal_arrears = element.text
    #     return element

    # """attributes:

    # tag:interest-arrears"""
    # def iati_activities__iati_activity__crs_add__loan_status__interest_arrears(self, element):
    #     model = self.get_func_parent_model()
    #     model.interest_arrears = element.text
    #     return element

    # """attributes:
    # extraction-date:2014-05-06
    # priority:1
    # phaseout-year:2016

    # tag:fss"""
    # def iati_activities__iati_activity__fss(self, element):
    #     model = self.get_func_parent_model()
    #     fss = models.Fss()
    #     fss.activity = model
    #     fss.year = element.attrib.get('phaseout-year')
    #     fss.extraction_date = self.validate_date(element.attrib.get('extraction-date'))
    #     self.set_func_model(fss)
    #     return element

    # """attributes:
    # year:2014
    # value-date:2013-07-03
    # currency:GBP

    # tag:forecast"""
    # def iati_activities__iati_activity__fss__forecast(self, element):
    #     model = self.get_func_parent_model()
    #     fss_forecast = models.FssForecast()
    #     fss_forecast.fss = model
    #     fss_forecast.year = element.attrib.get('year')
    #     fss_forecast.value_date = self.validate_date(element.attrib.get('value-date'))
    #     fss_forecast.currency = self.cached_db_call(models.Currency, element.attrib.get('currency'))
    #     return element

    def post_save_models(self):
        """Perform all actions that need to happen after a single activity's been parsed."""
        activity = self.get_model('Activity')
        if not activity:
            return False

        post_save.set_related_activities(activity)
        post_save.set_transaction_provider_receiver_activity(activity)
        post_save.set_derived_activity_dates(activity)
        post_save.set_activity_aggregations(activity)
        post_save.update_activity_search_index(activity)
        post_save.set_country_region_transaction(activity)
        post_save.set_sector_transaction(activity)

    def post_save_file(self, xml_source):
        """Perform all actions that need to happen after a single IATI source's been parsed.

        Keyword arguments:
        xml_source -- the IatiXmlSource object of the current source
        """
        self.delete_removed_activities(xml_source.ref)

    def delete_removed_activities(self, xml_source_ref):
        """ Delete activities that were not found in the XML source any longer

        Keyword arguments:
        xml_source_ref -- the IatiXmlSource object PK (ref) of the current source

        Used variables:
        activity.last_updated_model -- the datetime at which this activity was last saved
        self.parse_start_datetime -- the datetime at which parsing this source started
        """
        models.Activity.objects.filter(
            xml_source_ref=xml_source_ref,
            last_updated_model__lt=self.parse_start_datetime).delete()

