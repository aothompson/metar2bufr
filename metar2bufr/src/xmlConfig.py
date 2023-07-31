#
# Name: xmlConfig.py
# Purpose: To provide TAC->IWXXM and TAC->USWX decoders & encoders with
# site-specific information and customized settings
#
# Author: Mark Oberfield
# Organization: NOAA/NWS/OSTI/Meteorological Development Laboratory
# Contact Info: Mark.Oberfield@noaa.gov
# Date: 16 January 2020
#
import os
import re
#
os.environ['TZ'] = 'GMT0'
# -----------------------------------------------------------------------------------
#
# If this centre or office is performing bulk TAC->XML translations, or TAC->XML
# translations on behalf of another country, then TRANSLATOR should be set to true
# and its name and designator provided.
#
# For Meteorological or Space Weather Watch offices running this software, TRANSLATOR
# should be set to False.
#
TRANSLATOR = True
#
# The full name and identifier of translation centre running this software
#
TranslationCentreName = 'NCEP Central Operations'
TranslationCentreDesignator = 'KWNO'
#
# -----------------------------------------------------------------------------------
#
# The remainder of this file is relatively static, requiring updates when either:
# IWXXM versioning changes, WMO Code Registry and/or Annex 3 or WMO 306 changes.
#
# -----------------------------------------------------------------------------------
#
# IWXXM versioning
_iwxxm = '3.0'
_release = '3.0'
#
IWXXM_URI = 'http://icao.int/iwxxm/%s' % _iwxxm
IWXXM_URL = 'http://schemas.wmo.int/iwxxm/%s/iwxxm.xsd' % _release
#
# Path to file containing codes obtained from WMO Code Registry in RDF/XML format.
#
CodesFilePath = os.path.join(os.path.dirname(__file__), '../data')
#
# To support Annex 3 code forms, the following Containers from the WMO Code Registry
# site were downloaded into the CodesFilePath directory in RDF format.
#
# These are needed for MDL's IWXXM Encoders
#
CLDAMTS = 'CloudAmountReportedAtAerodrome'
COLOUR_CODES = 'AviationColourCode'
CVCTNCLDS = 'SigConvectiveCloudType'
NIL = 'nil'
RECENTWX = 'AerodromeRecentWeather'
RWYDEPST = '0-20-086'
RWYCNTMS = '0-20-087'
RWYFRCTN = '0-20-089'
SEACNDS = '0-22-061'
SWX_PHENOMENA = 'SpaceWxPhenomena'
SWX_LOCATION = 'SpaceWxLocation'
WEATHER = 'AerodromePresentOrForecastWeather'
#
# NIL reason values
MSSG = 'missing'
NA = 'inapplicable'
NOAUTODEC = 'notDetectedByAutoSystem'
NOOBSV = 'notObservable'
NOOPRSIG = 'nothingOfOperationalSignificance'
NOSIGC = 'noSignificantChange'
UNKNWN = 'unknown'
WTHLD = 'withheld'
#
# Coordinate Reference System used for all IWXXM messages. axisLabels and srsDimension
# must be consistent with CRS specified with srsName.
#
srsName = 'http://www.opengis.net/def/crs/EPSG/0/4326'
axisLabels = 'Lat Long'
srsDimension = '2'
#
# METAR/SPECI and TAF variables
# ---------------------------------------------------------------------------------------------
# If elevation of the aerodrome is provided, then provide the vertical datum it is
# based on and its unit of measure
#
useElevation = False
#
# Vertical datum must be set correctly for the elevation used. Allowed values are:
# 'EGM_96', 'AHD', 'NAVD88' or string matching the regular expression pattern:
#
# 'OTHER:(\w|_){1,58}'
#
verticalDatum = 'EGM_96'
#
# Elevation value unit of measure (UOM). Either 'FT' or 'M' or string matching the
# regular expression pattern:
#
# 'OTHER:(\w|_){1,58}'
#
elevationUOM = 'M'
#
# xlink:title attributes are optional in IWXXM XML documents. TITLES variable below
# determines whether they are displayed in TAF, METAR and SPECI reports
#
# If no xlink:title attributes are wanted in IWXXM XML documents, set TITLES to 0 (zero).
# Otherwise, set bits appropriately.
#
# Bit masks
Weather = 1 << 0
CloudAmt = 1 << 1
CloudType = 1 << 2
SeaCondition = 1 << 3
#
TITLES = 0
# TITLES=(CloudAmt|CloudType|SeaCondition)
#
# If xlink:titles are to appear in the document, set preferred language. English, 'en',
# is the default if the desired language is not found in the WMO Code Registry.
#
PreferredLanguageForTitles = 'en'
#
# Variables affecting METAR/SPECI Runway conditions. Depreciated, but keep for now.
#
NIL_SNOCLO_URL = 'http://codes.wmo.int/bufr4/codeflag/0-20-085/1'
RunwayDeposit = 1 << 4
AffectedRunwayCoverage = 1 << 5
RunwayFriction = 1 << 6
RunwayFrictionValues = {'91': 'Braking action poor', '92': 'Braking action medium to poor',
                        '93': 'Braking action medium', '94': 'Braking action medium to good',
                        '95': 'Braking action good', '99': 'Unreliable'}
#
# If prevailing horizontal visibility falls below this value (metres), RVR information
# should be supplied
#
RVR_MaximumDistance = 1500
#
# Critera for including sector visibility under the iwxxm namespace. See Recommendation
# 4.2.4.4a in Annex 3
#
Max_SectorVisibility_1 = 1500
Max_SectorVisibility_2 = 5000
Max_PercentageOfPrevailing = 50
#
# The use of CAVOK introduces potential ambiguities when conditions are forecasted to
# change during the TAF period of validity.
#
# When a forecast group introduces changes to sky or visibility conditions (and not both at
# the same time), it is not clear how the other elment is affected and the IWXXM schematron
# rule, TAF.TAF-8, requires both to be known when CAVOK is not in effect.
#
# By setting the 'noImpliedCAVOKCondition' to True, the TAF decoder will flag this forecast
# group to the forecaster for remediation.
#
# If noImpliedCAVOKCondition is set to False, then the missing element will be inserted
# into the forecast.  If visibility is missing, it will be set to >10km.  If sky condition
# is missing, it will be set to 'NSC' (no significant cloud).  By default, a message
# will be written to the log file indicating this action. By setting
# emitImpliedCAVOKConditionMessages, these messages will not be written to the log file.
#
noImpliedCAVOKCondition = True
emitImpliedCAVOKConditionMessage = True  # Only effective when noImpliedCAVOKCondition is False
# ---------------------------------------------------------------------------------------------
# Information is needed for Space Weather Advisories
#
# DAYLIGHTSIDE is the radius of the circle that circumscribes the daylight side of the
# Earth which is approximately one-quarter of the Earth's circumference
#
DAYLIGHTSIDE = 'DAYLIGHT_SIDE'
DAYLIGHTSIDE_RADIUS = '10100'
#
# DAYLIGHTSIDE_UOM, only [mi_i] or 'km' is allowed
DAYLIGHTSIDE_UOM = 'km'
#
# Whether latitude bands in SWX product are combined
JOIN_BANDS = False
# -----------------------------------------------------------------------------------
#
# IWXXM-US versioning
_us_iwxxm = '3.0'
_us_iwxxm_release = '3.0'
#
# USWX versioning
_uswx = '1.0'
_uswx_release = '1.0'
#
# US Code Registry for Meteorological Services
OFCM_CODE_REGISTRY_URL = 'https://codes.nws.noaa.gov'
#
# IWXXM-US URI and URLs
IWXXM_US_URI = 'http://www.weather.gov/iwxxm-us/%s' % _us_iwxxm
IWXXM_US_URL = 'https://nws.weather.gov/schemas/iwxxm-us/%s/' % _us_iwxxm_release
IWXXM_US_METAR_URL = 'https://nws.weather.gov/schemas/iwxxm-us/%s/metarSpeci.xsd' % _us_iwxxm_release
#
# USWX_URI and URLs
USWX_URI = 'http://nws.weather.gov/schemas/USWX/%s' % _uswx
USWX_URL = 'https://nws.weather.gov/schemas/uswx/%s' % _uswx_release
#
# For non-Annex 3 content in US METAR/SPECI reports
ACCUMLTN = 'http://codes.wmo.int/grib2/codeflag/4.10/1'
MAXIMUM = 'http://codes.wmo.int/grib2/codeflag/4.10/2'
MINIMUM = 'http://codes.wmo.int/grib2/codeflag/4.10/3'
AERONAUTICALVIS = 'http://codes.wmo.int/common/quantity-kind/aeronauticalVisibility'

PRSRTNDCY = '0-10-063'
SKYCATALOG = '0-20-012'
#
# Surface observations with 'ICAO' identifers that match the following regular expression are considered
# to be based on FMH-1 or AFMAN 15-111 manuals. These patterns should only match aerodrome observations that
# are issued from the United States or overseas military bases.
#
CONUS = 'K[A-Z0-9]{3}'
ALASKA = 'P(A|F|O|P)[A-Z]{2}'
PACIFIC = 'P(G|H|K|L|M|W)[A-Z]{2}'
SAN_JUAN = 'TJ[A-Z]{2}|TIST|TISX|TKPK|TNCM'
USMIL_EURO = 'BGTL|EGUL|EGUN|EGVA|ETAD|ETAR'
USMIL_CUBA = 'MUGM'
USMIL_ME = 'OEPS|OTBH'
USMIL_ASIA = 'RJTY|RKJK|RKSG|RKSO|RKSY|RODN'
#
# Combine all identifiers into a list
FMH1_AFMAN = [CONUS, ALASKA, PACIFIC, SAN_JUAN, USMIL_EURO, USMIL_ASIA, USMIL_CUBA, USMIL_ME]
#
# Create the regular expression
isUSObservation = re.compile(r'(%s)' % '|'.join(FMH1_AFMAN))
