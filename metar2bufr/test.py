import re

import metar2bufr.src.metarDecoders as MD
import metar2bufr.src.xmlUtilities as deu

from copy import deepcopy
from typing import Iterator
import csv
from io import StringIO
import logging
import json
import math
from csv2bufr import BUFRMessage

LOGGER = logging.getLogger(__name__)

FAILED = 0
PASSED = 1

fmh = MD.FMH1()
annex3 = MD.Annex3()

re_ID = re.compile(r'(METAR|SPECI)\s+(COR\s+)?(?P<id>\w{4})')

# metar = "METAR NZFX 032155Z 00000KT 9999 BCFG FEW010 FEW030 M26/M29 A2873 RMK VIS GRID N 1600 SLP724 LSR10 SDN/HDP HDN GRID N-E="
# metar = "METAR KRZT 221615Z AUTO 08007KT 10SM SCT023 OVC038 20/13 A3003 RMK AO2 PWINO="
# metar = "METAR SPTN 102000Z 23013KT 9999 SCT050 SCT120 27/17 Q1013 RMK PP000="
# metar = "METAR KOGS 221610Z AUTO VRB03G11KT 10SM FEW049 26/14 A3017 RMK AO2="
# metar = "METAR KOWX 221615Z AUTO 08010KT 10SM BKN033 23/11 A3006 RMK AO1="
# metar = "METAR KABC 121755Z AUTO 21016G24KT 180V240 1SM R11/P6000FT -RA BR BKN015 OVC025 06/04 A2990="
# BKN015 OVC025

metar = "METAR KAFF 121755Z AUTO 21016G24KT 180V240 1SM R11/P6000FTU R12/P6000 R01L/0600VP6000FT -RA VA PO BKN015 OVC025TCU 06/04 A2990="
# metar = "METAR KABC 121755Z AUTO 21016G24KT 180V240 1SM R11/P6000FT -RA BR BKN015 OVC025 06/04 A2990="


_keys = ['report_type',
         'station_id',
         'year', 'month', 'day', 'hour', 'minute',
         'auto', 'cor', 'nil',
         'wind_direction', 'wind_speed', 'gust_speed', 'wind_uom', 'variable_extreme_ccw', 'variable_extreme_cw',
         'visibility', 'visibility_uom', 'visibility_variation', 'visiblity_variation_direction',
        #  'runway_designator_1', 'rvr_1_mean', 'rvr_1_low', 'rvr_1_high', 'tend_1',
        #  'runway_designator_2', 'rvr_2_mean', 'rvr_2_low', 'rvr_2_high', 'tend_2',
        #  'runway_designator_3', 'rvr_3_mean', 'rvr_3_low', 'rvr_3_high', 'tend_3',
        #  'runway_designator_4', 'rvr_4_mean', 'rvr_4_low', 'rvr_4_high', 'tend_4',
        #  'cloud_amount_1', 'cloud_height_1', 'sig_convec_1',
        #  'cloud_amount_2', 'cloud_height_2', 'sig_convec_2',
        #  'cloud_amount_3', 'cloud_height_3', 'sig_convec_3',
        #  'vertical_visibility', 'NSC', 'NCD',
         'air_temp', 'dew_point_temp',
         'altimeter', 'altimeter_uom']

metar_template = dict.fromkeys(_keys)

MAPPINGS = "/home/alexander.thompson/metardecoder/metar-mappings.json"

# Load template mappings file, this will be updated for each message.
with open(MAPPINGS) as fh:
    _mapping = json.load(fh)

def parse_metar(message: str, year: int, month: int) -> dict:
    icaoID = re_ID.match(message).group('id')
    if deu.isUSIdentifier(icaoID):
        decoded = fmh(message)
    else:
        decoded = annex3(message)

    output = deepcopy(metar_template)

    output['report_type'] = message[0:5]
    output['year'] = year
    output['month'] = month

    if 'ident' in decoded:
        # output['station_id'] = decoded['ident']['str']

        try:    # placeholder until we can convert from ICAO to traditional station identifier (tsi)
            tsi = '72403'
            output['station_id'] = tsi
            output['block_no'] = tsi[0:2]
            output['station_no'] = tsi[2:5]
        except Exception:
            tsi = None
            output['station_id'] = None
            output['block_no'] = None
            output['station_no'] = None

    if 'itime' in decoded:
        output['day'] = decoded['itime']['tuple'].tm_mday
        output['hour'] = decoded['itime']['tuple'].tm_hour
        output['minute'] = decoded['itime']['tuple'].tm_min

    if 'auto' in decoded:
        output['auto'] = 'AUTO'

    if 'cor' in decoded:
        output['cor'] = 'COR'

    if 'wind' in decoded:
        # Metar reports wind speed in knots and direction in degrees, both of which are compatible with bufr
        output['wind_direction'] = decoded['wind']['dd']
        output['wind_speed'] = decoded['wind']['ff']
        if 'gg' in decoded['wind']:
            output['gust_speed'] = decoded['wind']['gg']
        output['wind_uom'] = decoded['wind']['uom']
        if 'ccw' in decoded['wind']:
            output['variable_extreme_ccw'] = int(decoded['wind']['ccw'])
        if 'cw' in decoded['wind']:
            output['variable_extreme_cw'] = int(decoded['wind']['cw'])

    if 'vsby' in decoded:
        # Metar reports visibility in statute miles. Need to convert value to meters to be bufr compatible
        vis_miles = float(decoded['vsby']['value'])
        output['visibility'] = math.floor(vis_miles * 1609.34)
        output['visibility_uom'] = decoded['vsby']['uom']

    # TODO need to incorporate visibility variation as outlined in section 15.6.2 in FM-15 manual

    num_rvr = 0
    if 'rvr' in decoded:
        num_rvr = len(decoded['rvr']['str'])
        for i in range(num_rvr):
            output[f'rvr_{i+1}_designator'] = decoded['rvr']['rwy'][i]
            mean_vis = float(decoded['rvr']['mean'][i])
            # if distance is reported in meters, we can copy directly to bufr
            if decoded['rvr']['uom'][i] == 'm':
                output[f'rvr_{i+1}_mean'] = int(mean_vis)

            # if distance is reported in ft, have to convert to meters for bufr
            elif decoded['rvr']['uom'][i] == '[ft_i]':
                output[f'rvr_{i+1}_mean'] = math.floor(mean_vis*0.3048)
            # output['runway_designator_'+str(i+1)] = decoded['rvr']['rwy'][i]
            # output['rvr_'+str(i+1)+'_mean'] = decoded['rvr']['mean'][i]
            output[f'rvr_{i+1}_tend'] = decoded['rvr']['tend'][i]

    num_vrbrvr = 0
    if 'vrbrvr' in decoded:
        num_vrbrvr = len(decoded['vrbrvr']['str'])
        for i in range(num_vrbrvr):
            output[f'vrbrvr_{i+1}_designator'] = decoded['rvr']['rwy'][i]
            low_vis = float(decoded['vrbrvr']['lo'][i])
            high_vis = float(decoded['vrbrvr']['hi'][i])
            
            # if distance is reported in meters, we can copy directly to bufr
            if decoded['vrbrvr']['uom'][i] == 'm':
                output[f'vrbrvr_{i+1}_low'] = int(low_vis)
                output[f'vrbrvr_{i+1}_high'] = int(high_vis)

            # if distance is reported in ft, have to convert to meters for bufr
            elif decoded['vrbrvr']['uom'][i] == '[ft_i]':
                output[f'vrbrvr_{i+1}_low'] = math.floor(low_vis*0.3048)
                output[f'vrbrvr_{i+1}_high'] = math.floor(high_vis*0.3048)

    # if 'vrbrvr' in decoded:
    #     num_rvr = len(decoded['rvr']['str'])
    #     for i in range(len(decoded['vrbrvr']['str'])):
    #         output['runway_designator_'+str(i+1+num_rvr)] = decoded['vrbrvr']['rwy'][i]
    #         output['rvr_'+str(i+1+num_rvr)+'_low'] = decoded['vrbrvr']['lo'][i]
    #         output['rvr_'+str(i+1+num_rvr)+'_high'] = decoded['vrbrvr']['hi'][i]

    num_pcp = 0
    if 'pcp' in decoded:
        num_pcp = len(decoded['pcp']['str'])
        for i in range(num_pcp):
            output[f'precip_{i+1}'] = decoded['pcp']['str'][0]

    num_obv = 0
    if 'obv' in decoded:
        num_obv = len(decoded['obv']['str'])
        for i in range(num_obv):
            output[f'observed_phenom_{i+1}'] = decoded['obv']['str'][i]

    num_sky = 0
    if 'sky' in decoded:
        num_sky = len(decoded['sky']['str'])
        for i in range(num_sky):
            if decoded['sky']['str'][0][:2] == 'VV':
                # METAR reports vertical visibility in 100s of ft. Need to convert to meters for bufr
                vertical_visibility_ft = float(decoded['sky']['str'][0][3:]) * 100
                output['vertical_visibility'] = math.floor(vertical_visibility_ft*0.3048)
                # output['vertical_visibility'] = decoded['sky']['str'][0][3:]
                break
            #need to convert the recorded cloud amount to bufr using ecCode cloudAmount - table 020011
            cloud_amount = decoded['sky']['str'][i][:3]
            if cloud_amount == 'FEW':
                # table 020011 codes FEW clouds as 13
                output[f'cloud_amount_{i+1}'] = 13
            elif cloud_amount == 'SCT':
                # codes SCATTERED clouds as 11
                output[f'cloud_amount_{i+1}'] = 11
            elif cloud_amount == 'BKN':
                # codes BROKEN clouds as 12
                output[f'cloud_amount_{i+1}'] = 12
            elif cloud_amount == 'OVC':
                # table 020011 lists two codes that might work for OVERCAST clouds, 9 and 10. Hard coding as 10 for now
                output[f'cloud_amount_{i+1}'] = 10
            # convert reported cloud height from hundreds of ft. to meters for bufr
            cloud_height_ft = float(decoded['sky']['str'][i][3:6]) * 100
            output[f'cloud_height_{i+1}'] = math.floor(cloud_height_ft*0.3048)

            # TODO: capture significant convective clouds, namely TCU OR CB using ecCodes
            if len(decoded['sky']['str'][i]) > 6:
                output['sig_convec_'+str(i+1)] = decoded['sky']['str'][i][6:]

            #  TODO need to incorporate NSC and NCD values as described in section 15.9.1.3 of FM-15 manual
    # if 'sky' in decoded:
    #     for i in range(len(decoded['sky']['str'])):
    #         if decoded['sky']['str'][0][:2] == 'VV':
    #             output['vertical_visibility'] = decoded['sky']['str'][0][3:]
    #             break
    #         output['cloud_amount_'+str(i+1)] = decoded['sky']['str'][i][:3]
    #         output['cloud_height_'+str(i+1)] = decoded['sky']['str'][i][3:6]
    #         if len(decoded['sky']['str'][i]) > 6:
    #             output['sig_convec_'+str(i+1)] = decoded['sky']['str'][i][6:]

    #         #  TODO need to incorporate NSC and NCD values as described in section 15.9.1.3 of FM-15 manual

    if 'temps' in decoded:
        output['air_temp'] = decoded['temps']['air']
        output['dew_point_temp'] = decoded['temps']['dewpoint']

    if 'altimeter' in decoded:
        output['altimeter'] = decoded['altimeter']['value']
        output['altimeter_uom'] = decoded['altimeter']['uom']

    return decoded, num_pcp, num_obv, num_sky

def transform(data: str, metadata: str, year: int, month: int) -> Iterator[dict]:
    # ===================
    # First parse metadata file
    # ===================
    if isinstance(metadata, str):
        fh = StringIO(metadata)
        reader = csv.reader(fh, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        col_names = next(reader)
        metadata_dict = {}
        tsi_mapping = {}
        for row in reader:
            if len(row) == 0:
                continue
            single_row = dict(zip(col_names, row))
            tsi = single_row['traditional_station_identifier']
            try:
                wsi = single_row['wigos_station_identifier']
                metadata_dict[wsi] = deepcopy(single_row)
                if tsi in tsi_mapping:
                    LOGGER.warning(("Duplicate entries found for station"
                                    f" {tsi} in station list file"))
                tsi_mapping[tsi] = wsi
            except Exception as e:
                LOGGER.error(e)

        fh.close()
        # metadata = metadata_dict[wsi]
    else:
        LOGGER.error("Invalid metadata")
        raise ValueError
    
    result = dict()

    mapping = deepcopy(_mapping)

    conversion_success = {}

    try:
        msg, num_pcp, num_obv, num_sky = parse_metar(data, year, month)
        tsi = msg['station_id']
    except Exception as e:
        LOGGER.error(f"Error parsing METAR report: {data}. {str(e)}")
    
    try:
        wsi = tsi_mapping[tsi]
    except Exception:
        conversion_success[tsi] = False
        LOGGER.warning(f"Station {tsi} not found in station file")

    # parse WSI to get sections
    try:
        wsi_series, wsi_issuer, wsi_issue_number, wsi_local = wsi.split("-")   # noqa
        # get other required metadata
        latitude = metadata_dict[wsi]["latitude"]
        longitude = metadata_dict[wsi]["longitude"]
        station_height = metadata_dict[wsi]["elevation"]
        # add these values to the data dictionary
        msg['_wsi_series'] = wsi_series
        msg['_wsi_issuer'] = wsi_issuer
        msg['_wsi_issue_number'] = wsi_issue_number
        msg['_wsi_local'] = wsi_local
        msg['_latitude'] = latitude
        msg['_longitude'] = longitude
        msg['_station_height'] = station_height
        conversion_success[tsi] = True
    except Exception:
        conversion_success[tsi] = False
        if wsi == "":
            LOGGER.warning(f"Missing WSI for station {tsi}")
        else:
            LOGGER.warning((f"Invalid WSI ({wsi}) found in station file,"
                            " unable to parse"))

    # TODO: update mappings based on number of precipitation observations and observed phenomena

    # for idx in range(num_sky):
    #     if 'vertical_visibility' in msg:    
    #         sky_cover_mappings = [
    #             {"eccodes_key": "#1#verticalVisibility", "value": "data:vertical_visibility"}
    #         ]
    #     else:
    #         sky_cover_mappings = [
    #             {"eccodes_key": f"#{idx+1}#cloudAmount", "value": f"data:cloud_amount_{idx+1}"},
    #             {"eccodes_key": f"#{idx+1}#heightOfBaseOfCloud", "value": f"data:cloud_height_{idx+1}"}
    #         ]
    #     print(sky_cover_mappings)
    #     # mapping.update(sky_cover_mappings[i] for i in range(len(sky_cover_mappings)))
    #     mapping.update(sky_cover_mappings[1])



    # for item in mapping['data']:
    #     print(item)

    # unexpanded_descriptors = [301150, 307080]
    # unexpanded_descriptors = [307011, 307012]
    unexpanded_descriptors = [307021]
    short_delayed_replications = []
    delayed_replications = []
    extended_delayed_replications = []
    table_version = 37

    try:
        # create new BUFR msg
        message = BUFRMessage(
            unexpanded_descriptors,
            short_delayed_replications,
            delayed_replications,
            extended_delayed_replications,
            table_version)
    except Exception as e:
        LOGGER.error(e)
        LOGGER.error("Error creating BUFRMessage")
        conversion_success[tsi] = False

    # parse
    if conversion_success[tsi]:
        # try:
        #     import pdb; pdb.set_trace()
        #     message.parse(msg, mapping)
        # except Exception as e:
        #     # import pdb; pdb.set_trace()
        #     LOGGER.error(e)
        #     LOGGER.error("Error parsing message")
        #     conversion_success[tsi] = False
        message.parse(msg, mapping)
    # Only convert to BUFR if there's no errors so far
    if conversion_success[tsi]:
        try:
            result["bufr4"] = message.as_bufr()  # encode to BUFR
            status = {"code": PASSED}
        except Exception as e:
            LOGGER.error("Error encoding BUFR, null returned")
            LOGGER.error(e)
            result["bufr4"] = None
            status = {
                "code": FAILED,
                "message": f"Error encoding, BUFR set to None:\n\t\tError: {e}\n\t\tMessage: {msg}"  # noqa
            }
            conversion_success[tsi] = False

        # now identifier based on WSI and observation date as identifier
        isodate = message.get_datetime().strftime('%Y%m%dT%H%M%S')
        rmk = f"WIGOS_{wsi}_{isodate}"

        # now additional metadata elements
        result["_meta"] = {
            "id": rmk,
            "geometry": {
                "type": "Point",
                "coordinates": [
                    message.get_element('#1#longitude'),
                    message.get_element('#1#latitude')
                ]
            },
            "properties": {
                "md5": message.md5(),
                "wigos_station_identifier": wsi,
                "datetime": message.get_datetime(),
                "originating_centre":
                message.get_element("bufrHeaderCentre"),
                "data_category": message.get_element("dataCategory")
            },
            "result": status
        }

    # now yield result back to caller
    yield result

    # Output conversion status to user
    if conversion_success[tsi]:
        LOGGER.info(f"Station {tsi} report converted")
    else:
        LOGGER.info(f"Station {tsi} report failed to convert")

    
with open("/home/alexander.thompson/metardecoder/station_list.csv") as fh:
    station_metadata = fh.read()

# result = transform(metar, station_metadata, 2023, 7)
# for item in result:
#     print(item)
test_dict, num_pcp, num_obv, num_sky = parse_metar(metar, 2023, 6)
for key in test_dict:
    print(key, ': ', test_dict[key])

# unexpanded_descriptors = [301150, 307021]
# short_delayed_replications = []
# delayed_replications = []
# extended_delayed_replications = []
# table_version = 37

# print("==ecCode Keys for descriptor 307021 - Metar representation==")
# message = BUFRMessage(
#             unexpanded_descriptors,
#             short_delayed_replications,
#             delayed_replications,
#             extended_delayed_replications,
#             table_version)

# unexpanded_descriptors = [307012]
# print("==ecCode Keys for descriptor 307012==")
# message = BUFRMessage(
#             unexpanded_descriptors,
#             short_delayed_replications,
#             delayed_replications,
#             extended_delayed_replications,
#             table_version)

# unexpanded_descriptors = [307013]
# print("==ecCode Keys for descriptor 307013==")
# message = BUFRMessage(
#             unexpanded_descriptors,
#             short_delayed_replications,
#             delayed_replications,
#             extended_delayed_replications,
#             table_version)