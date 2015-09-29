from IATI_2_01 import Parse as IATI_201_Parser

from iati import models
from iati_codelists import models as codelist_models

class Parse(IATI_201_Parser):

    #version of iati standard
    VERSION = '1.05'
    
    activity_date_type_mapping = {
        "start-planned": "1",
        "start-actual": "2",
        "end-planned": "3",
        "end-actual": "4",
    }

    sector_vocabulary_trans = {
        'ADT': 1,
        'COFOG': 2,
        'DAC': 3,
        'DAC-3': 4,
        'ISO': 5,
        'NACE': 6,
        'NTEE': 7,
        'WB': 8,
        'RO': 99,
    }

    transaction_type_trans = {
        'IF': 1,
        'C': 2,
        'D': 3,
        'E': 4,
        'IR': 5,
        'LR': 6,
        'R': 7,
        'QP': 8,
        'Q3': 9,
        'CG': 10
    }

    def add_narrative_105(self, text, parent):
        # lang = self.default_lang
        default_lang = self.default_lang
        lang = element.attrib.get('{http://www.w3.org/XML/1998/namespace}lang', default_lang)
        language = self.get_or_none(codelist_models.Language, code=lang)

        if not language: raise self.RequiredFieldError("language")
        if not text: raise self.RequiredFieldError("text")
        if not parent: raise self.RequiredFieldError("parent")

        narrative = models.Narrative()
        narrative.language = language
        narrative.content = text
        narrative.iati_identifier = self.iati_identifier # TODO: we need this?
        narrative.parent_object = parent

        self.register_model('Narrative', narrative)

    '''atributes:
    ref:AA-AAA-123456789
    type:21

    tag:reporting-org'''
    def iati_activities__iati_activity__reporting_org(self,element):
        super(Parse, self).iati_activities__iati_activity__reporting_org(element)

        ActivityReportingOrganisation = self.get_model('ActivityReportingOrganisation')
        self.add_narrative_105(element.text, activityReportingOrganisation)

        return element

    '''atributes:
    ref:BB-BBB-123456789
    role:Funding
    type:40

    tag:participating-org'''
    def iati_activities__iati_activity__participating_org(self,element):

        role_name = element.attrib.get('role')
        role = self.get_or_none(codelist_models.OrganisationRole, name=role_name)

        if not role: raise self.RequiredFieldError("role", "participating-org: role must be specified")

        element.attrib['role'] = role.code

        super(Parse, self).iati_activities__iati_activity__participating_org(element)

        ActivityParticipatingOrganisation = self.get_model('ActivityParticipatingOrganisation')
        self.add_narrative_105(element.text, activityParticipatingOrganisation)

        return element

    '''atributes:
    ref:ABC123-XYZ
    owner-name:A1
    tag:other-identifier'''
    def iati_activities__iati_activity__other_identifier(self, element):
        identifier = element.text
        owner_ref = element.attrib.get('owner-ref')
        owner_name = element.attrib.get('owner-name')

        if not identifier: raise self.RequiredFieldError("identifier", "other-identifier: identifier is required")
        if not (owner_ref or owner_name): raise self.RequiredFieldError("owner_ref", "Either owner_ref or owner_name must be set")

        activity = self.get_model('Activity')

        other_identifier = models.OtherIdentifier()
        other_identifier.activity = activity
        other_identifier.identifier=identifier
        other_identifier.owner_ref=owner_ref

        self.add_narrative_105(owner_name, other_identifier)
        self.register_model('OtherIdentifier', other_identifier)

        return element

    '''atributes:

    tag:title'''
    def iati_activities__iati_activity__title(self, element):
        text = element.text
        
        if not text: raise self.RequiredFieldError("text", "text is required")

        activity = self.get_model('Activity')
        title = models.Title()
        title.activity = activity

        self.add_narrative_105(text, title)
        self.register_model('Title', title)

        return element

    '''atributes:
    type:1

    tag:description'''
    def iati_activities__iati_activity__description(self,element):
        text = element.text
        description_type_code = element.attrib.get('type', 1)

        if not text: raise self.RequiredFieldError("text", "text is required")

        description_type = self.get_or_none(codelist_models.DescriptionType, code=description_type_code)

        activity = self.get_model('Activity')
        description = models.Description()
        description.activity = activity
        description.type = description_type

        self.add_narrative_105(element.text, description)
        self.register_model('Description', description)

        return element

    '''atributes:
    iso-date:2012-04-15
    type:1

    tag:activity-date'''
    def iati_activities__iati_activity__activity_date(self, element):
        # TODO: should iati Rules be checked? http://iatistandard.org/201/activity-standard/iati-activities/iati-activity/activity-date/
        type_name = element.attrib.get('type')
        type_code = self.activity_date_type_mapping.get(type_name)

        if not type_code: raise self.RequiredFieldError("type", "activity_date: type is required")

        element.attrib['type'] = type_code

        super(Parse, self).iati_activities__iati_activity__activity_date(element)

        activity_date = self.get_model('ActivityDate')
        self.add_narrative(element, activity_date)

        return element

    '''atributes:
    tag:organisation'''
    def iati_activities__iati_activity__contact_info(self, element):
        model = self.get_func_parent_model()
        contactInfoOrganisation = models.ContactInfoOrganisation()
        contactInfoOrganisation.ContactInfo = model
        self.add_narrative_105(element.text, contactInfoOrganisation)
        #store element 
        return element

    '''atributes:
    tag:organisation'''
    def iati_activities__iati_activity__contact_info__organisation(self, element):
        model = self.get_func_parent_model()
        contactInfoOrganisation = models.ContactInfoOrganisation()
        contactInfoOrganisation.ContactInfo = model
        self.add_narrative_105(element.text, contactInfoOrganisation)
        #store element 
        return element

    '''atributes:

    tag:person-name'''
    def iati_activities__iati_activity__contact_info__person_name(self, element):
        model = self.get_func_parent_model()
        contactInfoPersonName =  models.ContactInfoPersonName()
        contactInfoPersonName.ContactInfo = model
        self.add_narrative_105(element.text,contactInfoPersonName)
        #store element 
        return element

    '''atributes:

    tag:job-title'''
    def iati_activities__iati_activity__contact_info__job_title(self, element):
        model = self.get_func_parent_model()

        contact_info_job_title =  models.ContactInfoJobTitle()
        contact_info_job_title.ContactInfo = model
        self.add_narrative_105(element.text, contact_info_job_title)
        #store element 
        return element


    '''atributes:

    tag:mailing-address'''
    def iati_activities__iati_activity__contact_info__mailing_address(self,element):
        model = self.get_func_parent_model()
        contactInfoMailingAddress = models.ContactInfoMailingAddress()
        contactInfoMailingAddress.ContactInfo = model
        self.add_narrative_105(element.text,contactInfoMailingAddress)
        #store element 
        return element


    '''atributes:

    tag:name'''
    def iati_activities__iati_activity__location__name(self,element):
        model = self.get_func_parent_model()
        location_name = models.LocationName()
        location_name.location = model
        self.add_narrative_105(element.text,location_name)
        return element

    '''atributes:

    tag:description'''
    def iati_activities__iati_activity__location__description(self,element):
        model = self.get_func_parent_model()
        location_description = models.LocationDescription()
        location_description.location  = model
        self.add_narrative_105(element.text,location_description)
        #store element 
        return element

    '''atributes:

    tag:activity-description'''
    def iati_activities__iati_activity__location__activity_description(self,element):
        model = self.get_func_parent_model()
        location_activity_description = models.LocationActivityDescription()
        location_activity_description.location  = model
        self.add_narrative_105(element.text,location_activity_description)
        #store element 
        return element


    # '''atributes:
    # code:111
    # vocabulary:DAC

    # tag:sector'''
    # def iati_activities__iati_activity__sector(self,element):
    #     model = self.get_func_parent_model()
    #     sector = models.Sector()
    #     sector.activity = model
    #     sector.code = element.attrib.get('code')
    #     sector.vocabulary = self.cached_db_call(models.Vocabulary,self.sector_vocabulary_trans.get(element.attrib.get('vocabulary')))
    #     sector.save()
         
    #     return element

    '''atributes:

    tag:description'''
    def iati_activities__iati_activity__country_budget_items__budget_item__description(self,element):
        model = self.get_func_parent_model()
        budget_item_description = models.BudgetItemDescription()
        budget_item_description.budget_item = model
        self.add_narrative_105(element.text,budget_item_description)
        return element

    '''atributes:
    vocabulary:1
    code:2
    significance:3

    tag:policy-marker'''
    def iati_activities__iati_activity__policy_marker(self,element):
        model = self.get_func_parent_model()
         
        activity_policy_marker = models.ActivityPolicyMarker()
        activity_policy_marker.activity = model
        activity_policy_marker.policy_marker = self.cached_db_call(models.PolicyMarker,element.attrib.get('code'))
        activity_policy_marker.vocabulary = self.cached_db_call(models.Vocabulary,element.attrib.get('vocabulary'))
        activity_policy_marker.policy_significance = self.cached_db_call(models.PolicySignificance,element.attrib.get('significance'))
        activity_policy_marker.code = element.attrib.get('code')
        self.add_narrative_105(element.text,activity_policy_marker)
        activity_policy_marker.save()
        return element

    '''atributes:

    tag:description'''
    def iati_activities__iati_activity__transaction__description(self,element):
        model = self.get_func_parent_model()
        description = models.TransactionDescription()
        description.transaction = model
        self.add_narrative_105(element.text,description)
        return element


    '''atributes:
    provider-activity-id:BB-BBB-123456789-1234AA
    ref:BB-BBB-123456789

    tag:provider-org'''
    def iati_activities__iati_activity__transaction__provider_org(self, element):
        model = self.get_func_parent_model()
        model.provider_activity_id = element.attrib.get('provider-activity-id')
        provider_org = self.add_organisation(element)
        transaction_provider = models.TransactionProvider()
        transaction_provider.organisation = provider_org
        transaction_provider.transaction = model
        self.add_narrative_105(element.text, transaction_provider)
        #store element
        model.provider_organisation = transaction_provider
        return element

    '''atributes:
    receiver-activity-id:AA-AAA-123456789-1234
    ref:AA-AAA-123456789

    tag:receiver-org'''
    def iati_activities__iati_activity__transaction__receiver_org(self, element):
        model = self.get_func_parent_model()
        model.receiver_activity_id = element.attrib.get('receiver-activity-id')
        receiver_org = self.add_organisation(element)
        transaction_receiver = models.TransactionReceiver()
        transaction_receiver.transaction = model
        transaction_receiver.organisation = receiver_org
        self.add_narrative_105(element.text, transaction_receiver)
        #store element
        model.receiver_organisation = transaction_receiver
        return element


    '''atributes:

    tag:title'''
    def iati_activities__iati_activity__document_link__title(self, element):
        model = self.get_func_parent_model()
        document_link_title = models.DocumentLinkTitle()
        document_link_title.document_link = model
        self.add_narrative_105(element.text,document_link_title)
        return element


    '''atributes:

    tag:activity-website'''
    def iati_activities__iati_activity__activity_website(self, element):
        model = self.get_func_parent_model()
        website = models.ActivityWebsite()
        website.activity = model
        website.url = element.text
        website.save()
        #store element 
        return element

    '''atributes:
    type:1

    tag:condition'''
    def iati_activities__iati_activity__conditions__condition(self, element):
        model = self.get_func_parent_model()
        condition = models.Condition()
        condition.activity = model
        condition.type = self.cached_db_call(models.ConditionType,element.attrib.get('type'))
        self.add_narrative_105(element.text, condition)
        return element


    '''atributes:

    tag:title'''
    def iati_activities__iati_activity__result__title(self,element):
        model = self.get_func_parent_model()
        result_title = models.ResultTitle()
        result_title.result = model
        self.add_narrative_105(element.text,result_title)
        return element

    '''atributes:

    tag:description'''
    def iati_activities__iati_activity__result__description(self,element):
        model = self.get_func_parent_model()
        result_description = models.ResultDescription()
        result_description.result = model
        self.add_narrative_105(element.text,result_description)
        return element


    '''atributes:

    tag:title'''
    def iati_activities__iati_activity__result__indicator__title(self,element):
        model = self.get_func_parent_model()
        result_indicator_title = models.ResultIndicatorTitle()
        result_indicator_title.result_indicator = model
        self.add_narrative_105(element.text,result_indicator_title)
        return element

    '''atributes:

    tag:description'''
    def iati_activities__iati_activity__result__indicator__description(self,element):
        model = self.get_func_parent_model()
        result_indicator_description = models.ResultIndicatorDescription()
        result_indicator_description.result_indicator = model
        self.add_narrative_105(element.text,result_indicator_description)
        #store element 
        return element


    '''atributes:

    tag:comment'''
    def iati_activities__iati_activity__result__indicator__baseline__comment(self,element):
        model = self.get_func_parent_model()
        indicator_baseline_comment = models.ResultIndicatorBaseLineComment()
        indicator_baseline_comment.result_indicator = model
        self.add_narrative_105(element.text,indicator_baseline_comment)
        return element


    '''atributes:

    tag:comment'''
    def iati_activities__iati_activity__result__indicator__period__target__comment(self,element):
        model = self.get_func_parent_model()
        period_target_comment = models.ResultIndicatorPeriodTargetComment()
        period_target_comment.result_indicator_period = model
        self.add_narrative_105(element.text,period_target_comment)
        return element


    '''atributes:

    tag:comment'''
    def iati_activities__iati_activity__result__indicator__period__actual__comment(self,element):
        model = self.get_func_parent_model()
        period_actual_comment = models.ResultIndicatorPeriodActualComment()
        period_actual_comment.result_indicator_period = model
        self.add_narrative_105(element.text,period_actual_comment)
        return element


    '''atributes:
    code:1
    significance:1

    tag:aidtype-flag'''
    def iati_activities__iati_activity__crs_add__aidtype_flag(self,element):
        model = self.get_func_parent_model()
        crs_other_flags = models.CrsAddOtherFlags()
        crs_other_flags.crs_add = model
        crs_other_flags.other_flags = self.cached_db_call_no_version(models.OtherFlags,element.attrib.get('code'))
        crs_other_flags.significance = element.attrib.get('significance')
        crs_other_flags.save()
        #store element 
        return element


    '''atributes:
    year:2014
    value-date:2013-07-03
    currency:GBP

    tag:forecast'''
    def iati_activities__iati_activity__fss__forecast(self,element):
        model = self.get_func_parent_model()
        fss_forecast = models.FssForecast()
        fss_forecast.fss = model
        fss_forecast.year = element.attrib.get('year')
        fss_forecast.value_date = self.validate_date(element.attrib.get('value-date'))
        fss_forecast.currency = self.cached_db_call_no_version(models.Currency,element.attrib.get('currency'))
        return element
