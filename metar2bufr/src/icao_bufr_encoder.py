import re

import metarDecoders as MD
import xmlUtilities as deu

from copy import deepcopy
from typing import Iterator
import csv
from io import StringIO
import logging
import json
import math
import os
from csv2bufr import BUFRMessage
import urllib.request as request


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

metar = "METAR KAFF 121755Z AUTO 21016G24KT 180V240 1SM R11/6000FT R12/P6000 R01L/0600VP6000FT -RA VA PO BKN015 OVC025TCU 06/04 A2990="
# metar = "METAR KABC 121755Z AUTO 21016G24KT 180V240 1000 2000 R11/P6000FT -RA BR BKN015 OVC025 06/04 A2990="
# metar = "SPECI DNPO 180700Z 00000KT 5000 BR BKN008 24/24 Q1015 BECMG 7000="
# metar = "METAR FNHU 171700Z AUTO 13004KT 9999 // NCD 20/03 Q1024="
# metar = "METAR SABE 012200Z NIL="

# metar = "SPECI DNPO 180700Z 21016G24MPS 3000 0500NW 1000E BR BKN008 24/24 Q1015 BECMG 7000="
# metar = "METAR K2C8 181955Z AUTO 13005KT 5SM HZ FEW038 SCT060 BKN120 21/16 A2992 RMK AO2="
# metar = "METAR K17J 250035Z AUTO 24003KT 10SM CLR 26/20 A3009 RMK AO2 T02580203="

# metar = "SAUS11 KAWN 182000 RRA\
# METAR K2C8 181955Z AUTO 13005KT 5SM HZ FEW038 SCT060 BKN120 21/16 A2992\
#       RMK AO2=\
# METAR K6L4 181955Z AUTO 21004KT 10SM SCT041 SCT049 SCT120 28/21 A3005\
#       RMK AO2=\
# METAR KANE 181946Z 21007KT 10SM SCT060 28/10 A2996=\
# METAR KATW 181945Z 28005KT 10SM BKN050 27/12 A2998=\
# METAR KBAK 181945Z 26004KT 10SM SCT026 27/22 A2994=\
# METAR KC62 181955Z AUTO 14004KT 10SM SCT050 BKN065 25/15 A3000 RMK\
#       AO2 T02540147=\
# METAR KCWA 181947Z 24007KT 10SM SCT049 24/12 A2998=\
# METAR KESN 181945Z 31004KT 6SM HZ CLR 31/19 A2995=\
# METAR KGYY 181945Z 06010KT 10SM CLR 24/16 A2999=\
# METAR KLBE 181945Z 21006KT 9SM FEW032 SCT055 25/18 A3002=\
# METAR KMMU 181945Z 14011G16KT 10SM SCT033 BKN043 BKN120 28/23 A2992=\
# METAR KSCH 181945Z 04005KT 7SM BKN010 BKN030 22/21 A2991=\
# METAR KUES 181945Z 32005KT 10SM SCT060 24/09 A3000=\
# METAR KVNW 181955Z AUTO 30003KT 10SM SCT055 SCT070 26/16 A2999 RMK\
#       AO2="




# metar = "SAAG SABM 012200\
# SPECI DNPO 180700Z 21016G24MPS 1SM BR BKN008\
#     24/24 Q1015 BECMG 7000="
# SPECI DNPO 180700Z 00000KT 5000N BR BKN008 24/24\
#         Q1015 BECMG 7000=\
# SPECI DNPO 180700Z\
#             00000KT 5000 BR BKN008 24/24 Q1015 BECMG 7000="
# METAR KAXO 012200Z  29023G35KT CAVOK 21/M01 Q0998=\
# METAR KLCH 012200Z  29018KT CAVOK 24/M09 Q1001=\
# METAR KMSY 012200Z  09006KT CAVOK 21/00 Q1003=\
# METAR KSHV 012200Z  25015KT 9999  SCT030  15/01 \
# Q0992=\
# METAR KLIX 012200Z\
# 25020KT 190V290 9999 SCT020 10/05 Q0984=\
# METAR KBED 012200Z  25026G36KT 9999  FEW020 \
# 13/M01 Q0989="


_keys = ['report_type',
         'tsi', 'icao_location_identifier', 'station_type',
         'year', 'month', 'day', 'hour', 'minute',
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

THISDIR = os.path.dirname(os.path.realpath(__file__))
MAPPINGS = f"{THISDIR}{os.sep}resources{os.sep}icao-metar-mappings.json"
ICAOSTATIONSURL = "https://www.aviationweather.gov/docs/metar/stations.txt"


# MAPPINGS = "/home/alexander.thompson/metar2bufr/src/metar-mappings2.json"

# Load template mappings file, this will be updated for each message.
with open(MAPPINGS) as fh:
    _mapping = json.load(fh)


def extract_metar(data: str) -> list:
    if not data.__contains__("="):
        LOGGER.error((
            "Delimiters (=) are not present in the string,"
            " thus unable to identify separate METAR reports."
            ))  # noqa
        raise ValueError
    
    start_position = data.find("METAR")
    if start_position == -1:
        start_position = data.find("SPECI")
        if start_position == -1:
            raise ValueError("Invalid METAR message. 'METAR' or 'SPECI' could not be found.")
        
    data = re.split('=', data[start_position:])

    for i in range(len(data)):
        data[i] = data[i]+"="

    # print(data[:len(data)-1])
    return data[:len(data)-1]


def parse_metar(message: str, year: int, month: int) -> dict:
    icaoID = re_ID.match(message).group('id')
    if deu.isUSIdentifier(icaoID):
        decoded = fmh(message)
    else:
        decoded = annex3(message)

    for key in decoded:
        print(key, ': ', decoded[key])

    output = deepcopy(metar_template)

    output['report_type'] = message[0:5]
    output['year'] = year
    output['month'] = month

    if 'ident' in decoded:
        icao = decoded['ident']['str']
        output['icao_location_identifier'] = icao

        #   find ICAO identifier in aviation list and pull out lat, long, and elevation
        response = request.urlopen(ICAOSTATIONSURL)
        html = response.read().decode('utf-8').split('\n')
        for line in html:
            if f' {icao} ' in line:
                print(line)
                # lat = re.search('\d{1,2} [0-9]{1,2}[N,S]', line).group()
                # long = re.search('\d{1,2} [0-9]{1,2}[N,S]  \d{1,3} \d{1,2}[E,W]\s{1,4}\d{1,4}', line).group()
                # info = re.search('\d{1,2} \d{1,2}[N,S] \d{1,3} \d{2}[E,W]\s{1,4}\d{1,4}').group()

                info = re.search('\d{1,2} [0-9]{1,2}[N,S]  \d{1,3} \d{1,2}[E,W]\s{1,4}\d{1,4}', line).group().split()
                print(info)
                lat = int(info[0]) + int(info[1][:-1])/60   # degrees
                long = int(info[2]) + int(info[3][:-1])/60  # degrees
                elevation = info[4]                         # meters
                output['_latitude'] = lat
                output['_longitude'] = long
                output['_station_height'] = elevation
                break
                # # print(lat, long, elevation)
                # try:
                #     tsi = str(re.search('[0-9]{5}', line).group())
                #     output['tsi'] = tsi
                #     output['block_no'] = tsi[0:2]
                #     output['station_no'] = tsi[2:5]
                # # print(f'Mapping {icao} to {tsi}')
                #     break
                # except Exception:
                #     tsi = None
                #     output['tsi'] = None
                #     output['block_no'] = None
                #     output['station_no'] = None
                #     break

    if 'itime' in decoded:
        output['day'] = decoded['itime']['tuple'].tm_mday
        output['hour'] = decoded['itime']['tuple'].tm_hour
        output['minute'] = decoded['itime']['tuple'].tm_min

    # metar station type is binary, either AUTOMATIC (0) or MANNED(1)
    if 'auto' in decoded:
        output['station_type'] = 0
    else:
        output['station_type'] = 1

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
            qualifier = decoded['rvr']['oper'][i]
            # encode rvr qualifier to bufr per table 008014, 0 - NORMAL, 1 - ABOVE THE UPPER LIMIT, 2 - BELOW THE LOWER LIMIT
            if qualifier == 'ABOVE':
                output[f'rvr_{i+1}_qualifier'] = 1
            elif qualifier == 'BELOW':
                output[f'rvr_{i+1}_qualifier'] = 2
            elif qualifier == None:
                output[f'rvr_{i+1}_qualifier'] = 0

            mean_vis = float(decoded['rvr']['mean'][i])
            # if distance is reported in meters, we can copy directly to bufr
            if decoded['rvr']['uom'][i] == 'm':
                output[f'rvr_{i+1}_mean'] = int(mean_vis)
            # if distance is reported in ft, have to convert to meters for bufr
            elif decoded['rvr']['uom'][i] == '[ft_i]':
                output[f'rvr_{i+1}_mean'] = math.floor(mean_vis*0.3048)

            tendency = decoded['rvr']['tend'][i]
            # encode rvr tendency to bufr per table 020018, 0 - INCREASING, 1 - DECREASING, 2 - NO DISTINCT CHANGE
            if tendency == 'UPWARD':
                output[f'rvr_{i+1}_tend'] = 0
            elif tendency == 'DOWNWARD':
                output[f'rvr_{i+1}_tend'] = 1
            elif tendency == 'MISSING_VALUE':
                output[f'rvr_{i+1}_tend'] = 2

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
            if cloud_amount == 'SKC' or cloud_amount == 'CLR':
                # table 020011 codes no cloud cover as 0. break out of the loops since this will be the only group with no other info
                output[f'cloud_amount_{i+1}'] = 0
                break
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
        if 'air' in decoded['temps']:
            # metar records temperatures in Celsius. Need to convert to Kelvin for bufr
            air_temp = float(decoded['temps']['air'])
            output['air_temp'] = air_temp + 273.15
        if 'dewpoint' in decoded['temps']:
            # metar records temperatures in Celsius. Need to convert to Kelvin for bufr
            dewpoint_temp = float(decoded['temps']['dewpoint'])
            output['dew_point_temp'] = dewpoint_temp + 273.15

    if 'altimeter' in decoded:
        altimeter = float(decoded['altimeter']['value'])
        alt_uom = decoded['altimeter']['uom']
        if alt_uom == 'hPa':
            output['altimeter'] = altimeter*100
        elif alt_uom == "[in_i'Hg]":
            # if metar records altimeter in inches of Mercury. need to convert to Pascals for bufr
            output['altimeter'] = round(altimeter*3386.39, 2)
        output['altimeter_uom'] = decoded['altimeter']['uom']

    return output, num_rvr, num_vrbrvr, num_pcp, num_obv, num_sky

def transform(data: str, year: int, month: int) -> Iterator[dict]:
    # ===================
    # First parse metadata file
    # ===================
    # if isinstance(metadata, str):
    #     fh = StringIO(metadata)
    #     reader = csv.reader(fh, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    #     col_names = next(reader)
    #     metadata_dict = {}
    #     tsi_mapping = {}
    #     for row in reader:
    #         if len(row) == 0:
    #             continue
    #         single_row = dict(zip(col_names, row))
    #         tsi = single_row['traditional_station_identifier']
    #         try:
    #             wsi = single_row['wigos_station_identifier']
    #             metadata_dict[wsi] = deepcopy(single_row)
    #             if tsi in tsi_mapping:
    #                 LOGGER.warning(("Duplicate entries found for station"
    #                                 f" {tsi} in station list file"))
    #             tsi_mapping[tsi] = wsi
    #         except Exception as e:
    #             LOGGER.error(e)

    #     fh.close()
    #     # metadata = metadata_dict[wsi]
    # else:
    #     LOGGER.error("Invalid metadata")
    #     raise ValueError

    try:
        messages = extract_metar(data)
        # print(messages)
    except Exception as e:
        LOGGER.error(e)
        return None

     # Count how many conversions were successful using a dictionary
    conversion_success = {}

    for metar in messages:
        # print(metar)
        result = dict()

        mapping = deepcopy(_mapping)
        # print(mapping)

        conversion_success = {}

        try:
            msg, num_rvr, num_vrbrvr, num_pcp, num_obv, num_sky = parse_metar(metar, year, month)
            icao = msg['icao_location_identifier']
            conversion_success[icao] = True

        except Exception as e:
            LOGGER.error(f"Error parsing METAR report: {data}. {str(e)}")

        # try:
        #     wsi = tsi_mapping[tsi]
        # except Exception:
        #     conversion_success[tsi] = False
        #     LOGGER.warning(f"Station {tsi} not found in station file")

        # parse WSI to get sections
        # try:
        #     wsi_series, wsi_issuer, wsi_issue_number, wsi_local = wsi.split("-")   # noqa
        #     # get other required metadata
        #     latitude = metadata_dict[wsi]["latitude"]
        #     longitude = metadata_dict[wsi]["longitude"]
        #     station_height = metadata_dict[wsi]["elevation"]
        #     # add these values to the data dictionary
        #     msg['_wsi_series'] = wsi_series
        #     msg['_wsi_issuer'] = wsi_issuer
        #     msg['_wsi_issue_number'] = wsi_issue_number
        #     msg['_wsi_local'] = wsi_local
        #     msg['_latitude'] = latitude
        #     msg['_longitude'] = longitude
        #     msg['_station_height'] = station_height
        #     conversion_success[tsi] = True
        # except Exception:
        #     conversion_success[tsi] = False
        #     if wsi == "":
        #         LOGGER.warning(f"Missing WSI for station {tsi}")
        #     else:
        #         LOGGER.warning((f"Invalid WSI ({wsi}) found in station file,"
        #                         " unable to parse"))

        # TODO: update mappings based on number of precipitation observations and observed phenomena

        for idx in range(num_rvr):
            rvr_mappings = [
                {"eccodes_key": f"#{idx+1}#runwayDesignator", "value": f"data:rvr_{idx+1}_designator"},
                {"eccodes_key": f"#{idx+1}#qualifierForRunwayVisualRange", "value": f"data:rvr_{idx+1}_qualifier"},
                {"eccodes_key": f"#{idx+1}#runwayVisualRangeRvr", "value": f"data:rvr_{idx+1}_mean"},
                {"eccodes_key": f"#{idx+1}#tendencyOfRunwayVisualRange", "value": f"data:rvr_{idx+1}_tend"}
            ]
            # print(rvr_mappings)
            # import pdb; pdb.set_trace()
            # for i in range(4):
            #     print(f"Updating mapping with {rvr_mappings[i]}")
            #     mapping.update(rvr_mappings[i])
            mapping.update(rvr_mappings[i] for i in range(4))
        # print("New Mapping:")
        # # for item in mapping['data']:
        # #     print(item)
        # print(mapping)

        # for item in mapping:
        #     print(item)
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
        delayed_replications = [max(1, num_rvr)]
        extended_delayed_replications = []
        table_version = 37

        try:
            # import pdb; pdb.set_trace()

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
            conversion_success[icao] = False

        # parse
        if conversion_success[icao]:
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
        if conversion_success[icao]:
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
                conversion_success[icao] = False

            # now identifier based on WSI and observation date as identifier
            isodate = message.get_datetime().strftime('%Y%m%dT%H%M%S')
            rmk = f"ICAO_{icao}_{isodate}"

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
        if conversion_success[icao]:
            LOGGER.info(f"Station {icao} report converted")
        else:
            LOGGER.info(f"Station {icao} report failed to convert")

    # calculate number of successful conversions
    conversion_count = sum(tsi for tsi in conversion_success.values())
    # print number of messages converted
    LOGGER.info((f"{conversion_count} / {len(messages)}"
            " reports converted successfully"))

    
# with open("/home/alexander.thompson/metar2bufr/src/resources/station_list.csv") as fh:
#     station_metadata = fh.read()

result = transform(metar, 2023, 7)

for item in result:
    print(item)
#     bufr4 = item['bufr4']

# f = open('bufrtest.bufr','wb')
# f.write(bufr4)
# f.close()
# test_dict, num_rvr, num_vrbrvr, num_pcp, num_obv, num_sky = parse_metar(metar, 2023, 6)
# for key in test_dict:
#     print(key, ': ', test_dict[key])


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

# messages = extract_metar(metar)
# for message in messages:
#     print(message)