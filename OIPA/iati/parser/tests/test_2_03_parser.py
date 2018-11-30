###########################################################
# Unit tests for new functionality in IATI v. 2.03 parser #
###########################################################

import datetime
from decimal import Decimal

import dateutil.parser
# Runs each test in a transaction and flushes database
from django.test import TestCase
from lxml.builder import E

from iati.factory import iati_factory
from iati.parser.exceptions import (
    FieldValidationError, IgnoredVocabularyError, ParserError,
    RequiredFieldError
)
from iati.parser.IATI_2_03 import Parse as Parser_203
from iati.parser.parse_manager import ParseManager
from iati.transaction.factories import TransactionFactory
from iati_codelists.factory import codelist_factory
from iati_codelists.factory.codelist_factory import VersionFactory
from iati_synchroniser.factory import synchroniser_factory
from iati_vocabulary.factory.vocabulary_factory import (
    AidTypeVocabularyFactory, RegionVocabularyFactory, ResultVocabularyFactory,
    SectorVocabularyFactory, TagVocabularyFactory
)


class AddNarrativeTestCase(TestCase):

    """
    2.03: add_narrative() method testing
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # related objects
        # We need to test for two different objects which are 'Activity' and
        # 'Organisation'

        self.title = iati_factory.TitleFactory.create()
        # we want to use actual elements that have narravtive attribute
        self.organisation = iati_factory.OrganisationFactory.create()
        self.activity = iati_factory.ActivityDummyFactory.create()
        self.organisation_reporting_organisation = iati_factory.\
            OrganisationReportingOrganisationFactory.create()

        self.parser_203.register_model('Title', self.title)
        self.parser_203.register_model('Organisation', self.organisation)
        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model('OrganisationReportingOrganisation',
                                       self.
                                       organisation_reporting_organisation)

    def test_add_narrrative(self):
        # Testing for parent = 'organisation_reporting_organisation'
        # Case 1 : parent is not passed
        narrative_attr = {
            '{http://www.w3.org/XML/1998/namespace}lang': 'fr'
        }
        narrative_XML_element = E(
            'narrative',
            **narrative_attr
        )

        try:
            self.parser_203.add_narrative(narrative_XML_element, None,
                                          is_organisation_narrative=True)
        except ParserError as inst:
            self.assertEqual(inst.field, 'narrative')
            self.assertEqual(inst.message, 'parent object must be passed')

        # Case 2 : 'lang' cannot be found

        narrative_attr = {
            '{http://www.w3.org/XML/1998/namespace}lang': 'fr'
        }
        narrative_XML_element = E(
            'narrative',
            **narrative_attr
        )

        try:
            self.parser_203.add_narrative(narrative_XML_element,
                                          self.
                                          organisation_reporting_organisation,
                                          is_organisation_narrative=True)
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'xml:lang')
            self.assertEqual(inst.message, 'must specify xml:lang on '
                                           'iati-activity or xml:lang on the '
                                           'element itself')

        # Case 3 : 'text' is missing

        language = codelist_factory.LanguageFactory(code='en')
        narrative_attr = {
            '{http://www.w3.org/XML/1998/namespace}lang': language.code
        }
        narrative_XML_element = E(
            'narrative',
            **narrative_attr
        )

        try:
            self.parser_203.add_narrative(narrative_XML_element,
                                          self.
                                          organisation_reporting_organisation,
                                          is_organisation_narrative=True)
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'text')
            self.assertEqual(inst.message, 'empty narrative')

        # All is ok

        narrative_XML_element.text = 'Hello world!!'

        self.parser_203.add_narrative(narrative_XML_element, self.
                                      organisation_reporting_organisation,
                                      is_organisation_narrative=True)

        # check all required things are saved

        register_name = self.organisation_reporting_organisation.\
            __class__.__name__ + "Narrative"
        narrative = self.parser_203.get_model(register_name)

        self.assertEqual(narrative.organisation, self.organisation)
        self.assertEqual(narrative.language, language)
        self.assertEqual(narrative.content, narrative_XML_element.text)
        self.assertEqual(narrative._related_object, self.
                         organisation_reporting_organisation)

        # Testing for 'parent' =  Title
        # we only have to test if TitleNarrative is correctly saved.

        narrative_XML_element.text = 'Hello world!!'

        self.parser_203.add_narrative(narrative_XML_element, self.title)

        # check all required things are saved

        register_name = self.title.__class__.__name__ + "Narrative"
        narrative = self.parser_203.get_model(register_name)

        self.assertEqual(narrative.activity, self.activity)
        self.assertEqual(narrative.language, language)
        self.assertEqual(narrative.content, narrative_XML_element.text)
        self.assertEqual(narrative._related_object, self.title)


class ActivityParticipatingOrganisationTestCase(TestCase):
    """
    2.03: A new, not-required attribute 'crs-channel-code' was added
    """

    def setUp(self):

        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.organisation_role = codelist_factory.OrganisationRoleFactory(
            code='1'
        )
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )

    def test_participating_organisation_crs_channel_code(self):
        """
        - Tests if 'crs-channel-code' attribute is parsed and added correctly
          for <participating-organisation> object.
        - Doesn't test if object is actually saved in the database (the final
          stage), because 'save_all_models()' parser's function is (probably)
          tested separately
        """

        # 1. Create specific XML elements for test case:
        participating_org_attributes = {
            "role": self.organisation_role.code,
            "activity-id": self.activity.iati_identifier,
            # code is invalid:
            'crs-channel-code': 'xxx'
        }

        participating_org_XML_element = E(
            'participating-org',
            **participating_org_attributes
        )

        # 2. Create ParticipatingOrganisation object:
        test_organisation = iati_factory \
            .ParticipatingOrganisationFactory.create(
                ref="Gd-COH-123-participating-org",
                    activity=self.activity,
            )

        self.parser_203.register_model('Organisation', test_organisation)

        # crs-channel-code is invalid:
        try:
            self.parser_203.iati_activities__iati_activity__participating_org(
                participating_org_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.message, 'code is invalid')

        # crs-channel-code not found:
        participating_org_attributes['crs-channel-code'] = '123'

        participating_org_XML_element = E(
            'participating-org',
            **participating_org_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__participating_org(
                participating_org_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(
                inst.message, 'not found on the accompanying code list'
            )

        # crs-channel-code is correct:
        crs_object_instance = codelist_factory.CRSChannelCodeFactory(
            code='12345'
        )
        participating_org_attributes[
            'crs-channel-code'
        ] = crs_object_instance.code

        participating_org_XML_element = E(
            'participating-org',
            **participating_org_attributes
        )
        self.parser_203.iati_activities__iati_activity__participating_org(
            participating_org_XML_element)

        participating_organisation = self.parser_203.get_model(
            'ActivityParticipatingOrganisation')

        # Check if CRSChannelCode object is assigned to the participating org
        # (model is not yet saved at this point):
        self.assertEqual(
            participating_organisation.crs_channel_code, crs_object_instance
        )

        # Saving models is not tested here:
        self.assertEqual(participating_organisation.pk, None)


class ActivityTagTestCase(TestCase):
    """
    2.03: A new, xml element 'tag' was added for Activity
    """

    def setUp(self):

        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )

        self.parser_203.register_model('Activity', self.activity)

    def test_activity_tag(self):
        """
        - Tests if '<tag>' xml element is parsed and saved correctly with
          proper attributes and narratives
        - Doesn't test if object is actually saved in the database (the final
          stage), because 'save_all_models()' parser's function is (probably)
          tested separately
        """

        # Create specific XML elements for test case:
        activity_tag_attributes = {
            # Vocabulary is missing:

            # "vocabulary": '1',
            "code": '1',
            'vocabulary-uri': 'http://example.com/vocab.html',
        }

        activity_tag_XML_element = E(
            'tag',
            **activity_tag_attributes
        )

        # CASE 1:
        # 'vocabulary' attr is missing:
        try:
            self.parser_203.iati_activities__iati_activity__tag(
                activity_tag_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(inst.message, 'required attribute missing')

        # 'code' attr is missing:
        activity_tag_attributes['vocabulary'] = '1'
        activity_tag_attributes.pop('code')

        activity_tag_XML_element = E(
            'tag',
            **activity_tag_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__tag(
                activity_tag_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # CASE 2:
        # such TagVocabulary doesn't exist (is not yet created for our tests)
        # AND it's not 99:
        activity_tag_attributes['vocabulary'] = '88'
        activity_tag_attributes['code'] = '1'

        activity_tag_XML_element = E(
            'tag',
            **activity_tag_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__tag(
                activity_tag_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(inst.message, 'If a vocabulary is not on the '
                                           'TagVocabulary codelist, then the '
                                           'value of 99 (Reporting '
                                           'Organisation) should be declared')

        # CASE 3:
        # our system is missing such TagVocabulary object (but vocabulary attr
        # is correct (99)):
        activity_tag_attributes['vocabulary'] = '99'
        activity_tag_attributes['code'] = '1'

        activity_tag_XML_element = E(
            'tag',
            **activity_tag_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__tag(
                activity_tag_XML_element)
            self.asseritFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # CASE 4:
        # Create a Vocabulary and remove vocabulary-uri attr:
        fresh_tag_vicabulary = TagVocabularyFactory(code='99')

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        activity_tag_attributes['vocabulary'] = '99'
        activity_tag_attributes['code'] = '1'
        activity_tag_attributes.pop('vocabulary-uri')

        activity_tag_XML_element = E(
            'tag',
            **activity_tag_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__tag(
                activity_tag_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            # self.assertEqual(inst.field, 'vocabulary-uri')
            self.assertEqual(inst.message, "If a publisher uses a vocabulary "
                                           "of 99 (i.e. ‘Reporting "
                                           "Organisation’), then the "
                                           "@vocabulary-uri attribute should "
                                           "also be used")

        # CASE 5:
        # ALL IS GOOD:
        activity_tag_attributes[
            'vocabulary-uri'
        ] = 'http://example.com/vocab.html'

        activity_tag_XML_element = E(
            'tag',
            **activity_tag_attributes
        )

        self.parser_203.iati_activities__iati_activity__tag(
            activity_tag_XML_element)

        activity_tag = self.parser_203.get_model(
            'ActivityTag')

        # Check if CRSChannelCode object is assigned to the participating org
        # (model is not yet saved at this point):
        self.assertEqual(
            activity_tag.activity, self.activity
        )
        self.assertEqual(
            activity_tag.code, activity_tag_attributes['code']
        )
        self.assertEqual(
            activity_tag.vocabulary, fresh_tag_vicabulary
        )
        self.assertEqual(
            activity_tag.vocabulary_uri,
            activity_tag_attributes['vocabulary-uri']
        )

        # Saving models is not tested here:
        self.assertEqual(activity_tag.pk, None)


class RecipientCountryTestCase(TestCase):
    """
    2.03: 'percentage' attribute must be a decimal number between 0 and 100
    inclusive, WITH NO PERCENTAGE SIGN
    """

    def setUp(self):

        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )

        self.parser_203.register_model('Activity', self.activity)

    def test_recipient_country(self):
        """
        - Tests if '<recipient-country>' xml element is parsed and saved
          correctly with proper attributes and narratives
        - Doesn't test if object is actually saved in the database (the final
          stage), because 'save_all_models()' parser's function is (probably)
          tested separately
        """

        recipient_country_attributes = {
            # "code": '1',
            "country": '1',
            "percentage": '50',
        }

        recipient_country_XML_element = E(
            'recipient-country',
            **recipient_country_attributes
        )

        # CASE 1:
        # 'Code' attr is missing:
        try:
            self.parser_203.iati_activities__iati_activity__recipient_country(
                recipient_country_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # CASE 2:
        # 'Country' attr is missing:

        recipient_country_attributes = {
            "code": '1',
            # "country": '1',
            "percentage": '50',
        }

        recipient_country_XML_element = E(
            'recipient-country',
            **recipient_country_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__recipient_country(
                recipient_country_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(
                inst.message,
                'not found on the accompanying code list'
            )

        # CASE 3:
        # 'percentage' attr is wrong:

        # let's create Country object so parser doesn't complain anymore:
        country = iati_factory.CountryFactory(code='LTU')

        # Clear cache (from memory):
        self.parser_203.codelist_cache = {}

        recipient_country_attributes = {
            "code": country.code,
            "country": '1',
            "percentage": '50%',
        }

        recipient_country_XML_element = E(
            'recipient-country',
            **recipient_country_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__recipient_country(
                recipient_country_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'percentage')
            self.assertEqual(
                inst.message,
                'percentage value is not valid'
            )

        # CASE 4:
        # all is good:

        recipient_country_attributes = {
            "code": country.code,
            "country": '1',
            "percentage": '50',
        }

        recipient_country_XML_element = E(
            'recipient-country',
            **recipient_country_attributes
        )

        self.parser_203.iati_activities__iati_activity__recipient_country(
            recipient_country_XML_element)

        recipient_country = self.parser_203.get_model(
            'ActivityRecipientCountry')

        # check if everything's saved:

        self.assertEqual(
            recipient_country.country, country
        )
        self.assertEqual(
            recipient_country.activity, self.activity
        )
        self.assertEqual(
            recipient_country.percentage,
            Decimal(recipient_country_attributes['percentage'])
        )

        # Saving models is not tested here:
        self.assertEqual(recipient_country.pk, None)


class RecipientRegionTestCase(TestCase):
    """
    2.03: 'percentage' attribute must be a decimal number between 0 and 100
    inclusive, WITH NO PERCENTAGE SIGN
    """

    def setUp(self):

        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )

        self.parser_203.register_model('Activity', self.activity)

    def test_recipient_region(self):
        """
        - Tests if '<recipient-region>' xml element is parsed and saved
          correctly with proper attributes and narratives
        - Doesn't test if object is actually saved in the database (the final
          stage), because 'save_all_models()' parser's function is (probably)
          tested separately
        """

        recipient_region_attributes = {
            # "code": '1',
        }

        recipient_region_XML_element = E(
            'recipient-region',
            **recipient_region_attributes
        )

        # CASE 1:
        # 'Code' attr is missing:
        try:
            self.parser_203.iati_activities__iati_activity__recipient_region(
                recipient_region_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.model, 'recipient-region')
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'code is unspecified or invalid')

        # CASE 2:
        # Vocabulary not found:

        recipient_region_attributes = {
            "code": '222',
        }

        recipient_region_XML_element = E(
            'recipient-region',
            **recipient_region_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__recipient_region(
                recipient_region_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.model, 'recipient-region')
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(
                inst.message, 'not found on the accompanying code list'
            )

        # CASE 3:
        # Region not found (when code attr == 1):

        # Create Vocabulary obj:
        vocabulary = RegionVocabularyFactory(code=1)

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        recipient_region_attributes = {
            "code": '1',
            "vocabulary": str(vocabulary.code),
        }

        recipient_region_XML_element = E(
            'recipient-region',
            **recipient_region_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__recipient_region(
                recipient_region_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.model, 'recipient-region')
            self.assertEqual(inst.field, 'code')
            self.assertEqual(
                inst.message,
                "not found on the accompanying code list"
            )

        # CASE 4:
        # Region not found (when code attr is differnt):

        # Update Vocabulary obj:
        vocabulary.code = 222
        vocabulary.save()

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        recipient_region_attributes = {
            "code": '1',
            "vocabulary": str(vocabulary.code),
        }

        recipient_region_XML_element = E(
            'recipient-region',
            **recipient_region_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__recipient_region(
                recipient_region_XML_element)
            self.assertFail()
        except IgnoredVocabularyError as inst:
            self.assertEqual(inst.model, 'recipient-region')
            self.assertEqual(inst.field, 'code')
            self.assertEqual(
                inst.message, 'code is unspecified or invalid'
            )

        # CASE 5:
        # percentage is wrong:

        # Update Vocabulary obj:
        vocabulary.code = 1
        vocabulary.save()

        # Create Region obj:
        region = iati_factory.RegionFactory()

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        recipient_region_attributes = {
            "code": region.code,
            "vocabulary": str(vocabulary.code),
            "percentage": '100%'
        }

        recipient_region_XML_element = E(
            'recipient-region',
            **recipient_region_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__recipient_region(
                recipient_region_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            # self.assertEqual(inst.field, 'percentage')
            self.assertEqual(
                inst.message,
                'percentage value is not valid'
            )

        # CASE 6:
        # All is good:

        # Refresh related object so old one doesn't get assigned:
        vocabulary.refresh_from_db()

        recipient_region_attributes = {
            "code": region.code,
            "vocabulary": str(vocabulary.code),
            "percentage": '100',
            "vocabulary-uri": "http://www.google.lt",
        }

        recipient_region_XML_element = E(
            'recipient-region',
            **recipient_region_attributes
        )

        self.parser_203.iati_activities__iati_activity__recipient_region(
            recipient_region_XML_element)

        recipient_region = self.parser_203.get_model(
            'ActivityRecipientRegion')

        self.assertEqual(
            recipient_region.region, region
        )

        self.assertEqual(
            recipient_region.activity, self.activity
        )

        self.assertEqual(
            recipient_region.percentage,
            Decimal(recipient_region_attributes['percentage'])
        )

        self.assertEqual(
            recipient_region.vocabulary_uri,
            recipient_region_attributes['vocabulary-uri']
        )

        self.assertEqual(recipient_region.vocabulary, vocabulary)

        # Saving models is not tested here:
        self.assertEqual(recipient_region.pk, None)


class ActivitySectorTestCase(TestCase):
    """
    2.03: 'percentage' attribute must be a decimal number between 0 and 100
    inclusive, WITH NO PERCENTAGE SIGN
    """

    def setUp(self):

        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )

        self.parser_203.register_model('Activity', self.activity)

    def test_activity_sector(self):
        """
        - Tests if '<sector>' xml element is parsed and saved
          correctly with proper attributes and narratives
        - Doesn't test if object is actually saved in the database (the final
          stage), because 'save_all_models()' parser's function is (probably)
          tested separately
        """

        sector_attributes = {
            # "code": '1',
        }

        sector_XML_element = E(
            'sector',
            **sector_attributes
        )

        # CASE 1:
        # 'Code' attr is missing:
        try:
            self.parser_203.iati_activities__iati_activity__sector(
                sector_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.model, 'sector')
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # CASE 2:
        # Vocabulary not found:

        sector_attributes = {
            "code": '1',
            "vocabulary": '222',
        }

        sector_XML_element = E(
            'sector',
            **sector_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__sector(
                sector_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.model, 'sector')
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(
                inst.message,
                "not found on the accompanying code list"
            )

        # CASE 3:
        # Region not found (when code attr == 1):

        # Create Vocabulary obj:
        vocabulary = SectorVocabularyFactory(code=1)

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        sector_attributes = {
            "code": '1',
            "vocabulary": str(vocabulary.code),
        }

        sector_XML_element = E(
            'sector',
            **sector_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__sector(
                sector_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.model, 'sector')
            self.assertEqual(inst.field, 'code')
            self.assertEqual(
                inst.message,
                "not found on the accompanying code list"
            )

        # CASE 4:
        # Sector not found (when code attr is differnt):

        # Update Vocabulary obj:
        vocabulary.code = 222
        vocabulary.save()

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        sector_attributes = {
            "code": '1',
            "vocabulary": str(vocabulary.code),
        }

        sector_XML_element = E(
            'sector',
            **sector_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__sector(
                sector_XML_element)
            self.assertFail()
        except IgnoredVocabularyError as inst:
            self.assertEqual(inst.model, 'sector')
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(
                inst.message, 'non implemented vocabulary'
            )

        # CASE 5:
        # percentage is wrong:

        # Update Vocabulary obj:
        vocabulary.code = 1
        vocabulary.save()

        sector = iati_factory.SectorFactory()

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        sector_attributes = {
            "code": sector.code,
            "vocabulary": str(vocabulary.code),
            "percentage": '100%'
        }

        sector_XML_element = E(
            'sector',
            **sector_attributes
        )

        try:
            self.parser_203.iati_activities__iati_activity__sector(
                sector_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.model, 'sector')
            self.assertEqual(inst.field, 'percentage')
            self.assertEqual(
                inst.message,
                'percentage value is not valid'
            )

        # CASE 6:
        # All is good:

        # Refresh related object so old one doesn't get assigned:
        sector.refresh_from_db()
        vocabulary.refresh_from_db()

        sector_attributes = {
            "code": sector.code,
            "vocabulary": str(vocabulary.code),
            "percentage": '100',
            "vocabulary-uri": "http://www.google.lt",
        }

        sector_XML_element = E(
            'sector',
            **sector_attributes
        )

        self.parser_203.iati_activities__iati_activity__sector(
            sector_XML_element)

        activity_sector = self.parser_203.get_model(
            'ActivitySector')

        self.assertEqual(
            activity_sector.sector, sector
        )

        self.assertEqual(
            activity_sector.activity, self.activity
        )

        self.assertEqual(
            activity_sector.percentage,
            Decimal(sector_attributes['percentage'])
        )

        self.assertEqual(
            activity_sector.vocabulary_uri,
            sector_attributes['vocabulary-uri']
        )

        self.assertEqual(activity_sector.vocabulary, vocabulary)

        # Saving models is not tested here:
        self.assertEqual(activity_sector.pk, None)


class AidTypeTestCase(TestCase):
    """
    2.03: Added new @vocabulary attributes for elements relating to aid-type
    """

    def setUp(self):

        AidTypeVocabularyFactory(name='OECD DAC')

        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version,
            default_aid_type=None,
        )

        self.transaction = TransactionFactory(
            activity=self.activity
        )

        self.parser_203.register_model('Transaction', self.transaction)
        self.parser_203.register_model('Activity', self.activity)

    def test_transaction_aid_type(self):
        """
        - Tests if '<aid-type>' xml element is parsed and saved
          correctly with proper attributes and narratives
        - Doesn't test if object is actually saved in the database (the final
          stage), because 'save_all_models()' parser's function is (probably)
          tested separately
        """

        aid_type_attributes = {
            # "code": '1',
        }

        aid_type_XML_element = E(
            'aid-type',
            **aid_type_attributes
        )

        # CASE 1:
        # 'Code' attr is missing:
        try:
            self.parser_203.\
                iati_activities__iati_activity__transaction__aid_type(
                # NOQA: E501
                aid_type_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.model, 'iati-activity/transaction/aid-type')
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # CASE 2:
        # 'AidType' codelist not found:
        aid_type_attributes = {
            "code": '1',
        }

        aid_type_XML_element = E(
            'aid-type',
            **aid_type_attributes
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__transaction__aid_type(
                # NOQA: E501
                aid_type_XML_element)
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.model, 'transaction/aid-type')
            self.assertEqual(inst.field, 'code')
            self.assertEqual(
                inst.message,
                "not found on the accompanying code list. Note, that custom "
                "AidType Vocabularies currently are not supported"
            )

        # CASE 3: All is good
        # let's create an AidTypeVocabulary and AidType elements (so the
        # parser doesn't complain):
        aid_type_vocabulary = AidTypeVocabularyFactory(code='3')
        aid_type = codelist_factory.AidTypeFactory(
            code='3',
            vocabulary=aid_type_vocabulary
        )

        # Clear codelist cache (from memory):
        self.parser_203.codelist_cache = {}

        aid_type_attributes = {
            "code": aid_type.code,
            'vocabulary': aid_type_vocabulary.code,
        }

        aid_type_XML_element = E(
            'aid-type',
            **aid_type_attributes
        )

        self.parser_203.iati_activities__iati_activity__transaction__aid_type(
            # NOQA: E501
            aid_type_XML_element)

        transaction = self.parser_203.get_model('Transaction')

        transaction_aid_type = self.parser_203.get_model('TransactionAidType')

        self.assertEqual(
            transaction_aid_type.transaction, transaction
        )
        self.assertEqual(
            transaction_aid_type.aid_type, aid_type
        )


class ActivityDefaultAidTypeTestCase(TestCase):
    """
    2.03: 'The default-aid-type' element can be reported multiple times within
    an iati-activity element. The 'code' attribute definition was updated.
    The 'vocabulary' attribute was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )
        self.parser_203.register_model('Activity', self.activity)

    def test_activity_default_aid_type(self):

        # 1) code attribute is missing:
        activity_default_aid_type_attrs = {
            # 'code': 'A01',
            'vocabulary': '1',
        }

        activity_default_aid_type_XML_element = E(
            'default-aid-type',
            **activity_default_aid_type_attrs
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__default_aid_type(
                    activity_default_aid_type_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # let's create DEFAULT AidTypeVocabulary:

        default_aid_type_vocabulary = AidTypeVocabularyFactory(
            code='1',
            name='OECD DAC',
        )

        # 2) case with custom (currently not supported) AidTypeVocabulary
        # codelist:
        activity_default_aid_type_attrs = {
            'code': 'A01',
            'vocabulary': '4',  # this is custom vocabulary
        }

        activity_default_aid_type_XML_element = E(
            'default-aid-type',
            **activity_default_aid_type_attrs
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__default_aid_type(
                    activity_default_aid_type_XML_element
                )
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(
                inst.message,
                'not found on the accompanying AidTypeVocabulary code list. '
                'Note, that custom AidType Vocabularies currently are not '
                'supported'
            )

        # 3) case with invalid code from default AidTypeVocabulary:
        activity_default_aid_type_attrs = {
            'code': '2',  # this is invalid code
            'vocabulary': '1',
        }

        activity_default_aid_type_XML_element = E(
            'default-aid-type',
            **activity_default_aid_type_attrs
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__default_aid_type(
                    activity_default_aid_type_XML_element
                )
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(
                inst.message,
                'not found on the accompanying AidType code list. '
                'Note, that custom AidType Vocabularies currently are not '
                'supported'
            )

        # 4) all is good:
        # create default AidType codelist entry:
        first_default_aid_type = codelist_factory.AidTypeFactory(
            vocabulary=default_aid_type_vocabulary,
            code='H02'
        )

        activity_default_aid_type_attrs = {
            'code': 'H02',
            'vocabulary': '1',
        }

        activity_default_aid_type_XML_element = E(
            'default-aid-type',
            **activity_default_aid_type_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__default_aid_type(
                activity_default_aid_type_XML_element
            )

        activity_default_aid_type = self.parser_203.get_model(
            'ActivityDefaultAidType'
        )

        self.assertEqual(activity_default_aid_type.activity, self.activity)
        self.assertEqual(
            activity_default_aid_type.aid_type,
            first_default_aid_type
        )

        # 5) multiple default_aid_types for activity:

        # create 2nd default AidType codelist entry:
        second_default_aid_type = codelist_factory.AidTypeFactory(
            vocabulary=default_aid_type_vocabulary,
            code='H03'
        )

        activity_default_aid_type_attrs = {
            'code': 'H03',
            'vocabulary': '1',
        }

        activity_default_aid_type_XML_element = E(
            'default-aid-type',
            **activity_default_aid_type_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__default_aid_type(
                activity_default_aid_type_XML_element
            )

        self.activity.refresh_from_db()

        # all unassigned FK relationships are assigned here:
        self.parser_203.save_all_models()

        # Test if multiple default_aid_types are assigned for Activity:
        self.assertEqual(self.activity.default_aid_types.count(), 2)

        self.assertEqual(
            self.activity.default_aid_types.first().aid_type,
            first_default_aid_type,
        )
        self.assertEqual(
            self.activity.default_aid_types.last().aid_type,
            second_default_aid_type
        )


class ActivityDocumentLinkDescriptionTestCase(TestCase):
    '''
    2.03: The optional description element of a document-link element was
    added.
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_document_link_description(self):
        '''test if <description> element for Activity's <document-limk> element
        is parsed and saved correctly
        '''

        document_link_description_attrs = {}

        result_document_link_XML_element = E(
            'description',
            **document_link_description_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__document_link__description(
                result_document_link_XML_element
            )

        document_link_description = self.parser_203.get_model(
            'DocumentLinkDescription'
        )

        self.assertEqual(
            document_link_description.document_link,
            self.document_link

        )


class ActivityResultDocumentLinkTestCase(TestCase):
    '''
    2.03: Added new (optional) <document-link> element for <result>
    element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )
        self.result = iati_factory.ResultFactory.create()

        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model('Result', self.result)

    def test_activity_result_document_link(self):
        """
        - Tests if '<result_document_link>' xml element is parsed and saved
          correctly with proper attributes.
        - Doesn't test if object is actually saved in the database (the final
          stage), because 'save_all_models()' parser's function is (probably)
          tested separately
        """

        # Case 1:
        #  'url is missing'

        result_document_link_attr = {
            # url = 'missing'
            "format": 'something'
            # 'format_code' will be retrieved in the function
        }
        result_document_link_XML_element = E(
            'document-link',
            **result_document_link_attr
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__document_link(
                    result_document_link_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'url')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 2:
        # 'file_format' is missing

        result_document_link_attr = {
            "url": 'www.google.com'
            # "format":
            # 'format_code' will be retrieved in the function
        }
        result_document_link_XML_element = E(
            'document-link',
            **result_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__document_link(
                    result_document_link_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 3;
        # 'file_format_code' is missing

        result_document_link_attr = {
            "url": 'www.google.com',
            "format": 'something',
            # 'format_code will be retrieved in the function
        }
        result_document_link_XML_element = E(
            'document-link',
            **result_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__document_link(
                    result_document_link_XML_element
                )
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # Case 4;
        # all is good

        # dummy document-link object
        dummy_file_format = codelist_factory.\
            FileFormatFactory(code='application/pdf')

        dummy_document_link = iati_factory.\
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        result_document_link_attr = {
            "url": dummy_document_link.url,
            "format": dummy_file_format.code

        }
        result_document_link_XML_element = E(
            'document-link',
            **result_document_link_attr
        )

        self.parser_203 \
            .iati_activities__iati_activity__result__document_link(
                result_document_link_XML_element
            )

        document_link = self.parser_203.get_model('DocumentLink')

        # checking if everything is saved

        self.assertEqual(document_link.url, dummy_document_link.url)
        self.assertEqual(document_link.file_format,
                         dummy_document_link.file_format)
        self.assertEqual(document_link.activity, self.activity)
        self.assertEqual(document_link.result, self.result)


class ActivityResultDocumentLinkTitleTestCase(TestCase):
    '''
    2.03: Added new (optional) <document-link> element for <result>
    element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )
        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_document_link_title(self):
        '''
        Test if title attribute in <document_link> XML element is correctly
        saved.
        '''

        dummy_file_format = codelist_factory. \
            FileFormatFactory(code='application/pdf')

        dummy_document_link = iati_factory. \
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        result_document_link_attr = {
            "url": dummy_document_link.url,
            "format": dummy_file_format.code

        }
        result_document_link_XML_element = E(
            'document-link',
            **result_document_link_attr
        )
        self.parser_203 \
            .iati_activities__iati_activity__result__document_link__title(
                result_document_link_XML_element)
        document_link_title = self.parser_203.get_model(
            'DocumentLinkTitle')

        self.assertEqual(self.document_link,
                         document_link_title.document_link)


class ActivityResultDocumentLinkCategoryTestCase(TestCase):
    """
    2.03: Added  (optional) <category> element of a <document-link> in a
    <result> element.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory.create()

        self.parser_203.register_model(
            'DocumentLink', self.document_link
        )

    def test_activity_result_document_link_document_category(self):
        # FIXME: fix all these docstrings:

        """
        Test if <document_link> attribute in <documen_link_category> XML
        element is correctly saved.
        """

        # case 1: when code is missing

        document_link_category_attr = {
            # 'code': 'A04'

        }

        document_link_category_XML_element = E(
            'category',
            **document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__document_link__category(  # NOQA: E501
                document_link_category_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'required attribute missing')

        # case 2: when category cannot be retrieved using the given code
        document_link_category_attr = {
            'code': 'A04'

        }

        document_link_category_XML_element = E(
            'category',
            **document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__document_link__category(  # NOQA: E501
                document_link_category_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'codelist')

        # case:  when all is good

        # Let's create dummy document_category
        document_category = codelist_factory.DocumentCategoryFactory(
            code='A04'
        )
        document_link_category_attr = {
            'code': document_category.code

        }

        document_link_category_XML_element = E(
            'category',
            **document_link_category_attr
        )

        self.parser_203.codelist_cache = {}

        self.parser_203\
            .iati_activities__iati_activity__result__document_link__category(
                document_link_category_XML_element
            )
        # get DocumentLinkCategory

        document_link_category = self.parser_203.get_model(
            'DocumentLinkCategory')

        self.assertEqual(document_link_category.document_link, self.
                         document_link)
        self.assertEqual(document_link_category.category, document_category)


class ActivityResultDocumentLinkDocumentDateTestCase(TestCase):
    '''
    2.03: Added new (optional) <document-link> element for <result>
    element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_document_link_document_date(self):
        '''
        Test if iso-date attribute in <document_link> XML element is
        correctly saved.
        '''

        # case 1: 'iso-date' is missing

        document_date_attr = {
            # "iso-date": '25116600000'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__document_link__document_date(  # NOQA: E501

                document_date_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2 : 'iso-date' is not valid
        document_date_attr = {

            "iso-date": '25116600000'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.parser_203.iati_activities__iati_activity__result__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'Unspecified or invalid. Date '
                                           'should be of type xml:date.')

        # case 3: 'iso-date' is not in correct range
        document_date_attr = {

            "iso-date": '18200915'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'iso-date not of type xsd:date')

        # all is good
        document_date_attr = {

            "iso-date": '2011-05-06'  # this is acceptable  iso-date

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__document_link__document_date(  # NOQA: E501
            document_date_XML_element
        )

        # Let's test date is saved

        date = dateutil.parser.parse('2011-05-06', ignoretz=True)

        document_link = self.parser_203.get_model('DocumentLink')
        self.assertEqual(date, document_link.iso_date)


class ActivityResultDocumentLinkLanguageTestCase(TestCase):
    '''
    2.03: Added new (optional) <document-link> element for <result>
    element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_document_link_language(self):
        '''
        Test if language attribute in <document_link_language> XML element is
        correctly saved.
        '''

        # case 1: 'code' is missing

        document_language_attr = {
            # "code": 'en'

        }
        document_language_XML_element = E(
            'document-date',
            **document_language_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__document_link__language(  # NOQA: E501

                document_language_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2: 'language' is not found
        document_language_attr = {

            "code": 'ab'

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__document_link__language(  # NOQA: E501
                document_language_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'not found on the accompanying code list')

        # all is good
        language = codelist_factory.LanguageFactory()  # dummy language object
        document_language_attr = {

            "code": language.code

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__document_link__language(
                document_language_XML_element
            )

        # Let's test language is saved

        document_link = self.parser_203.get_model('DocumentLink')
        document_link_language = self.parser_203.get_model(
            'DocumentLinkLanguage')
        self.assertEqual(document_link, document_link_language.document_link)
        self.assertEqual(language, document_link_language.language)


class ActivityResultDocumentLinkDescriptionTestCase(TestCase):
    '''
    2.03: The optional <description> element of a <document-link> element was
    added.
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()
        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_document_link_description(self):
        '''test if <description> element for Result's <document-link> element
        is parsed and saved correctly
        '''

        document_link_description_attrs = {}

        result_document_link_XML_element = E(
            'description',
            **document_link_description_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__result__document_link__description(
                result_document_link_XML_element
            )

        document_link_description = self.parser_203.get_model(
            'DocumentLinkDescription'
        )

        self.assertEqual(
            document_link_description.document_link,
            self.document_link
        )


class ActivityResultIndicatorTestCase(TestCase):

    """
    2.03: The optional attribute 'aggregation-status' was added
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.result = iati_factory.ResultFactory.create()
        self.activity = self.result.activity

        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model('Result', self.result)

    def test_activity_result_indicator(self):
        """test if <indicator> element inside <result> element is parsed
        properly
        """

        # 1) measure attribute is missing:
        result_indicator_attrs = {
            # "measure": "1",
            "ascending": "1",
            "aggregation-status": "1",

        }

        result_indicator_XML_element = E(
            'indicator',
            **result_indicator_attrs
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator(
                    result_indicator_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'measure')
            self.assertEqual(inst.message, 'required attribute missing')

        # 2) IndicatorMeasure codelist is missing:

        result_indicator_attrs = {
            "measure": "1",
            "ascending": "1",
            "aggregation-status": "1",

        }

        result_indicator_XML_element = E(
            'indicator',
            **result_indicator_attrs
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator(
                    result_indicator_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'measure')
            self.assertEqual(
                inst.message,
                'not found on the accompanying code list'
            )

        # 3) everything's OK:
        # let's create an IndicatorMeasure codelist object:

        self.parser_203.codelist_cache = {}

        result_indicator_attrs = {
            "measure": "1",
            "ascending": "1",
            "aggregation-status": "1",

        }

        indicator_measure = iati_factory.IndicatorMeasureFactory.create(
            code=result_indicator_attrs.get("measure")
        )

        result_indicator_XML_element = E(
            'indicator',
            **result_indicator_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__result__indicator(
                result_indicator_XML_element
            )

        result_indicator = self.parser_203.get_model('ResultIndicator')

        self.assertEqual(result_indicator.result, self.result)
        self.assertEqual(
            result_indicator.measure,
            indicator_measure
        )
        self.assertEqual(result_indicator.ascending, True)
        self.assertEqual(result_indicator.aggregation_status, True)


class ActivityResultIndicatorDocumentLinkTestCase(TestCase):

    """
    2.03: The optional document-link element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create(
            name="dataset-2"
        )

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Related objects:
        self.result_indicator = iati_factory.ResultIndicatorFactory.create()
        self.activity = self.result_indicator.result.activity
        self.result = self.result_indicator.result

        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model('Result', self.result)
        self.parser_203.register_model(
            'ResultIndicator', self.result_indicator
        )

    def test_activity_result_indicator_document_link(self):

        # Case 1:
        #  'url is missing'

        result_indicator_document_link_attr = {
            # url = 'missing'
            "format": 'something'
            # 'format_code' will be retrieved in the function
        }
        result_indicator_document_link_XML_element = E(
            'document-link',
            **result_indicator_document_link_attr
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__document_link(  # NOQA: E501
                    result_indicator_document_link_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'url')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 2:
        # 'file_format' is missing

        result_indicator_document_link_attr = {
            "url": 'www.google.com'

            # "format":
            # 'format_code' will be retrieved in the function
        }
        result_indicator_document_link_XML_element = E(
            'document-link',
            **result_indicator_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__document_link(  # NOQA: E501
                    result_indicator_document_link_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 3;
        # 'file_format_code' is missing

        result_indicator_document_link_attr = {
            "url": 'www.google.com',
            "format": 'something',
            # 'format_code will be retrieved in the function
        }
        result_indicator_document_link_XML_element = E(
            'document-link',
            **result_indicator_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__document_link(  # NOQA: E501
                    result_indicator_document_link_XML_element
                )
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # Case 4;
        # all is good

        # dummy document-link object
        dummy_file_format = codelist_factory.\
            FileFormatFactory(code='application/pdf')

        dummy_document_link = iati_factory.\
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        result_indicator_document_link_attr = {
            "url": dummy_document_link.url,
            "format": dummy_file_format.code

        }
        result_indicator_document_link_XML_element = E(
            'document-link',
            **result_indicator_document_link_attr
        )

        self.parser_203 \
            .iati_activities__iati_activity__result__indicator__document_link(
                result_indicator_document_link_XML_element
            )

        result_indicator_document_link = self.parser_203.get_model(
            'DocumentLink'
        )

        # checking if everything is saved

        self.assertEqual(
            result_indicator_document_link.url,
            dummy_document_link.url
        )
        self.assertEqual(
            result_indicator_document_link.file_format,
            dummy_document_link.file_format
        )
        self.assertEqual(
            result_indicator_document_link.activity,
            self.activity
        )
        self.assertEqual(
            result_indicator_document_link.result_indicator,
            self.result_indicator
        )


class ActivityResultIndicatorDocumentLinkDocumentDateTestCase(TestCase):

    """
    2.03: The optional document-date element of a document-link in a indicator
    in a result element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory.create()

        self.parser_203.register_model(
            'DocumentLink', self.document_link
        )

    def test_activity_result_indicator_document_link_document_date(self):
        """
        Test if iso-date attribute in <document_link> XML element is correctly
        saved.
        """

        # Case 1: 'ido-date' attribute is missing:

        document_date_attr = {
            # 'iso-date': '2018-10-10',
        }

        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__document_link__document_date(  # NOQA: E501
                    document_date_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 2:
        # ISO date is invalid:

        document_date_attr = {
            'iso-date': '2018-10-ab',
        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__document_link__document_date(  # NOQA: E501
                    document_date_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(
                inst.message,
                'Unspecified or invalid. Date should be of type xml:date.'
            )

        # Case 3:
        # all is good:

        document_date_attr = {
            'iso-date': '2018-10-10',
        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        self.parser_203.\
            iati_activities__iati_activity__result__indicator__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )

        result_indicator_document_link = self.parser_203.get_model(
            'DocumentLink'
        )

        self.assertEqual(
            result_indicator_document_link.iso_date,
            datetime.datetime(2018, 10, 10, 0, 0)
        )


class ActivityResultIndicatorDocumentLinkTitleTestCase(TestCase):
    '''
    2.03: Added new (optional) <document-link> element for <indicator>
    element inside <result> element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_document_link_title(self):
        '''
        Test if title attribute in <document_link> XML element for
        <indicator> element is correctly saved.
        '''

        dummy_file_format = codelist_factory. \
            FileFormatFactory(code='application/pdf')

        dummy_indicator_document_link = iati_factory. \
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        result_document_link_attr = {
            "url": dummy_indicator_document_link.url,
            "format": dummy_file_format.code

        }
        result_indicator_document_link_XML_element = E(
            'document-link',
            **result_document_link_attr
        )
        self.parser_203 \
            .iati_activities__iati_activity__result__indicator__document_link__title(  # NOQA: E501
            result_indicator_document_link_XML_element)

        document_link_title = self.parser_203.get_model(
            'DocumentLinkTitle')

        self.assertEqual(self.document_link,
                         document_link_title.document_link)


class ActivityResultIndicatorDocumentLinkCategoryTestCase(TestCase):
    """
    2.03: Added  (optional) <category> element of a <document-link> in a
    <result> element.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory.create()

        self.parser_203.register_model(
            'DocumentLink', self.document_link
        )

    def test_activity_result_indicator_document_link_document_category(self):
        """
        Test if <indicator_document_link> attribute in
        <document_link_category> XML element is correctly saved.
        """

        # case 1: when code is missing

        indicator_document_link_category_attr = {
            # 'code': 'A04'

        }

        indicator_document_link_category_XML_element = E(
            'category',
            **indicator_document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__document_link__category(  # NOQA: E501
                indicator_document_link_category_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'required attribute missing')

        # case 2: when category cannot be retrieved using the given code
        indicator_document_link_category_attr = {
            'code': 'A04'

        }

        indicator_document_link_category_XML_element = E(
            'category',
            **indicator_document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__document_link__category(  # NOQA: E501
                indicator_document_link_category_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # case:  when all is good

        # Let's create dummy document_category
        indicator_document_category = \
            codelist_factory.DocumentCategoryFactory(
                code='A04'
            )
        indicator_document_link_category_attr = {
            'code': indicator_document_category.code

        }

        indicator_document_link_category_XML_element = E(
            'category',
            **indicator_document_link_category_attr
        )

        self.parser_203.codelist_cache = {}

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__document_link__category(  # NOQA: E501
                indicator_document_link_category_XML_element
            )
        # get DocumentLinkCategory

        indicator_document_link_category = self.parser_203.get_model(
            'DocumentLinkCategory')

        self.assertEqual(indicator_document_link_category.document_link, self.
                         document_link)
        self.assertEqual(indicator_document_link_category.category,
                         indicator_document_category)


class ActivityResultIndicatorDocumentLinkLanguageTestCase(TestCase):
    '''
    2.03: Added new (optional) <document-link> element for <indicator>
    element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()
        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink',
                                       self.document_link)

    def test_activity_result_indicator_document_link_language(self):
        '''
        Test if <language> element in <document_link> XML element is
        correctly saved.
        '''

        # case 1: 'code' is missing

        language_attr = {
            # "code": 'en'

        }
        language_XML_element = E(
            'language',
            **language_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__indicator__document_link__language(  # NOQA: E501

                language_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2: 'language' is not found
        language_attr = {

            "code": 'ab'

        }
        language_XML_element = E(
            'language',
            **language_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__document_link__language(  # NOQA: E501
                language_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'not found on the accompanying code list')

        # all is good
        language = codelist_factory.LanguageFactory()  # dummy language object
        language_attr = {

            "code": language.code

        }
        language_XML_element = E(
            'language',
            **language_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__indicator__document_link__language(  # NOQA: E501
                language_XML_element
            )

        # Let's test language is saved

        document_link_language = self.parser_203.get_model(
            'DocumentLinkLanguage')
        self.assertEqual(self.document_link,
                         document_link_language.document_link)
        self.assertEqual(language, document_link_language.language)


class ActivityResultIndicatorDocumentLinkDescriptionTestCase(TestCase):
    '''
    2.03: The optional <description> element of a <document-link> element was
    added.
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()
        self.document_link = iati_factory.DocumentLinkFactory.\
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_document_link_description(self):
        '''test if <description> element for Result Indicator's <document-link>
        element is parsed and saved correctly
        '''

        document_link_description_attrs = {}

        result_document_link_XML_element = E(
            'description',
            **document_link_description_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__result__indicator__document_link__description(  # NOQA: E501
                result_document_link_XML_element
            )

        document_link_description = self.parser_203.get_model(
            'DocumentLinkDescription'
        )

        self.assertEqual(
            document_link_description.document_link,
            self.document_link
        )


class ActivityResultIndicatorBaselineTestCase(TestCase):
    """
    2.03: The occurance rules of the baseline element were amended so that it
    can be reported multiple times.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.result_indicator = iati_factory.ResultIndicatorFactory()

        self.result_indicator_baseline = iati_factory.\
            ResultIndicatorBaselineFactory(
                result_indicator=self.result_indicator
            )

        self.parser_203.register_model(
            'ResultIndicatorBaseline', self.result_indicator_baseline
        )
        self.parser_203.register_model(
            'ResultIndicator', self.result_indicator
        )

    def test_activity_result_indicator_baseline(self):
        """
        test if <baseline> element in context of an indicator in a result
        element is parsed and saved correctly
        """

        # 1. year value is not provided:

        result_indicator_baseline_attrs = {
            'iso-date': '2018-11-13',
            # 'year': '2018',
            'value': '10',
        }

        result_indicator_baseline_XML_element = E(
            'baseline',
            **result_indicator_baseline_attrs
        )

        try:
            self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline(
                    result_indicator_baseline_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(
                inst.message, 'required attribute missing (should be of type '
                              'xsd:positiveInteger with format (yyyy))'
            )

        # 2. year value is wrong:

        result_indicator_baseline_attrs = {
            'iso-date': '2018-11-13',
            'year': '1899',
            'value': '10',
        }

        result_indicator_baseline_XML_element = E(
            'baseline',
            **result_indicator_baseline_attrs
        )

        try:
            self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline(
                    result_indicator_baseline_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(
                inst.message, 'required attribute missing (should be of type '
                              'xsd:positiveInteger with format (yyyy))'
            )

        # 3. all is good:
        result_indicator_baseline_attrs = {
            'iso-date': '2018-11-13',
            'year': '2018',
            'value': '10',
        }

        result_indicator_baseline_XML_element = E(
            'baseline',
            **result_indicator_baseline_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__baseline(
                result_indicator_baseline_XML_element
            )

        result_indicator_baseline = self.parser_203.get_model(
            'ResultIndicatorBaseline'
        )

        # Year
        self.assertEqual(
            result_indicator_baseline.year,
            int(result_indicator_baseline_attrs['year']),
        )

        # Value
        self.assertEqual(
            result_indicator_baseline.value,
            result_indicator_baseline_attrs['value'],
        )

        # ISO date
        self.assertEqual(
            result_indicator_baseline.iso_date,
            result_indicator_baseline_attrs['iso-date'],
        )

        # Result Indicator
        self.assertEqual(
            result_indicator_baseline.result_indicator,
            self.result_indicator,
        )


class ActivityResultIndicatorBaselineLocationTestCase(TestCase):
    '''2.03: The optional location element was added.
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.result_indicator = iati_factory.ResultIndicatorFactory()

        self.result_indicator_baseline = iati_factory.\
            ResultIndicatorBaselineFactory(
                result_indicator=self.result_indicator,
            )

        self.activity = self.result_indicator_baseline.result_indicator\
            .result.activity

        self.location = iati_factory.LocationFactory(ref='KH-PNH')

        self.parser_203.register_model('Activity', self.activity)

        self.parser_203.register_model(
            'ResultIndicatorBaseline',
            self.result_indicator_baseline
        )
        self.parser_203.register_model('Location', self.location)

    def test_activity_result_indicator_baseline_location(self):

        """
        Test if <location> element in context of a baseline element (as part
        of a parent result/indicator element) is parsed and saved correctly
        """

        # 1. 'ref' attribute is not provided:
        result_indicator_baseline_location_attrs = {
            # 'ref': 'AF-KAN',
        }

        result_indicator_baseline_location_XML_element = E(
            'location',
            **result_indicator_baseline_location_attrs
        )

        try:
            self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline__location(  # NOQA: E501
                    result_indicator_baseline_location_XML_element
                )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'ref')
            self.assertEqual(inst.message,
                             "This attribute has to be a cross-reference to "
                             "the internal reference assigned to a defined "
                             "location: iati-activity/location/@ref, so "
                             "leaving it blank makes no sense")

        # 2. Referenced location doesn't exist:
        result_indicator_baseline_location_attrs = {
            'ref': 'AF-KAN',  # it's not 'KH-PNH'
        }

        result_indicator_baseline_location_XML_element = E(
            'location',
            **result_indicator_baseline_location_attrs
        )

        try:
            self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline__location(  # NOQA: E501
                    result_indicator_baseline_location_XML_element
                )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'ref')

            self.assertEqual(
                inst.message,
                "Referenced location doesn't exist"
            )

        # 3. Referenced location isn't referenced on an activity level:
        result_indicator_baseline_location_attrs = {
            'ref': 'KH-PNH',
        }

        result_indicator_baseline_location_XML_element = E(
            'location',
            **result_indicator_baseline_location_attrs
        )

        try:
            self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline__location(  # NOQA: E501
                    result_indicator_baseline_location_XML_element
                )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'ref')

            self.assertEqual(
                inst.message,
                "Referenced location has to be referenced on an Activity level"
            )

        # 4. all is good:

        self.activity.location_set.add(self.location)

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__baseline__location(  # NOQA: E501
                result_indicator_baseline_location_XML_element
            )

        referenced_location = self.parser_203.get_model('Location')

        self.assertEqual(
            referenced_location.result_indicator_baseline,
            self.result_indicator_baseline,
        )


class ActivityResultIndicatorBaselineDocumentLinkTestCase(TestCase):
    """
    2.03: The optional <document-link> element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        current_version = VersionFactory(code='2.03')

        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )
        self.result_indicator_baseline = iati_factory\
            .ResultIndicatorBaselineFactory.create()

        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model(
            'ResultIndicatorBaseline',
            self.result_indicator_baseline
        )

    def test_activity_result_indicator_baseline_document_link(self):
        '''Tests <document-link> in a baseline in a indicator in a result
        element is parsed and saved correctly
        '''

        # Case 1:
        #  'url is missing'

        result_indicator_baseline_document_link_attr = {
            # url = 'missing'
            "format": 'something'
            # 'format' will be retrieved in the function
        }
        result_indicator_baseline_document_link_XML_element = E(
            'document_link',
            **result_indicator_baseline_document_link_attr
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__baseline__document_link(  # NOQA: E501
                    result_indicator_baseline_document_link_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'url')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 2:
        # 'file_format' is missing

        result_indicator_baseline_document_link_attr = {
            "url": 'www.google.com'
            # "format":
            # 'format_code' will be retrieved in the function
        }
        result_indicator_baseline_document_link_XML_element = E(
            'document-link',
            **result_indicator_baseline_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__baseline__document_link(  # NOQA: E501
                    result_indicator_baseline_document_link_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 3;
        # 'file_format_code' is missing

        result_indicator_baseline_document_link_attr = {
            "url": 'www.google.com',
            "format": 'something',
            # 'format_code will be retrieved in the function
        }
        result_indicator_baseline_document_link_XML_element = E(
            'document-link',
            **result_indicator_baseline_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__baseline__document_link(  # NOQA: E501
                    result_indicator_baseline_document_link_XML_element
                )
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # Case 4;
        # all is good

        # dummy document-link object
        dummy_file_format = codelist_factory.\
            FileFormatFactory(code='application/pdf')

        dummy_document_link = iati_factory.\
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        result_indicator_baseline_document_link_attr = {
            "url": dummy_document_link.url,
            "format": dummy_file_format.code

        }
        result_indicator_baseline_document_link_XML_element = E(
            'document-link',
            **result_indicator_baseline_document_link_attr
        )

        self.parser_203 \
            .iati_activities__iati_activity__result__indicator__baseline__document_link(  # NOQA: E501
                result_indicator_baseline_document_link_XML_element
            )

        result_indicator_baseline_document_link = self\
            .parser_203.get_model(
                'DocumentLink'
            )

        # checking if everything is saved

        self.assertEqual(
            result_indicator_baseline_document_link.url,
            dummy_document_link.url
        )
        self.assertEqual(
            result_indicator_baseline_document_link.file_format,
            dummy_document_link.file_format
        )
        self.assertEqual(
            result_indicator_baseline_document_link.activity,
            self.activity
        )
        self.assertEqual(
            result_indicator_baseline_document_link.result_indicator_baseline,  # NOQA: E501
            self.result_indicator_baseline)


class ActivityResultIndicatorBaselineDocumentLinkDocumentDateTestCase(
    TestCase
):
    '''
    2.03: Added new (optional) <document-link> element for Result Indicator
    <baseline> element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_baseline_document_link_document_date(
        self
    ):
        '''
        Test if iso-date attribute in <document-link> XML element is
        correctly saved.
        '''

        # case 1: 'iso-date' is missing
        document_date_attr = {
            # "iso-date": '25116600000'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__indicator__baseline__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2 : 'iso-date' is not valid
        document_date_attr = {
            "iso-date": '25116600000'
        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__baseline__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'Unspecified or invalid. Date '
                                           'should be of type xml:date.')

        # case 3: 'iso-date' is not in correct range
        document_date_attr = {

            "iso-date": '18200915'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__baseline__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'iso-date not of type xsd:date')

        # all is good
        document_date_attr = {
            "iso-date": '2011-05-06'  # this is acceptable iso-date
        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__indicator__baseline__document_link__document_date(  # NOQA: E501
            document_date_XML_element
        )

        # Let's check if the date is saved

        date = dateutil.parser.parse('2011-05-06', ignoretz=True)

        document_link = self.parser_203.get_model('DocumentLink')
        self.assertEqual(date, document_link.iso_date)


class ActivityResultIndicatorBaselineDocumentLinkDescriptionTestCase(TestCase):
    """
    2.03: The optional <description> element of a <document-link> element was
    added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicatior_baseline_document_link_description(
        self
    ):
        '''test if <description> element for Activity Result Indicator Baseline
        <document-link> element is parsed and saved correctly
        '''

        document_link_description_attrs = {}

        result_document_link_XML_element = E(
            'description',
            **document_link_description_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__result__indicator__baseline__document_link__description(  # NOQA: E501
                result_document_link_XML_element
            )

        document_link_description = self.parser_203.get_model(
            'DocumentLinkDescription'
        )

        self.assertEqual(
            document_link_description.document_link,
            self.document_link
        )


class ActivityResultIndicatorBaselineDocumentLinkLanguageTestCase(
    TestCase
):

    """
    2.03: An optional <language> element of a document-link in a baseline in
    an indicator in a result element was added
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_result_indicator_baseline_document_link_language_element(
            self):
        '''
        Test if <language> element in <document-link> XML element is
        correctly parsed and saved.
        '''

        # case 1: 'code' is missing

        document_language_attr = {
            # "code": 'en'

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__indicator__baseline__document_link__language(  # NOQA: E501

                document_language_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2: 'language' is not found
        document_language_attr = {

            "code": 'ab'

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__baseline__document_link__language(  # NOQA: E501
                document_language_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'not found on the accompanying code list')

        # all is good
        language = codelist_factory.LanguageFactory()  # dummy language object
        document_language_attr = {

            "code": language.code

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__indicator__baseline__document_link__language(  # NOQA: E501
                document_language_XML_element
            )

        # Let's test language is saved

        document_link = self.parser_203.get_model('DocumentLink')
        document_link_language = self.parser_203.get_model(
            'DocumentLinkLanguage')
        self.assertEqual(document_link, document_link_language.document_link)
        self.assertEqual(language, document_link_language.language)


class ActivityResultIndicatorBaselineDocumentLinkCategoryTestCase(TestCase):

    """
    2.03: The optional <document-link> element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()
        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory.create()

        self.parser_203.register_model(
            'DocumentLink', self.document_link
        )

    def test_activity_result_indicator_baseline_document_link_category(self):
        """
        Test if <category> element of a document-link elment in a baseline in
        a indicator in a result element is correctly parsed and saved
        """

        # case 1: when code is missing

        document_link_category_attr = {
            # 'code': 'A04'

        }

        document_link_category_XML_element = E(
            'category',
            **document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__baseline__document_link__category(  # NOQA: E501
                document_link_category_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'required attribute missing')

        # case 2: when category cannot be retrieved using the given code
        document_link_category_attr = {
            'code': 'A04'

        }

        document_link_category_XML_element = E(
            'category',
            **document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__baseline__document_link__category(  # NOQA: E501
                document_link_category_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # case:  when all is good

        # Let's create dummy document_category
        document_category = codelist_factory.DocumentCategoryFactory(
            code='A04'
        )
        document_link_category_attr = {
            'code': document_category.code

        }

        document_link_category_XML_element = E(
            'category',
            **document_link_category_attr
        )

        self.parser_203.codelist_cache = {}

        self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline__document_link__category(  # NOQA: E501
                document_link_category_XML_element
            )
        # get DocumentLinkCategory

        document_link_category = self.parser_203.get_model(
            'DocumentLinkCategory')

        self.assertEqual(document_link_category.document_link, self.
                         document_link)
        self.assertEqual(document_link_category.category, document_category)


class ActivityResultIndicatorBaselineDimensionTestCase(TestCase):
    """
    2.03: The optional dimension element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()
        # Related objects:
        self.result_indicator_baseline = iati_factory.\
            ResultIndicatorBaselineFactory()

        self.parser_203.register_model(
            'ResultIndicatorBaseline', self.result_indicator_baseline
        )

    def test_activity_result_indicator_baseline_dimension(self):
        """
        Tests if <dimension> element in context of a baseline element (as part
        of a parent result/indicator element) is parsed and saved correctly
        """

        # case 1: 'name' attribute is missing:
        result_indicator_baseline_dimension_attrs = {
            # 'name': 'sex'
        }

        result_indicator_baseline_dimension_XML_element = E(
            'dimension',
            **result_indicator_baseline_dimension_attrs
        )

        try:
            self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline__dimension(  # NOQA: E501
                    result_indicator_baseline_dimension_XML_element
                )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'name')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2: 'value' attribute is missing:
        result_indicator_baseline_dimension_attrs = {
            'name': 'sex',
            # 'value': 'female'
        }

        result_indicator_baseline_dimension_XML_element = E(
            'dimension',
            **result_indicator_baseline_dimension_attrs
        )

        try:
            self.parser_203\
                .iati_activities__iati_activity__result__indicator__baseline__dimension(  # NOQA: E501
                    result_indicator_baseline_dimension_XML_element
                )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'value')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 3: all is good:
        result_indicator_baseline_dimension_attrs = {
            'name': 'sex',
            'value': 'female'
        }

        result_indicator_baseline_dimension_XML_element = E(
            'dimension',
            **result_indicator_baseline_dimension_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__baseline__dimension(  # NOQA: E501
                result_indicator_baseline_dimension_XML_element
            )

        result_indicator_baseline_dimension = self.parser_203.get_model(
            'ResultIndicatorBaselineDimension'
        )

        self.assertEqual(
            result_indicator_baseline_dimension.result_indicator_baseline,
            self.result_indicator_baseline
        )

        self.assertEqual(
            result_indicator_baseline_dimension.name,
            result_indicator_baseline_dimension_attrs['name']
        )

        self.assertEqual(
            result_indicator_baseline_dimension.value,
            result_indicator_baseline_dimension_attrs['value']
        )


class ActivityResultIndicatorPeriodTargetTestCase(TestCase):

    """
    2.03: this element can now be reported multiple times
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()
        # Related objects:
        self.result_indicator_period = iati_factory.\
            ResultIndicatorPeriodFactory()
        self.result_indicator = self.result_indicator_period.result_indicator
        self.activity = self.result_indicator.result.activity
        self.result = self.result_indicator.result

        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model('Result', self.result)
        self.parser_203.register_model(
            'ResultIndicator', self.result_indicator
        )
        self.parser_203.register_model(
            'ResultIndicatorPeriod', self.result_indicator_period
        )

    def test_activity_result_indicator_period_target(self):
        """
        test if <target> element within period, in context of an indicator in
        a result element is parsed and saved correctly
        """

        # 1) test if value is not provided:
        result_indicator_period_target_attrs = {
            # 'value': '11'
        }

        result_indicator_period_target_XML_element = E(
            'target',
            **result_indicator_period_target_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__target(  # NOQA: E501
                result_indicator_period_target_XML_element
            )

        result_indicator_period_target = self.parser_203.get_model(
            'ResultIndicatorPeriodTarget')

        self.assertEqual(
            result_indicator_period_target.value,
            ''
        )

        # 2) test if value is provided:
        result_indicator_period_target_attrs = {
            'value': '11'
        }

        result_indicator_period_target_XML_element = E(
            'target',
            **result_indicator_period_target_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__target(  # NOQA: E501
                result_indicator_period_target_XML_element
            )

        result_indicator_period_target = self.parser_203.get_model(
            'ResultIndicatorPeriodTarget')

        self.assertEqual(
            result_indicator_period_target.value,
            result_indicator_period_target_attrs['value']
        )

        # 3) test multiple target elements:

        # FIRST ResultIndicatorPeriodTarget:
        result_indicator_period_target_attrs = {
            'value': '20'
        }

        result_indicator_period_target_XML_element = E(
            'target',
            **result_indicator_period_target_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__target(  # NOQA: E501
                result_indicator_period_target_XML_element
            )

        # SECOND ResultIndicatorPeriodTarget:
        result_indicator_period_target_attrs2 = {
            'value': '21'
        }

        result_indicator_period_target_XML_element2 = E(
            'target',
            **result_indicator_period_target_attrs2
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__target(  # NOQA: E501
                result_indicator_period_target_XML_element2
            )

        # all unassigned FK relationships are assigned here:
        self.parser_203.save_all_models()

        self.result_indicator_period.refresh_from_db()

        # check ForeignKey assignments:
        result_indicator_period_target = self.parser_203.get_model(
            'ResultIndicatorPeriodTarget')

        self.assertEqual(
            result_indicator_period_target.result_indicator_period,
            self.result_indicator_period
        )

        # check 'value' attributes:

        # it's 4 because during the test we asigned 1) '', 2) 11, 3) 20 & 21:
        self.assertEqual(self.result_indicator_period.targets.count(), 4)

        self.assertListEqual(
            ['', '11', '20', '21'],
            list(self.result_indicator_period.targets.values_list(
                'value', flat=True
            ))
        )


class ActivityResultIndicatorPeriodTargetDocumentLinkTestCase(TestCase):

    """
    2.03: The optional <document-link> element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        current_version = VersionFactory(code='2.03')

        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )
        self.result_indicator_period_target = iati_factory\
            .ResultIndicatorPeriodTargetFactory.create()

        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model(
            'ResultIndicatorPeriodTarget',
            self.result_indicator_period_target
        )

    def test_activity_result_indicatior_period_target_document_link(  # NOQA: E501
        self
    ):
        '''test if <document-link> element in a target in a period in a
        indicator in a result element is parsed and saved correctly
        '''

        # Case 1:
        #  'url is missing'

        result_indicator_period_target_document_link_attr = {
            # url = 'missing'
            "format": 'something'
            # 'format' will be got in the function

        }
        result_indicator_period_target_document_link_XML_element = E(
            'document_link',
            **result_indicator_period_target_document_link_attr
        )

        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__period__target__document_link(  # NOQA: E501
                    result_indicator_period_target_document_link_XML_element)
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'url')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 2:
        # 'file_format' is missing

        result_indicator_period_target_document_link_attr = {
            "url": 'www.google.com'

            # "format":
            # 'format_code' will be got in the function

        }
        result_indicator_period_target_document_link_XML_element = E(
            'document-link',
            **result_indicator_period_target_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__period__target__document_link(  # NOQA: E501
                    result_indicator_period_target_document_link_XML_element
                )
            self.assertFail()
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 3;
        # 'file_format_code' is missing

        result_indicator_period_target_document_link_attr = {
            "url": 'www.google.com',
            "format": 'something',
            # 'format_code will be got in the function

        }
        result_indicator_period_target_document_link_XML_element = E(
            'document-link',
            **result_indicator_period_target_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__period__target__document_link(  # NOQA: E501
                    result_indicator_period_target_document_link_XML_element
                )
            self.assertFail()
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # Case 4;
        # all is good

        # dummy document-link object
        dummy_file_format = codelist_factory.\
            FileFormatFactory(code='application/pdf')

        dummy_document_link = iati_factory.\
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        result_indicator_period_target_document_link_attr = {
            "url": dummy_document_link.url,
            "format": dummy_file_format.code

        }
        result_indicator_period_target_document_link_XML_element = E(
            'document-link',
            **result_indicator_period_target_document_link_attr
        )

        self.parser_203 \
            .iati_activities__iati_activity__result__indicator__period__target__document_link(  # NOQA: E501
                result_indicator_period_target_document_link_XML_element
            )

        result_indicator_period_target_document_link = self\
            .parser_203.get_model(
                'DocumentLink'
            )

        # checking if everything is saved

        self.assertEqual(
            result_indicator_period_target_document_link.url,
            dummy_document_link.url
        )
        self.assertEqual(
            result_indicator_period_target_document_link.file_format,
            dummy_document_link.file_format
        )
        self.assertEqual(
            result_indicator_period_target_document_link.activity,
            self.activity
        )
        self.assertEqual(
            result_indicator_period_target_document_link.result_indicator_period_target,  # NOQA: E501
            self.result_indicator_period_target)


class ActivityResultIndicatorBaselineDocumentLinkTitleTestCase(
        TestCase):

    """
    2.03: The optional <document-link> element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Version
        current_version = VersionFactory(code='2.03')

        # Related objects:
        self.activity = iati_factory.ActivityFactory.create(
            iati_standard_version=current_version
        )
        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicatior_baseline_document_link_title(
            self):

        '''
        Test if <title> element in <document-link> XML element is correctly
        saved.
        '''

        dummy_file_format = codelist_factory. \
            FileFormatFactory(code='application/pdf')

        dummy_document_link = iati_factory. \
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        result_indicator_baseline_document_link_attr = {
            "url": dummy_document_link.url,
            "format": dummy_file_format.code

        }
        result_indicator_baseline_document_link_XML_element = E(
            'document-link',
            **result_indicator_baseline_document_link_attr
        )
        self.parser_203 \
            .iati_activities__iati_activity__result__indicator__baseline__document_link__title(  # NOQA: E501
                result_indicator_baseline_document_link_XML_element)
        document_link_title = self.parser_203.get_model(
            'DocumentLinkTitle')

        self.assertEqual(self.document_link,
                         document_link_title.document_link)


class ActivityResultIndicatorPeriodTargetDocumentLinkCategoryTestCase(
        TestCase):

    """
    2.03: The optional <document-link> element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()
        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory.create()

        self.parser_203.register_model(
            'DocumentLink', self.document_link
        )

    def test_activity_result_indicatior_period_target_document_link_category(self):  # NOQA: E501
        '''test if <document-link>'s <category> element in a target in a period
        in an indicator in a result element is parsed and saved correctly
        '''

        # case 1: when code is missing

        result_indicator_period_target_document_link_category_attr = {
            # 'code': 'A04'

        }

        result_indicator_period_target_document_link_category_XML_element = E(
            'category',
            **result_indicator_period_target_document_link_category_attr
        )
        try:
            self\
            .parser_203\
            .iati_activities__iati_activity__result__indicator__period__target__document_link__category(  # NOQA: E501
                result_indicator_period_target_document_link_category_XML_element  # NOQA: E501
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'required attribute missing')

        # case 2: when category cannot be retrieved using the given code
        result_indicator_period_target_document_link_category_attr = {
            'code': 'A04'

        }

        result_indicator_period_target_document_link_category_XML_element = E(
            'category',
            **result_indicator_period_target_document_link_category_attr
        )
        try:
            self\
            .parser_203\
            .iati_activities__iati_activity__result__indicator__period__target__document_link__category(  # NOQA: E501
                result_indicator_period_target_document_link_category_XML_element  # NOQA: E501
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # case:  when all is good

        # Let's create dummy document_category
        indicator_document_category = codelist_factory.DocumentCategoryFactory(
            code='A04'
        )
        result_indicator_period_target_document_link_category_attr = {
            'code': indicator_document_category.code

        }

        result_indicator_period_target_document_link_category_XML_element = E(
            'category',
            **result_indicator_period_target_document_link_category_attr
        )

        self.parser_203.codelist_cache = {}

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__target__document_link__category(  # NOQA: E501
                    result_indicator_period_target_document_link_category_XML_element  # NOQA: E501
            )

        # get DocumentLinkCategory
        result_indicator_period_target_document_link_category = self.\
            parser_203.get_model(
                'DocumentLinkCategory'
            )

        self.assertEqual(
            result_indicator_period_target_document_link_category.document_link,  # NOQA E501
            self.document_link
        )
        self.assertEqual(
            result_indicator_period_target_document_link_category.category,
            indicator_document_category
        )


class ActivityResultIndicatorPeriodTargetDocumentLinkDescriptionTestCase(
    TestCase
):

    """
    2.03: The optional <description> element of a <document-link> element was
    added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicatior_period_target_document_link_description(  # NOQA: E501
        self
    ):
        '''test if <description> element for Activity Result Indicator Period
        Target's <document-link> element is parsed and saved correctly
        '''

        document_link_description_attrs = {}

        result_document_link_XML_element = E(
            'description',
            **document_link_description_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__result__indicator__period__target__document_link__description(  # NOQA: E501
                result_document_link_XML_element
            )

        document_link_description = self.parser_203.get_model(
            'DocumentLinkDescription'
        )

        self.assertEqual(
            document_link_description.document_link,
            self.document_link
        )


class ActivityResultIndicatorPeriodTargetDocumentLinkLanguageTestCase(
    TestCase
):

    """
    2.03: An optional language element of a document-link in a target in a
    period in a indicator in a result element was added
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_result_indicator_period_target_document_link_language_element(
            self):
        '''
        Test if <language> element in <document-link> XML element is
        correctly parsed and saved.
        '''

        # case 1: 'code' is missing

        document_language_attr = {
            # "code": 'en'

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__indicator__period__target__document_link__language(  # NOQA: E501

                document_language_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2: 'language' is not found
        document_language_attr = {

            "code": 'ab'

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__period__target__document_link__language(  # NOQA: E501
                document_language_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'not found on the accompanying code list')

        # all is good
        language = codelist_factory.LanguageFactory()  # dummy language object
        document_language_attr = {

            "code": language.code

        }
        document_language_XML_element = E(
            'language',
            **document_language_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__target__document_link__language(  # NOQA: E501
                document_language_XML_element
            )

        # Let's test language is saved

        document_link = self.parser_203.get_model('DocumentLink')
        document_link_language = self.parser_203.get_model(
            'DocumentLinkLanguage')
        self.assertEqual(document_link, document_link_language.document_link)
        self.assertEqual(language, document_link_language.language)


class ActivityResultIndicatorPeriodTargetDocumentLinkDocumentDateTestCase(
    TestCase
):
    '''
    2.03: Added new, optional <document-date> element of a document-link in a
    target in a period in an indicator in a result element
    '''

    def setUp(self):

        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_result_indicator_period_target_document_link_document_date(
            self):
        '''
        Test if iso-date attribute in <document-link> XML element is
        correctly parsed and saved.
        '''
        # case 1: 'iso-date' is missing

        document_date_attr = {
            # "iso-date": '25116600000'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__indicator__period__target__document_link__document_date(  # NOQA: E501

                document_date_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2 : 'iso-date' is not valid
        document_date_attr = {
            "iso-date": '25116600000'
        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__period__target__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'Unspecified or invalid. Date '
                                           'should be of type xml:date.')

        # case 3: 'iso-date' is not in correct range
        document_date_attr = {
            "iso-date": '18200915'
        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__period__target__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'iso-date not of type xsd:date')

        # all is good
        document_date_attr = {
            "iso-date": '2011-05-06'  # this is acceptable  iso-date
        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__target__document_link__document_date(  # NOQA: E501
            document_date_XML_element
        )

        # Let's test if the date is saved

        date = dateutil.parser.parse('2011-05-06', ignoretz=True)

        document_link = self.parser_203.get_model('DocumentLink')
        self.assertEqual(date, document_link.iso_date)


class ActivityResultIndicatorPeriodActualTestCase(TestCase):

    """
    2.03: this element can now be reported multiple times
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.result_indicator_period = iati_factory.\
            ResultIndicatorPeriodFactory()
        self.result_indicator = self.result_indicator_period.result_indicator
        self.activity = self.result_indicator.result.activity
        self.result = self.result_indicator.result

        self.parser_203.register_model('Activity', self.activity)
        self.parser_203.register_model('Result', self.result)
        self.parser_203.register_model(
            'ResultIndicator', self.result_indicator
        )
        self.parser_203.register_model(
            'ResultIndicatorPeriod', self.result_indicator_period
        )

    def test_activity_result_indicator_period_actual(self):
        """
        test if <actual> element within period, in context of an indicator in
        a result element is parsed and saved correctly
        """

        # 1) test if value is not provided:
        result_indicator_period_actual_attrs = {
            # 'value': '11'
        }

        result_indicator_period_actual_XML_element = E(
            'actual',
            **result_indicator_period_actual_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__actual(  # NOQA: E501
                result_indicator_period_actual_XML_element
            )

        result_indicator_period_actual = self.parser_203.get_model(
            'ResultIndicatorPeriodActual')

        self.assertEqual(
            result_indicator_period_actual.value,
            ''
        )

        # 2) test if value is provided:
        result_indicator_period_actual_attrs = {
            'value': '11'
        }

        result_indicator_period_actual_XML_element = E(
            'actual',
            **result_indicator_period_actual_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__actual(  # NOQA: E501
                result_indicator_period_actual_XML_element
            )

        result_indicator_period_actual = self.parser_203.get_model(
            'ResultIndicatorPeriodActual')

        self.assertEqual(
            result_indicator_period_actual.value,
            result_indicator_period_actual_attrs['value']
        )

        # 3) test multiple actual elements:

        # FIRST ResultIndicatorPeriodActual:
        result_indicator_period_actual_attrs = {
            'value': '20'
        }

        result_indicator_period_actual_XML_element = E(
            'actual',
            **result_indicator_period_actual_attrs
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__actual(  # NOQA: E501
                result_indicator_period_actual_XML_element
            )

        # SECOND ResultIndicatorPeriodActual:
        result_indicator_period_actual_attrs2 = {
            'value': '21'
        }

        result_indicator_period_actual_XML_element2 = E(
            'actual',
            **result_indicator_period_actual_attrs2
        )

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__actual(  # NOQA: E501
                result_indicator_period_actual_XML_element2
            )

        # all unassigned FK relationships are assigned here:
        self.parser_203.save_all_models()

        self.result_indicator_period.refresh_from_db()

        # check ForeignKey assignments:
        result_indicator_period_actual = self.parser_203.get_model(
            'ResultIndicatorPeriodActual')

        self.assertEqual(
            result_indicator_period_actual.result_indicator_period,
            self.result_indicator_period
        )

        # check 'value' attributes:

        # it's 4 because during the test we asigned 1) '', 2) 11, 3) 20 & 21:
        self.assertEqual(self.result_indicator_period.actuals.count(), 4)

        self.assertListEqual(
            ['', '11', '20', '21'],
            list(self.result_indicator_period.actuals.values_list(
                'value', flat=True
            ))
        )


class ActivityResultIndicatorPeriodActualDocumentLinkTestCase(TestCase):

    """
    2.03: The optional document-link element was added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.parser_203.default_lang = "en"

        assert (isinstance(self.parser_203, Parser_203))

        # Related objects
        self.result_indicator_period_actual = iati_factory.\
            ResultIndicatorPeriodActualFactory.create()

        self.result_indicator = self.result_indicator_period_actual.\
            result_indicator_period.result_indicator

        self.activity = self.result_indicator.result.activity

        self.parser_203.register_model('Activity', self.activity)

        self.parser_203.register_model(
            'ResultIndicatorPeriodActual', self.result_indicator_period_actual
        )

    def test_activity_result_indicator_period_actual_document_link(self):
        """
        tests if 'url' and 'format' attributes of <document-link> element and
        all related objects are parsed and saved correctly

        """

        # Case 1: when 'url' is missing.
        result_indicator_period_actual_document_link_attr = {
            # url = 'something'
            "format": 'something'
            # "file_format" will be retrieved in the function
        }
        result_indicator_period_actual_document_link_XML_element = E(
            'document-link',
            **result_indicator_period_actual_document_link_attr
        )

        # testing if correct error message is returned
        try:
            self.parser_203. \
                iati_activities__iati_activity__result__indicator__period__actual__document_link(  # NOQA: E501
                result_indicator_period_actual_document_link_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'url')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 2: when 'file_format' is missing

        result_indicator_period_actual_document_link_attr = {
            "url": 'www.google.com'
            # "format": 'something'
            # "file_format" will be retrieved in the function
        }
        result_indicator_period_actual_document_link_XML_element = E(
            'document-link',
            **result_indicator_period_actual_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__period__actual__document_link(  # NOQA: E501
                result_indicator_period_actual_document_link_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'required attribute missing')

        # Case 3: when 'file_format' cannot be got from given 'format'

        result_indicator_period_actual_document_link_attr = {
            "url": 'www.google.com',
            "format": 'something',
            # "file_format" should be retrieved in the function but in this
            # case no file_format can be retrieved using given 'format'
        }
        result_indicator_period_actual_document_link_XML_element = E(
            'document-link',
            **result_indicator_period_actual_document_link_attr
        )
        try:
            self.parser_203.\
                iati_activities__iati_activity__result__indicator__period__actual__document_link(  # NOQA: E501
                result_indicator_period_actual_document_link_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'format')
            self.assertEqual(inst.message, 'not found on the accompanying '
                             'code list')

        # Case 4: when all is good

        # create dummy objects
        dummy_file_format = codelist_factory.\
            FileFormatFactory(code='application/pdf')

        self.parser_203.codelist_cache = {}

        result_indicator_period_actual_document_link_attr = {
            "url": 'http://aasamannepal.org.np/',
            "format": dummy_file_format.code
        }

        result_indicator_period_actual_document_link_XML_element = E(
            'document-link',
            **result_indicator_period_actual_document_link_attr
        )
        self.parser_203.\
            iati_activities__iati_activity__result__indicator__period__actual__document_link(  # NOQA: E501
            result_indicator_period_actual_document_link_XML_element
        )
        result_indicator_period_actual_document_link = self.\
            parser_203.get_model('DocumentLink')

        # Check if everything is correctly saved
        self.assertEqual(result_indicator_period_actual_document_link.activity,
                         self.activity)

        self.assertEqual(result_indicator_period_actual_document_link.url,
                         result_indicator_period_actual_document_link_attr.
                         get('url'))

        self.assertEqual(result_indicator_period_actual_document_link.
                         file_format,
                         dummy_file_format)

        self.assertEqual(result_indicator_period_actual_document_link.
                         result_indicator_period_actual,
                         self.result_indicator_period_actual)


class ActivityResultIndicatorPeriodActualDocumentLinkDescriptionTestCase(
    TestCase
):

    """
    2.03: The optional <description> element of a <document-link> element was
    added.
    """

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_period_actual_document_link_description(self):  # NOQA: E501
        '''test if <description> element for Activity Result Indicator Period
        Actual's <document-link> element is parsed and saved correctly
        '''

        document_link_description_attrs = {}

        result_document_link_XML_element = E(
            'description',
            **document_link_description_attrs
        )

        self.parser_203.\
            iati_activities__iati_activity__result__indicator__period__actual__document_link__description(  # NOQA: E501
                result_document_link_XML_element
            )

        document_link_description = self.parser_203.get_model(
            'DocumentLinkDescription'
        )

        self.assertEqual(
            document_link_description.document_link,
            self.document_link
        )


class AcitivityResultIndicatorPeriodActualDocumentLinkLanguageTestCase(
        TestCase):
    '''
    2.03: Added new (optional) <document-link> element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_period_actual_document_link_language(
            self):
        '''
        Test if <language> element of a document-link in a actual in a period
        in a indicator in a result element is correctly parsed and saved
        '''

        # case 1: 'code' is missing

        document_link_language_attr = {
            # "code": 'en'

        }
        document_link_language_XML_element = E(
            'document-date',
            **document_link_language_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__indicator__period__actual__document_link__language(  # NOQA: E501

                document_link_language_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2: 'language' is not found
        document_link_language_attr = {

            "code": 'ab'

        }
        document_link_language_XML_element = E(
            'language',
            **document_link_language_attr
        )
        try:
            self.parser_203. \
                iati_activities__iati_activity__result__indicator__period__actual__document_link__language(  # NOQA: E501
                    document_link_language_XML_element
                )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'not found on the accompanying code list')

        # all is good
        language = codelist_factory.LanguageFactory()  # dummy language object
        document_link_language_attr = {

            "code": language.code

        }
        document_link_language_XML_element = E(
            'language',
            **document_link_language_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__actual__document_link__language(  # NOQA: E501
                document_link_language_XML_element
            )

        # Let's test language is saved

        document_link = self.parser_203.get_model('DocumentLink')
        document_link_language = self.parser_203.get_model(
            'DocumentLinkLanguage')
        self.assertEqual(document_link, document_link_language.document_link)
        self.assertEqual(language, document_link_language.language)


class AcitivityResultIndicatorPeriodActualDocumentLinkTitleTestCase(TestCase):
    """
    2.03: The optional  <document-link> element was
    added.

    """
    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_period_actual_document_link_title(self):
        """
        test if <title> element for Activity Result Indicator Period
        Actual's <document-link> element is parsed and saved correctly

        """
        dummy_file_format = codelist_factory. \
            FileFormatFactory(code='application/pdf')

        dummy_indicator_period_actual_document_link = iati_factory. \
            DocumentLinkFactory(url='http://aasamannepal.org.np/')

        self.parser_203.codelist_cache = {}

        indicator_period_actual_document_link_attr = {
            "url": dummy_indicator_period_actual_document_link.url,
            "format": dummy_file_format.code

        }
        indicator_period_actual_document_link_XML_element = E(
            'document-link',
            **indicator_period_actual_document_link_attr
        )
        self.parser_203 \
            .iati_activities__iati_activity__result__indicator__period__actual__document_link__title(  # NOQA: E501
            indicator_period_actual_document_link_XML_element)

        document_link_title = self.parser_203.get_model(
            'DocumentLinkTitle')

        self.assertEqual(self.document_link,
                         document_link_title.document_link)


class AcitivityResultIndicatorPeriodActualDocumentLinkCategoryTestCase(
        TestCase):
    """
    2.03: The optional  <document-link> element was
    added.

    """
    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_period_actual_document_link_category(
            self):
        """
        Test if <category> element of a document-link in a actual in a period
        in a indicator in a result element is parsed and saved correctly
        """

        # case 1: when code is missing
        indicator_document_link_category_attr = {
            # 'code': 'A04'

        }

        indicator_document_link_category_XML_element = E(
            'category',
            **indicator_document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__period__actual__document_link__category(  # NOQA: E501
                indicator_document_link_category_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'required attribute missing')

        # case 2: when category cannot be retrieved using the given code
        indicator_document_link_category_attr = {
            'code': 'A04'

        }

        indicator_document_link_category_XML_element = E(
            'category',
            **indicator_document_link_category_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__period__actual__document_link__category(  # NOQA: E501
                indicator_document_link_category_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message, 'not found on the accompanying '
                                           'code list')

        # case:  when all is good

        # Let's create dummy document_category
        indicator_document_category = \
            codelist_factory.DocumentCategoryFactory(
                code='A04'
            )
        indicator_document_link_category_attr = {
            'code': indicator_document_category.code

        }

        indicator_document_link_category_XML_element = E(
            'category',
            **indicator_document_link_category_attr
        )

        self.parser_203.codelist_cache = {}

        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__actual__document_link__category(  # NOQA: E501
                indicator_document_link_category_XML_element
            )
        # get DocumentLinkCategory

        indicator_document_link_category = self.parser_203.get_model(
            'DocumentLinkCategory')

        self.assertEqual(indicator_document_link_category.document_link, self.
                         document_link)
        self.assertEqual(indicator_document_link_category.category,
                         indicator_document_category)


class ActivityResultIndicatorPeriodActualDocumentLinkDocumentDateTestCase(TestCase):  # NOQA: E501
    '''
    2.03: Added new (optional) <document-link> element for <actual> element
    inside <result> <indicator>'s <period> element
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        self.document_link = iati_factory.DocumentLinkFactory. \
            create(url='http://someuri.com')

        self.parser_203.register_model('DocumentLink', self.document_link)

    def test_activity_result_indicator_period_actual_document_link_document_date(self):  # NOQA: E501
        '''
        Test if iso-date attribute in <document-link> XML element is
        correctly saved.
        '''

        # case 1: 'iso-date' is missing

        document_date_attr = {
            # "iso-date": '25116600000'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.date = self.parser_203 \
                 .iati_activities__iati_activity__result__indicator__period__actual__document_link__document_date(  # NOQA: E501

                document_date_XML_element

            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'required attribute missing')

        # case 2 : 'iso-date' is not valid
        document_date_attr = {

            "iso-date": '25116600000'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )

        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__period__actual__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'Unspecified or invalid. Date '
                                           'should be of type xml:date.')

        # case 3: 'iso-date' is not in correct range
        document_date_attr = {

            "iso-date": '18200915'

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        try:
            self.parser_203.iati_activities__iati_activity__result__indicator__period__actual__document_link__document_date(  # NOQA: E501
                document_date_XML_element
            )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'iso-date')
            self.assertEqual(inst.message, 'iso-date not of type xsd:date')

        # all is good
        document_date_attr = {

            "iso-date": '2011-05-06'  # this is acceptable  iso-date

        }
        document_date_XML_element = E(
            'document-date',
            **document_date_attr
        )
        self.parser_203\
            .iati_activities__iati_activity__result__indicator__period__actual__document_link__document_date(  # NOQA: E501
            document_date_XML_element
        )

        # Let's test if the date is saved

        date = dateutil.parser.parse('2011-05-06', ignoretz=True)

        document_link = self.parser_203.get_model('DocumentLink')
        self.assertEqual(date, document_link.iso_date)


class ActivityResultReferenceTestCase(TestCase):

    '''
    2.03: Added new (optional) <reference> element for <result>
    element.
    '''

    def setUp(self):
        # 'Main' XML file for instantiating parser:
        xml_file_attrs = {
            "generated-datetime": datetime.datetime.now().isoformat(),
            "version": '2.03',
        }
        self.iati_203_XML_file = E("iati-activities", **xml_file_attrs)

        dummy_source = synchroniser_factory.DatasetFactory.create()

        self.parser_203 = ParseManager(
            dataset=dummy_source,
            root=self.iati_203_XML_file,
        ).get_parser()

        # Related objects:
        # create dummy object
        self.result_vocabulary = ResultVocabularyFactory(code='99')
        self.result = iati_factory.ResultFactory.create()

        self.parser_203.register_model('Result', self.result)

    def test_activity_result_reference(self):
        """
        Test if result, code, vocabulary_uri attributes in <reference> XML
        element is correctly saved.
        """

        # case 1: where 'vocabulary' is missing

        reference_attr = {
            # "vocabulary": result_vocabulary.code,
            "code": '01',
            "vocabulary-uri": 'www.example.com'

        }
        reference_XML_element = E(
            'reference',
            **reference_attr
        )
        try:
            self.parser_203 \
            .iati_activities__iati_activity__result__reference(  # NOQA: E501
            reference_XML_element
            )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(inst.message,
                             'required attribute missing')

        # case 2: where 'vocabulary' cannot be found because of non-existent
        #  vocabulary_code '100'

        reference_attr = {
            "vocabulary": '100',
            "code": '01',
            "vocabulary-uri": 'www.example.com'

        }
        reference_XML_element = E(
            'reference',
            **reference_attr
        )
        try:
            self.parser_203 \
                .iati_activities__iati_activity__result__reference(
                    reference_XML_element
                )
        except FieldValidationError as inst:
            self.assertEqual(inst.field, 'vocabulary')
            self.assertEqual(inst.message,
                             'not found on the accompanying code list')

        # case 3: where 'code' is missing

        reference_attr = {
            "vocabulary": self.result_vocabulary.code,
            # "code": '01',
            "vocabulary-uri": 'www.example.com'

        }
        reference_XML_element = E(
            'reference',
            **reference_attr
        )
        try:
            self.parser_203 \
                .iati_activities__iati_activity__result__reference(
                    reference_XML_element
                )
        except RequiredFieldError as inst:
            self.assertEqual(inst.field, 'code')
            self.assertEqual(inst.message,
                             'Unspecified or invalid.')

        # case 4: where 'vocabulary_uri' is missing. This case is not tested
        # because 'vocabulary_uri' is optional.

        # case 5: all is good
        reference_attr = {
            "vocabulary": self.result_vocabulary.code,
            "code": '01',
            "vocabulary-uri": 'www.example.com'
        }

        reference_XML_element = E(
            'reference',
            **reference_attr
        )
        self.parser_203 \
            .iati_activities__iati_activity__result__reference(  # NOQA: E501
                reference_XML_element
            )

        # get 'ResultReference to check if its attributes are correctly stored
        reference = self.parser_203.get_model('ResultReference')

        # check everything is correctly stored
        self.assertEqual(self.result, reference.result)
        self.assertEqual(reference_attr.get('code'),
                         reference.code)
        self.assertEqual(reference_attr.get('vocabulary-uri'),
                         reference.vocabulary_uri)