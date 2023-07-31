import re

import metar2bufr.src.metarDecoders as MD
import metar2bufr.src.xmlUtilities as deu

fmh = MD.FMH1()
annex3 = MD.Annex3()

alist = ["METAR SPTN 102000Z 23013KT 9999 SCT050 SCT120 27/17 Q1013 RMK PP000=",
         "METAR KOGS 221610Z AUTO VRB03G11KT 10SM FEW049 26/14 A3017 RMK AO2=",
         "METAR KOWX 221615Z AUTO 08010KT 10SM BKN033 23/11 A3006 RMK AO1=",
         "METAR KRPJ 221615Z AUTO 08007KT 10SM CLR 29/11 A3005 RMK AO2 T0290E0110 TSNO=",
         "METAR KRZT 221615Z AUTO 08007KT 10SM SCT023 OVC038 20/13 A3003 RMK AO2 PWINO="]

re_ID = re.compile(r'(METAR|SPECI)\s+(COR\s+)?(?P<id>\w{4})')

while True:
    
    try:
        met_report = alist.pop()
    except IndexError:
        break

    icaoID = re_ID.match(met_report).group('id')
    if deu.isUSIdentifier(icaoID):
        adictionary = fmh(met_report)
    else:
        adictionary = annex3(met_report)

    
