#
# Name: metarDecoders.py
#
# Purpose: Annex 3: To decode, in its entirety, the METAR/SPECI traditional alphanumeric code
#          as described in the Meteorological Service for International Air Navigation,
#          Annex 3 to the Convention on International Civil Aviation.
#
#          FMH1: To decode, in its entirety, the METAR/SPECI traditional alphanumeric code as
#          described in the US Federal Meteorological Handbook No. 1 (FMH-1)
#
# Author: Mark Oberfield
# Organization: NOAA/NWS/OSTI/MDL/WIAB
# Contact Info: Mark.Oberfield@noaa.gov
#
import calendar
import logging
import re
import time

import tpg as tpg
import xmlConfig as des
import xmlUtilities as deu


class Annex3(tpg.Parser):
    r"""
    set lexer = ContextSensitiveLexer
    set lexer_dotall = True

    separator spaces:    '\s+' ;

    token type:  'METAR|SPECI' ;
    token ident: '[A-Z]{4}' ;
    token itime: '\d{6}Z' ;
    token auto:  'AUTO' ;
    token wind: '(VRB|(\d{3}|///))P?(\d{2,3}|//)(GP?\d{2,3})?(MPS|KT)' ;
    token wind_vrb: '\d{3}V\d{3}' ;
    token vsby1: '((?P<whole>\d{1,3}(?!/))?(?P<fraction>(M|\s+)?\d/\d{1,2})?|/{2,4})SM' ;
    token vsby2: '(?P<vsby>\d{4}|////)\s?(NDV)?' ;
    token minvsby: '\d{4}[NEWS]{0,2}'  ;
    token rvr: 'R(?P<rwy>[/\d]{2}[RCL]?)/(?P<oper>[MP])?(?P<mean>[/\d]{4}(FT)?)/?(?P<tend>[UDN]?)' ;
    token nsw: 'NSW' ;
    token pcp: '//|[+-]?((TS|SH)(GR|GS|RA|SN|UP){1,3}|FZ(DZ|RA|UP){1,2}|(DZ|RA|SN|SG|PL){1,3}|DS|SS|FC|UP)' ;
    token tpcp: '[+]?((TS|SH)(GR|GS|RA|SN){1,3}|FZ(DZ|RA){1,2}|(DZ|RA|SN|SG|PL){1,3}|DS|SS|FC)' ;
    token obv: '(BC|FZ|MI|PR)?FG|BR|(BL|DR)?(SA|DU)|(BL|DR)SN|HZ|FU|VA|SQ|PO|TS' ;
    token vcnty: 'VC(FG|PO|FC|DS|SS|TS|SH|VA|BL(SN|SA|DU))' ;
    token noclouds: 'NSC|NCD' ;
    token vvsby: 'VV(\d{3}|///)' ;
    token sky: '(FEW|SCT|BKN|OVC|///)(\d{3}|///)(CB|TCU|///)?' ;
    token temps: '(?P<air>(M|-)?\d{2}|MM|//)/(?P<dewpoint>(M|-)?\d{2}|MM|//)' ;
    token altimeter: '(Q|A)(\d{3,4}|////)' ;

    token rewx: 'RE(FZ|SH|TS)?(DZ|RASN|RA|(BL)?SN|SG|GR|GS|SS|DS|FC|VA|PL|UP|//)|RETS' ;
    token windshear: 'WS\s+(R(WY)?(?P<rwy>\d{2}[RLC]?)|ALL\s+RWYS?)' ;
    token seastate: 'W(?P<temp>(M|-)?\d\d|//)/(S|H)(?P<value>[/\d]{1,3})' ;
    token rwystate: 'R(\d{0,2}[LCR]?)/([\d/]{6}|SNOCLO|CLRD[/\d]{0,2})' ;
    token trendtype:'BECMG|TEMPO' ;
    token ftime: '(AT|FM)\d{4}' ;
    token ttime: 'TL\d{4}' ;
    token twind: '\d{3}P?\d{2,3}(GP?\d{2,3})?(MPS|KT)' ;

    START/e -> METAR/e $ e=self.finish() $ ;

    METAR -> Type Cor? Ident ITime (NIL|Report) ;
    Report -> Auto? Main Supplement? TrendFcst? ;
    Main -> Wind VrbDir? (CAVOK|((Vsby1|(Vsby2 MinVsby?)) Rvr{0,4} (Pcp|Obv|Vcnty){0,3} (NoClouds|VVsby|Sky{1,4}))) Temps Altimeter{1,2} ; # noqa: E501
    Supplement -> RecentPcp{0,3} WindShear? SeaState? RunwayState*;
    TrendFcst -> NOSIG|(TrendType (FTime|TTime){0,2} TWind? CAVOK? (Vsby1|Vsby2)? Nsw? (TPcp|Obv){0,3} (NoClouds|VVsby|Sky{0,4}))+ ;

    Type -> type/x $ self.obtype(x) $ ;
    Ident -> ident/x $ self.ident(x) $ ;
    ITime -> itime/x $ self.itime(x) $ ;

    NIL -> 'NIL' $ self.nil() $ ;

    Auto -> auto $ self.auto() $ ;
    Cor ->  'COR' $ self.correction() $ ;
    Wind -> wind/x $ self.wind(x) $ ;
    TWind -> twind/x $ self.wind(x) $ ;
    VrbDir -> wind_vrb/x $ self.wind(x) $ ;
    CAVOK -> 'CAVOK' $ self.cavok() $ ;

    Vsby1 -> vsby1/x $ self.vsby(x,'[mi_i]') $ ;
    Vsby2 -> vsby2/x $ self.vsby(x,'m') $ ;
    MinVsby -> minvsby/x $ self.vsby(x,'m') $ ;
    Rvr -> rvr/x $ self.rvr(x) $ ;
    Pcp -> pcp/x $ self.pcp(x) $ ;
    TPcp -> tpcp/x $ self.pcp(x) $ ;
    Nsw -> nsw/x $ self.pcp(x) $ ;
    Obv -> obv/x $ self.obv(x) $ ;
    Vcnty -> vcnty/x $ self.vcnty(x) $ ;
    NoClouds -> noclouds/x $ self.sky(x) $ ;
    VVsby -> vvsby/x $ self.sky(x) $ ;
    Sky -> sky/x $ self.sky(x) $ ;
    Temps -> temps/x $ self.temps(x) $ ;
    Altimeter -> altimeter/x $ self.altimeter(x) $ ;

    RecentPcp -> rewx/x $ self.rewx(x) $ ;

    WindShear -> windshear/x $ self.windshear(x) $ ;
    SeaState -> seastate/x $ self.seastate(x) $ ;
    RunwayState -> rwystate/x $ self.rwystate(x) $ ;
    NOSIG -> 'NOSIG' $ self.nosig() $ ;

    TrendType -> trendtype/x $ self.trendtype(x) $ ;
    FTime -> ftime/x $ self.timeBoundary(x) $ ;
    TTime -> ttime/x $ self.timeBoundary(x) $ ;
    """

    def __init__(self):

        self._tokenInEnglish = {'_tok_1': 'NIL', '_tok_2': 'COR', '_tok_3': 'CAVOK', '_tok_4': 'NOSIG',
                                'type': 'Keyword METAR or SPECI', 'ident': 'ICAO Identifier',
                                'itime': 'issuance time ddHHmmZ', 'auto': 'AUTO', 'wind': 'wind',
                                'wind_vrb': 'variable wind direction', 'vsby1': 'visibility in statute miles',
                                'vsby2': 'visibility in metres', 'minvsby': 'directional minimum visibility',
                                'rvr': 'runway visual range', 'pcp': 'precipitation',
                                'nsw': 'NSW', 'obv': 'obstruction to vision', 'vcnty': 'precipitation in the vicinity',
                                'noclouds': 'NCD, NSC', 'vvsby': 'vertical visibility', 'sky': 'cloud layer',
                                'temps': 'air and dew-point temperature', 'altimeter': 'altimeter',
                                'rewx': 'recent weather', 'windshear': 'windshear', 'seastate': 'state of the sea',
                                'rwystate': 'state of the runway', 'trendtype': 'trend qualifier',
                                'ftime': 'start of trend time period', 'ttime': 'end of trend time period',
                                'twind': 'wind (VRB not permitted)',
                                'tpcp': 'moderate to heavy precipitation'}

        self.header = re.compile(r'^(METAR|SPECI)(\s+COR)?\s+[A-Z]{4}.+?=', (re.MULTILINE | re.DOTALL))
        self.rmkKeyword = re.compile(r'[\s^]RMK[\s$]', re.MULTILINE)

        super(Annex3, self).__init__()
        self._Logger = logging.getLogger(__name__)

    def __call__(self, tac):

        self._metar = {'bbb': ' ',
                       'translationTime': time.strftime('%Y-%m-%dT%H:%M:%SZ')}
        try:
            result = self.header.search(tac)
            tac = result.group(0)[:-1]

        except AttributeError:
            self._metar['err_msg'] = 'Unable to find start and end positions of the METAR/SPECI.'
            return self._metar

        if self.__class__.__name__ == 'Annex3':
            #
            # Remove RMK token and everything beyond that. This decoder follows
            # Annex 3 specifications to the letter and ignores content beyond the
            # RMK keyword. Any unidentified content in the report renders it invalid.
            #
            rmkResult = self.rmkKeyword.search(tac)
            if rmkResult:
                tac = tac[:rmkResult.start()]

        try:
            self._expected = []
            return super(Annex3, self).__call__(tac)

        except tpg.SyntacticError:
            try:
                if 'altimeter' in self._metar:
                    self._expected.remove('altimeter')
            except ValueError:
                pass

            if len(self._expected):
                err_msg = 'Expecting %s ' % ' or '.join([self._tokenInEnglish.get(x, x)
                                                         for x in self._expected])
            else:
                err_msg = 'Unidentified group '

            tacLines = tac.split('\n')
            debugString = '\n%%s\n%%%dc\n%%s' % self.lexer.cur_token.end_column
            errorInTAC = debugString % ('\n'.join(tacLines[:self.lexer.cur_token.end_line]), '^',
                                        '\n'.join(tacLines[self.lexer.cur_token.end_line:]))
            self._Logger.info('%s\n%s' % (errorInTAC, err_msg))

            err_msg += 'at line %d column %d.' % (self.lexer.cur_token.end_line, self.lexer.cur_token.end_column)
            self._metar['err_msg'] = err_msg
            return self.finish()

        except Exception:
            self._Logger.exception(tac)
            return self.finish()

    def finish(self):
        #
        # If NIL, no QC checking is required
        if 'nil' in self._metar:
            self._metar
        #
        try:
            self._metar['trendFcsts'].append(self._trend)
            del self._trend
        except (AttributeError, KeyError):
            pass
        #
        # Set boundaries so multiple trend forecasts don't overlap in time
        try:
            for previous, trend in enumerate(self._metar['trendFcsts'][1:]):
                if 'til' not in self._metar['trendFcsts'][previous]['ttime']:
                    self._metar['trendFcsts'][previous]['ttime']['til'] = trend['ttime']['from']
        except KeyError:
            pass

        return self._metar

    def index(self):

        ti = self.lexer.cur_token
        return ('%d.%d' % (ti.line, ti.column - 1),
                '%d.%d' % (ti.end_line, ti.end_column - 1))

    def tokenOK(self, pos=0):
        'Checks whether token ends with a blank'
        try:
            return self.lexer.input[self.lexer.token().stop + pos].isspace()
        except IndexError:
            return True

    def eatCSL(self, name):
        'Overrides super definition'
        try:
            value = super(Annex3, self).eatCSL(name)
            self._expected = []
            return value

        except tpg.WrongToken:
            self._expected.append(name)
            raise

    def updateDictionary(self, key, value, root):

        try:
            d = root[key]
            d['index'].append(self.index())
            d['str'].append(value)

        except KeyError:
            root[key] = {'str': [value], 'index': [self.index()]}

    #######################################################################
    # Methods called by the parser
    def obtype(self, s):

        self._metar['type'] = {'str': s, 'index': self.index()}

    def ident(self, s):

        self._metar['ident'] = {'str': s, 'index': self.index()}

    def itime(self, s):

        d = self._metar['itime'] = {'str': s, 'index': self.index()}
        mday, hour, minute = int(s[:2]), int(s[2:4]), int(s[4:6])

        tms = list(time.gmtime())
        tms[2:6] = mday, hour, minute, 0
        deu.fix_date(tms)
        d['intTime'] = calendar.timegm(tuple(tms))
        d['tuple'] = time.gmtime(d['intTime'])
        d['value'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', d['tuple'])

    def auto(self):

        self._metar['auto'] = {'index': self.index()}

    def correction(self):

        self._metar['cor'] = {'index': self.index()}

    def nil(self):

        self._metar['nil'] = {'index': self.index()}

    def wind(self, s):
        #
        # Wind groups can appear later in the trend section of the report
        try:
            root = getattr(self, '_trend')
        except AttributeError:
            root = getattr(self, '_metar')
        #
        # Handle variable wind direction which always comes after the wind group
        try:
            d = root['wind']
            d['index'] = (d['index'][0], self.index()[1])
            d['str'] = "%s %s" % (d['str'], s)
            ccw, cw = s.split('V')
            d.update({'ccw': ccw, 'cw': cw})
            return

        except KeyError:
            if self.lexer.cur_token.name == 'wind_vrb':
                raise tpg.WrongToken
            pass

        d = root['wind'] = {'str': s, 'index': self.index()}
        dd = s[:3]

        if s[-3:] == 'MPS':
            uom = 'm/s'
            spd = s[3:-3]
        elif s[-2:] == 'KT':
            uom = '[kn_i]'
            spd = s[3:-2]

        try:
            ff, gg = spd.split('G')
            if ff[0] == 'P':
                d['ffplus'] = True
                ff = ff[1:]

            if gg[0] == 'P':
                d['ggplus'] = True
                gg = gg[1:]

            d.update({'dd': dd, 'ff': ff, 'gg': gg, 'uom': uom})

        except ValueError:
            if spd[0] == 'P':
                d['ffplus'] = True
                ff = spd[1:]
            else:
                ff = spd

            d.update({'dd': dd, 'ff': ff, 'uom': uom})

    def cavok(self):

        try:
            root = getattr(self, '_trend')
        except AttributeError:
            root = getattr(self, '_metar')

        root['cavok'] = {'index': self.index()}

    def vsby(self, s, uom):

        vis = 0.0
        oper = None
        v = self.lexer.tokens[self.lexer.cur_token.name][0].match(s)
        if self.lexer.cur_token.name == 'vsby1':
            try:
                vis += float(v.group('whole'))
            except TypeError:
                pass

            try:
                numerator, denominator = v.group('fraction').split('/', 1)
                if numerator[0] == 'M':
                    vis += float(numerator[1:]) / float(denominator)
                    oper = 'M'
                else:
                    vis += float(numerator) / float(denominator)

            except (AttributeError, ZeroDivisionError):
                pass

            value = '%.4f' % vis

        elif self.lexer.cur_token.name == 'vsby2':
            value = v.group('vsby')

        try:
            root = getattr(self, '_trend')
        except AttributeError:
            root = getattr(self, '_metar')

        if 'vsby' in root:
            root['vsby'].update({'min': s[0:4], 'bearing': deu.CardinalPtsToDegreesS.get(s[4:], '/')})
            root['vsby']['index'].append(self.index())
        else:
            root['vsby'] = {'str': s, 'index': [self.index()], 'value': value, 'uom': uom, 'oper': oper}

    def rvr(self, s):

        result = self.lexer.tokens[self.lexer.cur_token.name][0].match(s)
        uom = 'm'
        oper = {'P': 'ABOVE', 'M': 'BELOW'}.get(result.group('oper'), None)
        tend = {'D': 'DOWNWARD', 'N': 'NO_CHANGE', 'U': 'UPWARD'}.get(result.group('tend'), 'MISSING_VALUE')
        mean = result.group('mean')

        if mean[-2:] == 'FT':
            mean = mean[:-2]
            uom = '[ft_i]'

        try:
            d = self._metar['rvr']
            d['str'].append(s)
            d['index'].append(self.index())
            d['rwy'].append(result.group('rwy'))
            d['mean'].append(mean)
            d['oper'].append(oper)
            d['tend'].append(tend)
            d['uom'].append(uom)

        except KeyError:
            self._metar['rvr'] = {'str': [s], 'index': [self.index()], 'rwy': [result.group('rwy')],
                                  'oper': [oper], 'mean': [mean], 'tend': [tend], 'uom': [uom]}

    def obv(self, s):

        if s == '//' and not self.tokenOK():
            raise tpg.WrongToken

        try:
            root = getattr(self, '_trend')
        except AttributeError:
            root = getattr(self, '_metar')

        self.updateDictionary('obv', s, root)

    def pcp(self, s):

        if s == '//' and not self.tokenOK():
            raise tpg.WrongToken

        try:
            root = getattr(self, '_trend')
        except AttributeError:
            root = getattr(self, '_metar')

        self.updateDictionary('pcp', s, root)

    def vcnty(self, s):

        self.updateDictionary('vcnty', s, self._metar)

    def sky(self, s):

        try:
            root = getattr(self, '_trend')
        except AttributeError:
            root = getattr(self, '_metar')

        self.updateDictionary('sky', s, root)

    def temps(self, s):

        d = self._metar['temps'] = {'str': s, 'index': self.index(), 'uom': 'Cel'}

        rePattern = self.lexer.tokens[self.lexer.cur_token.name][0]
        result = rePattern.match(s)

        d.update(result.groupdict())
        try:
            d['air'] = str(int(result.group('air').replace('M', '-')))
        except ValueError:
            pass
        try:
            d['dewpoint'] = str(int(result.group('dewpoint').replace('M', '-')))
        except ValueError:
            pass

    def altimeter(self, s):

        if s[0] == 'Q':
            self._metar['altimeter'] = {'str': s, 'index': self.index(), 'uom': 'hPa', 'value': s[1:]}
        #
        # Add it only if QNH hasn't been found.
        elif 'altimeter' not in self._metar:
            try:
                value = '%.02f' % (int(s[1:]) * 0.01)
            except ValueError:
                value = '////'

            self._metar['altimeter'] = {'str': s, 'index': self.index(), 'uom': "[in_i'Hg]", 'value': value}

    def rewx(self, s):

        self.updateDictionary('rewx', s[2:], self._metar)

    def windshear(self, s):

        rePattern = self.lexer.tokens[self.lexer.cur_token.name][0]
        result = rePattern.match(s)
        self._metar['ws'] = {'str': s, 'index': self.index(), 'rwy': result.group('rwy')}

    def seastate(self, s):

        rePattern = self.lexer.tokens[self.lexer.cur_token.name][0]
        result = rePattern.match(s)

        stateType = {'S': 'seaState', 'H': 'significantWaveHeight'}.get(result.group(3))

        try:
            seatemp = str(int(result.group('temp').replace('M', '-')))
        except ValueError:
            seatemp = result.group('temp')

        self._metar['seastate'] = {'str': s, 'index': self.index(),
                                   'seaSurfaceTemperature': seatemp,
                                   stateType: result.group('value')}

    def rwystate(self, s):  # pragma: no cover

        rePattern = self.lexer.tokens[self.lexer.cur_token.name][0]
        result = rePattern.match(s)
        try:
            self._metar['rwystate'].append({'str': s, 'index': self.index(),
                                            'runway': result.group(1),
                                            'state': result.group(2)})
        except KeyError:
            self._metar['rwystate'] = [{'str': s, 'index': self.index(),
                                        'runway': result.group(1),
                                        'state': result.group(2)}]

    def nosig(self):

        self._metar['nosig'] = {'index': self.index()}

    def trendtype(self, s):

        try:
            self._metar.setdefault('trendFcsts', []).append(getattr(self, '_trend'))
            del self._trend
        except AttributeError:
            pass

        self._trend = {'type': s, 'index': self.index()}

    def timeBoundary(self, s):

        hour, minute = int(s[-4:-2]), int(s[-2:])
        tms = list(self._metar['itime']['tuple'])
        tms[3:6] = hour, minute, 0
        if hour == 24:
            tms[3] = 0
            tms[2] += 1

        deu.fix_date(tms)
        #
        # Cases when forecast crosses midnight UTC.
        if calendar.timegm(tms) < self._metar['itime']['intTime']:
            tms[2] += 1
            deu.fix_date(tms)

        try:
            self._trend['ttime'].update({s[:2]: time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                                              time.gmtime(calendar.timegm(tuple(tms))))})
        except KeyError:
            self._trend.update({'ttime': {s[:2]: time.strftime('%Y-%m-%dT%H:%M:%SZ',
                                                               time.gmtime(calendar.timegm(tuple(tms))))}})


class LocationParser(tpg.VerboseParser):
    #
    # LocationParser shall _always_ have VerboseParser as a super-class.
    #
    r"""
    set lexer = ContextSensitiveLexer
    set lexer_dotall = True
    separator spaces:    '\s+' ;

    token overhead:  'OHD' ;
    token allquads:  'ALQD?S' ;
    token compassPt: '\d{0,3}[NEWS]{1,2}' ;

    START -> Discrete|Span|Point ;

    Point -> (compassPt|overhead|allquads) ;
    Span -> Point('-'Point)+ ;
    Discrete ->  (Span|Point)('AND'(Span|Point))+ ;
    """
    re_compassPt = re.compile(r'(\d{0,3})([NEWS]{1,3})')
    CompassDegrees = {'N': (337.5, 022.5), 'NE': (022.5, 067.5), 'E': (067.5, 112.5), 'SE': (112.5, 157.5),
                      'S': (157.5, 202.5), 'SW': (202.5, 247.5), 'W': (247.5, 292.5), 'NW': (292.5, 337.5)}
    verbose = 0

    def __call__(self, string):
        #
        # Initialize
        self._spans = {}
        self._cnt = -1
        self._newDictionary = True
        self._overhead = False
        self._allquads = False
        try:
            super(LocationParser, self).__call__(string)
        except tpg.SyntacticError:
            pass
        #
        # Combine adjacent compass points
        k = list(self._spans.keys())
        k.sort(key=int)
        delete = []
        for f, s in zip(k, k[1:]):

            if f not in delete and self._spans[f]['cw'] == self._spans[s]['ccw']:
                if self._spans[f]['distance'] == self._spans[s]['distance']:
                    self._spans[f]['cw'] = self._spans[s]['cw']
                    self._spans[f]['s'] += '-%s' % self._spans[s]['s']
                    delete.append(s)
        #
        # Remove those that are combined
        for d in delete:
            del self._spans[d]
        #
        # Return list of dictionaries with one or more combined sector information
        k = list(self._spans.keys())
        k.sort(key=int)
        return [self._spans[i] for i in k]

    def eatCSL(self, name):
        """Overrides and enhance base class method"""
        value = super(LocationParser, self).eatCSL(name)
        #
        # If 'overhead' is found, set and return value
        if name == 'overhead':
            if self._overhead:
                return value

            self._overhead = True
            self._cnt += 1
            dKey = '%d' % self._cnt
            self._spans[dKey] = {'ccw': 0, 'cw': 0, 's': value, 'distance': None, 'uom': None}
            self._newDictionary = True

            return value
        #
        if name == 'allquads':
            if self._allquads:
                return value

            self._allquads = True
            self._cnt += 1
            dKey = '%d' % self._cnt
            self._spans[dKey] = {'ccw': 0, 'cw': 360, 's': value, 'distance': None, 'uom': None}
            return value
        #
        # Call token_info() regardless of verbose value.
        stackInfo = self.token_info(self.lexer.token(), "==", name)
        #
        # Determine the context
        frames = stackInfo.split('.')
        #
        # Pop off the first frame since its not useful here
        frames.pop(0)
        aztype = ''.join([f[0] for f in frames])

        if aztype not in ['DSP', 'DS', 'D']:
            return value

        if aztype == 'D':
            self._newDictionary = True
            return value

        if aztype == 'DS':
            dKey = '%d' % self._cnt
            if self._spans[dKey]['s'][-1] != '-' or self._spans[dKey]['s'] != 'OHD':
                self._spans[dKey]['s'] += value
            return value
        #
        # 'value' is a key as it contains the compass point
        #
        # Separate distance and compass direction
        result = self.re_compassPt.match(value)
        distance, key = result.groups()
        try:
            distance = int(result.group(1))
        except ValueError:
            distance = 0
        #
        dKey = '%d' % self._cnt
        if self._newDictionary:

            self._newDictionary = False
            self._cnt += 1
            dKey = '%d' % self._cnt
            self._spans[dKey] = {'ccw': 0, 'cw': 0, 'distance': [], 's': '', 'uom': '[mi_i]'}

        d = self._spans[dKey]
        if distance != 0:
            d['distance'].append(distance)

        try:
            d['cw'] = self.CompassDegrees[key][1]
        except KeyError:
            d['cw'] = self.CompassDegrees[key[0]][1]

        d['s'] = '%s%s' % (d['s'], key)
        if d['ccw'] == 0:
            try:
                d['ccw'] = self.CompassDegrees[key][0]
            except KeyError:
                d['ccw'] = self.CompassDegrees[key[0]][0]

        return value


class FMH1(Annex3):
    r"""
    set lexer = ContextSensitiveLexer
    set lexer_dotall = True

    separator spaces:    '\s+' ;

    token type:  'METAR|SPECI' ;
    token ident: '[A-Z][A-Z0-9]{3}' ;
    token itime: '\d{6}Z' ;
    token auto:  'AUTO' ;
    token wind: '(VRB|(\d{3}|///))P?(\d{2,3}|//)(GP?\d{2,3})?KT' ;
    token wind_vrb: '\d{3}V\d{3}' ;
    token vsby1: '(?P<whole>\d{1,3}(?!/))?(?P<fraction>(M|\s+)?\d/\d{1,2})?SM' ;
    token vsby2: '(?P<vsby>\d{4}|////)\s?(NDV)?' ;
    token rvr: 'R(?P<rwy>[/\d]{2}[RCL]?)/(?P<oper>[MP])?(?P<mean>[/\d]{4}(FT)?)/?(?P<tend>[UDN]?)' ;
    token vrbrvr: 'R(?P<rwy>\d{2}[RCL]?)/(?P<lo>M?\d{4})V(?P<hi>P?\d{4})FT' ;
    token pcp: '//|[+-]?((TS|SH)(GR|GS|PL|RA|SN|UP){1,3}|FZ(DZ|RA|UP){1,2}|(DZ|RA|SN|SG|PL){1,3}|DS|SS|FC|UP)' ;
    token obv: '(BC|FZ|MI|PR)?FG|BR|(BL|DR)?(SA|DU)|(BL|DR)SN|HZ|FU|VA|SQ|PO|TS' ;
    token vcnty: 'VC(FG|PO|FC|DS|SS|TS|SH|VA|BL(SN|SA|DU))' ;
    token noclouds: 'SKC|CLR' ;
    token vvsby: 'VV(\d{3}|///)' ;
    token sky: '(FEW|SCT|BKN|OVC|///)(\d{3}|///)(CB|TCU|///)?' ;
    token temps: '(?P<air>(M|-)?\d{2}|MM|//)/(?P<dewpoint>(M|-)?\d{2}|MM|//)?' ;
    token altimeter: 'A(\d{4}|////)' ;

    token ostype: 'AO(1|2)A?' ;
    token pkwnd: 'PK\s+WND\s+(\d{5,6}/\d{2,4})' ;
    token wshft: 'WSHFT\s+\d{2,4}(\s+FROPA)?' ;
    token sfcvis1: 'SFC\s+VIS\s+(?P<whole>\d{1,2}(?!/))?(?P<fraction>(M|\s+)?\d/\d{1,2})?' ;
    token twrvis1: 'TWR\s+VIS\s+(?P<whole>\d{1,2}(?!/))?(?P<fraction>(M|\s+)?\d/\d{1,2})?' ;
    token vvis1: '(VSBY|VIS)\s+(?P<vintlo>\d{1,2}(?!/))?(?P<vfraclo>\s*M?\d/\d{1,2})?V(?P<vinthi>\d{1,2}(?!/))?(?P<vfrachi>\s*\d/\d{1,2})?' ;
    token sctrvis1: 'VIS\s+[NEWS]{1,2}\s+(?P<whole>\d{1,2}(?!/))?(?P<fraction>(M|\s+)?\d/\d{1,2})?' ;
    token vis2loc1: 'VIS\s+(?P<whole>\d{1,2}(?!/))?(?P<fraction>(M|\s+)?\d/\d{1,2})?\s+(?P<loc>([RWY\s]+\d{1,2}[RCL]?([-/RWY\s]+\d{1,2}[RCL]?)?|\S+))' ;
    token ltg: '((OCNL|FRQ|CONS)\s+)?LTG(CG|IC|CC|CA){0,4}(OHD|VC|DSNT|ALQD?S|\d{0,2}[NEWS]{1,3}((?=[-\s])|$)|AND|[-\s])+' ;
    token tstmvmt: '(CBMAM|CB|TS)(OHD|VC|DSNT|ALQD?S|\d{0,2}[NEWS]{1,3}(?=[-\s])|AND|[-\s])*(?P<mov>MOV(D|G)?\s+([NEWS]{1,3}|OHD))?' ;
    token pcpnhist: '((SH|FZ)?(TS|DZ|RA|SN|SG|IC|PE|GR|GS|UP|PL)((B|E)\d{2,4})+)+' ;
    token hail: 'GR(\s+(LESS|GREATER)\s+THAN)?\s+(?P<whole>\d{1,2}(?!/))?(?P<fraction>(\s+)?\d/\d{1,2})?' ;
    token vcig: 'CIG\s+(\d{3})V(\d{3})' ;
    token obsc: '(FG|FU|DU|VA|HZ)\s+(FEW|SCT|BKN|OVC|///)\d{3}' ;
    token vsky: '(FEW|SCT|BKN|OVC)(\d{3})?\s+V\s+(SCT|BKN|OVC)' ;
    token cig2loc: 'CIG\s+\d{3}\s+(?P<loc>([RWY\s]+\d{1,2}[RCL]?([-/RWY\s]+\d{1,2}[RCL]?)?|\S+))' ;
    token pchgr: 'PRES(R|F)R' ;
    token mslp: 'SLP\d{3}' ;
    token nospeci: 'NOSPECI' ;
    token aurbo: 'AURBO' ;
    token contrails: 'CONTRAILS' ;
    token snoincr: 'SNINCR\s+\d/[\d/]{1,3}' ;
    token other: '(FIRST|LAST)' ;
    token pcpn1h: 'P(\d{3,4}|/{3,4})' ;
    token pcpn6h: '6(\d{4}|////)' ;
    token pcpn24h: '7(\d{4}|////)' ;
    token iceacc: 'I[1,3,6](\d{3}|///)' ;
    token snodpth: '4/(\d{3}|///)' ;
    token lwe: '933(\d{3}|///)' ;
    token sunshine: '98(\d{3}|///)' ;
    token skychar: '8/[/\d]{3}' ;
    token tempdec: 'T[01]\d{3}[01/][/\d]{3}' ;
    token xmt6h: '[12](\d{4}|////)' ;
    token xtrmet: '4[\d/]{8}' ;
    token ptndcy3h: '5(\d{4}|////)' ;
    token ssindc: '(RVR|PWI|P|FZRA|TS|SLP)NO|(VISNO|CHINO)(\s+([RWY]{1,3}\s*\d\d[LCR]?|[NEWS]{1,2}))?' ;
    token maintenance: '\$' ;
    token any: '\S+' ;

    START/e -> METAR/e $ e=self.finish() $ ;

    METAR -> Type Ident ITime Report ;
    Report -> (Auto|Cor)? Main Remarks? ;
    Main -> Wind? VrbDir? (Vsby1|Vsby2)? (VrbRvr|Rvr){0,4} (Pcp|Obv|Vcnty){0,3} (NoClouds|VVsby|Sky{1,6})? Temps? Altimeter? ;
    Remarks -> 'RMK' (Ostype|TempDec|Slp|Pcpn1h|Ptndcy3h|Ssindc|Maintenance|XmT6h|PcpnHist|PkWnd|Ltg|Pcpn6h|XtrmeT|VCig|Pchgr|VVis1|Wshft|Pcpn24h|Cig2Loc|Iceacc|VSky|SfcVis1|TwrVis1|Tstmvmt|Vis2Loc1|Other|Snodpth|Obsc|Nospeci|SctrVis1|Snoincr|Contrails|Lwe|Hail|SkyChar|Aurbo|Sunshine|any)* ;  # noqa: E501

    Type -> type/x $ self.obtype(x) $ ;
    Ident -> ident/x $ self.ident(x) $ ;
    ITime -> itime/x $ self.itime(x) $ ;

    Auto -> auto $ self.auto() $ ;
    Cor ->  'COR' $ self.correction() $ ;
    Wind -> wind/x $ self.wind(x) $ ;
    VrbDir -> wind_vrb/x $ self.wind(x) $ ;

    Vsby1 -> vsby1/x $ self.vsby(x,'[mi_i]') $ ;
    Vsby2 -> vsby2/x $ self.vsby(x,'m') $ ;
    Rvr -> rvr/x $ self.rvr(x) $ ;
    VrbRvr -> vrbrvr/x $ self.vrbrvr(x) $ ;
    Pcp -> pcp/x $ self.pcp(x) $ ;
    Obv -> obv/x $ self.obv(x) $ ;
    Vcnty -> vcnty/x $ self.vcnty(x) $ ;
    NoClouds -> noclouds/x $ self.sky(x) $ ;
    VVsby -> vvsby/x $ self.sky(x) $ ;
    Sky -> sky/x $ self.sky(x) $ ;
    Temps -> temps/x $ self.temps(x) $ ;
    Altimeter -> altimeter/x $ self.altimeter(x) $ ;

    Ostype -> ostype/x $ self.ostype(x) $ ;
    PkWnd -> pkwnd/x $ self.pkwnd(x) $ ;
    Wshft -> wshft/x $ self.wshft(x) $ ;
    SfcVis1 -> sfcvis1/x $ self.sfcvsby(x,'[mi_i]') $ ;
    TwrVis1 -> twrvis1/x $ self.twrvsby(x,'[mi_i]') $ ;
    VVis1 -> vvis1/x $ self.vvis(x,'[mi_i]') $ ;
    SctrVis1 -> sctrvis1/x $ self.sctrvis(x,'[mi_i]') $ ;
    Vis2Loc1 -> vis2loc1/x $ self.vis2loc(x,'[mi_i]') $ ;

    SkyChar -> skychar/x $ self.skychar(x) $ ;
    Ltg -> ltg/x $ self.ltg(x) $ ;
    PcpnHist -> pcpnhist/x $ self.pcpnhist(x) $ ;
    Tstmvmt -> tstmvmt/x $ self.tstmvmt(x) $ ;
    Hail -> hail/x $ self.hail(x) $ ;
    VCig -> vcig/x $ self.vcig(x) $ ;
    Obsc -> obsc/x $ self.obsc(x) $ ;
    VSky -> vsky/x $ self.vsky(x) $ ;
    Cig2Loc -> cig2loc/x $ self.cig2loc(x) $ ;
    Pchgr -> pchgr/x $ self.pressureChgRapidly(x) $ ;
    Slp -> mslp/x $ self.mslp(x) $ ;
    Nospeci -> nospeci/x $ self.nospeci(x) $ ;
    Aurbo -> aurbo/x $ self.aurbo(x) $;
    Contrails -> contrails/x $ self.contrails(x) $;
    Snoincr -> snoincr/x $ self.snoincr(x) $ ;
    Other -> other/x $ self.other(x) $ ;
    Pcpn1h -> pcpn1h/x $ self.pcpn1h(x) $ ;
    Pcpn6h -> pcpn6h/x $ self.pcpn6h(x) $ ;
    Pcpn24h -> pcpn24h/x $ self.pcpn24h(x) $ ;
    Iceacc -> iceacc/x $ self.iceacc(x) $ ;
    Snodpth -> snodpth/x $ self.snodpth(x) $ ;
    Lwe -> lwe/x $ self.lwe(x) $ ;
    Sunshine -> sunshine/x $ self.sunshine(x) $ ;
    TempDec -> tempdec/x $ self.tempdec(x) $ ;
    XmT6h -> xmt6h/x $ self.xmt6h(x) $ ;
    XtrmeT -> xtrmet/x $ self.xtrmet(x) $ ;
    Ptndcy3h -> ptndcy3h/x $ self.prestendency(x) $ ;
    Ssindc -> ssindc/x $ self.ssindc(x) $ ;
    Maintenance -> maintenance/x $ self.maintenance(x) $ ;
    """

    def __init__(self):

        super(FMH1, self).__init__()

        self._tokenInEnglish = {'_tok_1': 'RMK', 'type': 'Keyword METAR or SPECI', 'ident': 'ICAO Identifier',
                                '_tok_2': 'COR', 'itime': 'issuance time ddHHmmZ', 'auto': 'AUTO', 'wind': 'wind',
                                'wind_vrb': 'variable wind direction', 'altimeter': 'altimeter',
                                'vsby1': 'prevailing visibility in statute miles', 'vsby2': 'visibility in metres',
                                'rvr': 'runway visual range', 'drytstm': 'thunderstorm', 'pcp': 'precipitation',
                                'obv': 'obstruction to vision', 'vcnty': 'precipitation in the vicinity',
                                'noclouds': 'CLR, SKC', 'vvsby': 'vertical visibility', 'sky': 'cloud layer',
                                'temps': 'air and dew-point temperature'}

        self._CompassDegrees = {'N': (337.5, 022.5), 'NE': (022.5, 067.5), 'E': (067.5, 112.5), 'SE': (112.5, 157.5),
                                'S': (157.5, 202.5), 'SW': (202.5, 247.5), 'W': (247.5, 292.5), 'NW': (292.5, 337.5)}
        #
        # For FMH-1 thunderstorm and lightning location and bearing information
        self._locationParser = LocationParser()
        self._re_VC = re.compile(r'VC\s*(ALQD?S|[NEWS]{1,3}|AND|-|VC|\s)*')
        self._re_DSNT = re.compile(r'DSNT\s*(ALQD?S|[NEWS]{1,3}|AND|-|DSNT|\s)*')
        self._re_sectr = re.compile(r'(\d{0,4})([NEWS]{1,3})')
        self._re_rwy = re.compile(r'[RWY]{1,3}\s*(\d\d[LCR]?)')

        self._vsbyFactor = 100. / float(des.Max_PercentageOfPrevailing)

        self._Logger = logging.getLogger(__name__)
        self.header = re.compile(r'^(METAR|SPECI)(\s+COR)?\s+[A-Z][A-Z0-9]{3}.+?=', (re.MULTILINE | re.DOTALL))

    def __call__(self, tac):

        self._expected = []
        return super(FMH1, self).__call__(tac)

    def temps(self, s):
        try:
            super(FMH1, self).temps(s)
        except AttributeError:
            pass

    def vrbrvr(self, s):

        result = self.lexer.tokens[self.lexer.cur_token.name][0].match(s)

        oper = None
        uom = 'm'
        if s[-2:] == 'FT':
            uom = '[ft_i]'
        lo = result.group('lo')
        hi = result.group('hi')
        if 'M' in lo:
            oper = 'M'
            lo = lo.replace('M', '')
        elif 'P' in hi:
            oper = 'P'
            hi = hi.replace('P', '')

        try:
            d = self._metar['vrbrvr']
            d['str'].append(s)
            d['index'].append(self.index())
            d['rwy'].append(result.group('rwy'))
            d['lo'].append(lo)
            d['hi'].append(hi)
            d['oper'].append(oper)
            d['uom'].append(uom)
        except KeyError:
            self._metar['vrbrvr'] = {'str': [s], 'index': [self.index()], 'rwy': [result.group('rwy')],
                                     'oper': [oper], 'lo': [lo], 'hi': [hi], 'uom': [uom]}

    def ostype(self, s):

        self._metar['ostype'] = {'str': s, 'index': self.index()}

    def pkwnd(self, s):

        d = self._metar['pkwnd'] = {'str': s, 'index': self.index()}
        result = self.lexer.tokens[self.lexer.cur_token.name][0].match(s)
        wind, hhmm = result.group(1).split('/')

        d['dd'] = wind[:3]
        d['ff'] = wind[3:]
        try:
            d['uom'] = self._metar['wind']['uom']
        except KeyError:
            d['uom'] = '[kn_i]'

        tms = list(self._metar['itime']['tuple'])
        if len(hhmm) == 2:
            tms[4] = int(hhmm)
            d['itime'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', tuple(tms))

        elif len(hhmm) == 4:
            tms[3:5] = int(hhmm[:2]), int(hhmm[2:])
            deu.fix_date(tms)
            if calendar.timegm(tms) > self._metar['itime']['intTime']:
                tms[2] -= 1
                deu.fix_date(tms)

            d['itime'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(calendar.timegm(tuple(tms))))

    def wshft(self, s):

        tokens = s.split()
        d = self._metar['wshft'] = {'str': s, 'fropa': len(tokens) == 3, 'index': self.index()}

        hhmm = tokens[1]
        tms = list(self._metar['itime']['tuple'])
        if len(hhmm) == 2:
            tms[4] = int(hhmm)
            d['itime'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', tuple(tms))

        elif len(hhmm) == 4:
            tms[3:5] = int(hhmm[:2]), int(hhmm[2:])
            deu.fix_date(tms)
            if calendar.timegm(tms) > self._metar['itime']['intTime']:
                tms[2] -= 1
                deu.fix_date(tms)

            d['itime'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(calendar.timegm(tuple(tms))))

    def sfcvsby(self, s, uom):

        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        vis = 0.0
        try:
            vis += float(v.group('whole'))
        except TypeError:
            pass

        try:
            numerator, denominator = v.group('fraction').split('/', 1)
            if numerator[0] == 'M':
                vis += float(numerator[1:]) / float(denominator)
                oper = 'M'
            else:
                vis += float(numerator) / float(denominator)

        except (AttributeError, ZeroDivisionError):
            pass

        vis = '%.2f' % vis
        #
        # What is in the prevailing group is tower visibility
        try:
            self._metar['twrvsby'] = self._metar['vsby'].copy()
        except KeyError:
            pass

        self._metar['vsby'] = {'str': s,
                               'index': [self.index()],
                               'value': vis,
                               'uom': uom}
        try:
            self._metar['vsby']['oper'] = oper
        except NameError:
            pass

    def twrvsby(self, s, uom):

        d = self._metar['twrvsby'] = {'str': s, 'index': self.index()}
        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        vis = 0.0
        try:
            vis += float(v.group('whole'))
        except TypeError:
            pass

        try:
            numerator, denominator = v.group('fraction').split('/', 1)
            if numerator[0] == 'M':
                vis += float(numerator[1:]) / float(denominator)
                d['oper'] = 'M'
            else:
                vis += float(numerator) / float(denominator)

        except (AttributeError, ZeroDivisionError):
            pass

        d.update({'value': '%.2f' % vis, 'uom': uom})

    def vvis(self, s, uom):

        d = self._metar['vvis'] = {'str': s, 'index': self.index(), 'uom': uom}
        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        vis = 0.0
        try:
            vis += float(v.group('vintlo'))
        except (AttributeError, TypeError):
            pass

        try:
            numerator, denominator = v.group('vfraclo').split('/', 1)
            if numerator[0] == 'M':
                vis += float(numerator[1:]) / float(denominator)
                d['oper'] = 'M'

            else:
                vis += float(numerator) / float(denominator)

        except (AttributeError, ZeroDivisionError):
            pass

        d['lo'] = vis

        vis = 0.0
        try:
            vis += float(v.group('vinthi'))
        except (AttributeError, TypeError):
            pass

        try:
            numerator, denominator = v.group('vfrachi').split('/', 1)
            vis += float(numerator) / float(denominator)

        except (AttributeError, ZeroDivisionError):
            pass

        d['hi'] = vis
        #
        # If the observer decides to put the higher visibility first, then switch
        if d['hi'] < d['lo']:
            d['hi'], d['lo'] = d['lo'], d['hi']

        d['hi'] = '%.4f' % d['hi']
        d['lo'] = '%.4f' % d['lo']

    def skychar(self, s):

        self._metar['skychar'] = {'str': s, 'index': self.index()}

    def sctrvis(self, s, uom):

        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        vis = 0.0
        oper = None
        try:
            vis += float(v.group('whole'))
        except TypeError:
            pass

        try:
            numerator, denominator = v.group('fraction').split('/', 1)
            if numerator[0] == 'M':
                vis = float(numerator[1:]) / float(denominator)
                oper = 'M'
            else:
                vis += float(numerator) / float(denominator)

        except (AttributeError, ZeroDivisionError):
            pass

        vis = '%.4f' % vis

        compassPt = s.split()[1]
        #
        # Sector visibility can be handled under the 'iwxxm' namespace if Annex III criteria are met.
        pvis = deu.checkVisibility(float(self._metar['vsby']['value']), self._metar['vsby']['uom'])
        svis = deu.checkVisibility(float(vis), uom)

        if svis < pvis and (svis < des.Max_SectorVisibility_1 or (pvis > (self._vsbyFactor * svis)
                                                                  and svis < des.Max_SectorVisibility_2)):
            #
            # Construct Annex III compliant sector visibility string and invoke the vsby() method
            self.vsby('%04d%s' % (svis, compassPt), 'm')
        #
        # Otherwise, sector visibility has a key of its own. FHM-1 reports sector visibility under
        # different critera
        #
        else:
            self._metar['sectorvis'] = {'str': s, 'index': self.index(), 'value': vis, 'oper': oper,
                                        'direction': deu.CardinalPtsToDegreesS.get(compassPt, '360'),
                                        'uom': uom}

    def vis2loc(self, s, uom):

        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        vis = 0.0
        oper = None
        try:
            vis += float(v.group('whole'))
        except (AttributeError, TypeError):
            pass

        try:
            numerator, denominator = v.group('fraction').split('/', 1)
            if numerator[0] == 'M':
                vis += float(numerator[1:]) / float(denominator)
                oper = 'M'
            else:
                vis += float(numerator) / float(denominator)

        except (AttributeError, ZeroDivisionError):
            pass

        vis = str(deu.checkVisibility(vis, uom))
        uom = 'm'

        location = v.group('loc')
        try:
            d = self._metar['secondLocation']
            d['str'] = '%s %s' % (d['str'], s)
            d['index'].append(self.index())
            try:
                d[location].update({'vsby': vis, 'vuom': uom, 'oper': oper})
            except KeyError:
                d[location] = {'vsby': vis, 'vuom': uom, 'oper': oper}

        except KeyError:
            self._metar['secondLocation'] = {location: {'vsby': vis, 'vuom': uom, 'oper': oper},
                                             'index': [self.index()], 'str': s}

    def ltg(self, s):

        if 'lightning' in self._metar:

            self._metar['lightning']['str'] = '%s %s' % (self._metar['lightning']['str'], s)
            self._metar['lightning']['index'].append(self.index())

        else:
            self._metar['lightning'] = {'str': s, 'index': [self.index()], 'locations': {}}

        lxr = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        bpos = s.find('LTG') + 3
        epos = lxr.end(3)
        ss = s.replace('LTG', '   ')
        frequency = lxr.group(2)
        if frequency is not None:
            ss = ss.replace(frequency, ' ' * len(frequency))
        #
        # Sorted lightning characteristics, if any
        sortedTypes = ''
        if epos > 0:

            ltgtypes = ss[bpos:epos]
            sortedTypes = [ltgtypes[n:n + 2] for n in range(0, len(ltgtypes), 2)]
            sortedTypes.sort()
            ss = ss.replace(ltgtypes, ' ' * len(ltgtypes))
        #
        stypes = ''.join(sortedTypes)
        key = '%s_%s' % (frequency, stypes)
        #
        # Location/Distance are present
        locationString = ss[epos + 1:].strip()
        locations = self.processLocationString(locationString)
        for qualifier, sectors in locations.items():
            for sector in sectors:
                del sector['distance']
                del sector['uom']
        #
        self._metar['lightning']['locations'].setdefault(key, []).append(locations)

    def pcpnhist(self, s):

        try:
            d = self._metar['pcpnhist']
            d['str'] = '%s%s' % (d['str'], s)
            d['index'] = (d['index'][0], self.index()[1])

        except KeyError:
            self._metar['pcpnhist'] = {'str': s, 'index': self.index()}

    def tstmvmt(self, s):

        lxr = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        #
        # First, process movement of the thunderstorm
        if lxr.group('mov') not in [None, '']:
            try:
                movement = self._locationParser(lxr.group('mov').split()[1])[0]
                #
                # Remove cruft
                del movement['distance']
                del movement['uom']
            except IndexError:
                movement = None
        else:
            movement = None
        #
        # Process sector in which thunderstorms are found
        bpos, epos = lxr.end(1), lxr.start(3)
        if epos > bpos:
            results = self.processLocationString(s[bpos:epos])
        else:
            results = self.processLocationString(s[bpos:])
        #
        # If horribly garbled sector string is provided that parser can't make sense of . . .
        if results == {} and movement is None:
            raise tpg.WrongToken
        #
        # If multiple thunderstorms are reported
        if 'tstmvmt' in self._metar:

            self._metar['tstmvmt']['str'] = '%s %s' % (self._metar['tstmvmt']['str'], s)
            try:
                self._metar['tstmvmt']['index'].append(self.index())
            except AttributeError:
                t = self._metar['tstmvmt']['index']
                self._metar['tstmvmt']['index'] = [t, self.index()]
        else:
            self._metar['tstmvmt'] = {'str': s, 'index': self.index(), 'locations': {}}
        #
        # Some post-processing of the dictionaries returned
        for qualifier, sectors in results.items():
            for sector in sectors:
                lRange = sector['distance']
                if type(lRange) == list:
                    if len(lRange) == 0:
                        del sector['distance']
                        del sector['uom']
                    elif len(lRange) == 1:
                        lRange.append(lRange[0])
                    else:
                        while len(lRange) > 2:
                            lRange.pop(1)

        self._metar['tstmvmt']['locations'].setdefault(lxr.group(1), []).append((results, movement))

    def processLocationString(self, locationString):
        #
        locations = {}
        #
        # Parse out language "in the vicinity" (VC); shouldn't be mixed up with "distant" (DSNT)
        vcLocation = self._re_VC.search(locationString)
        if vcLocation:
            bpos, epos = vcLocation.span()
            vcString = locationString[bpos:epos]
            locationString = locationString.replace(vcString, '')
            locations['VC'] = self._locationParser(vcString.replace('VC', ''))

        dsntLocation = self._re_DSNT.search(locationString)
        if dsntLocation:
            bpos, epos = dsntLocation.span()
            dsntString = locationString[bpos:epos]
            locationString = locationString.replace(dsntString, '')
            locations['DSNT'] = self._locationParser(dsntString.replace('DSNT', ''))
        #
        # locationString now has what is left over....
        if locationString.strip():
            locations['ATSTN'] = self._locationParser(locationString)

        return locations

    def hail(self, s):

        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        siz = 0.0
        try:
            siz += float(v.group('whole'))
        except (AttributeError, TypeError):
            pass

        try:
            num, den = v.group('fraction').split('/', 1)
            siz += float(num) / float(den)

        except (AttributeError, ValueError, ZeroDivisionError):
            pass

        self._metar['hail'] = d = {'str': s, 'value': '%.2f' % siz, 'index': self.index(), 'uom': '[in_i]'}

        if 'LESS' in s:
            d.update({'oper': 'BELOW'})
        elif 'GREATER' in s:
            d.update({'oper': 'ABOVE'})

    def vcig(self, s):

        d = self._metar['vcig'] = {'str': s, 'index': self.index(), 'uom': '[ft_i]'}
        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        d['lo'] = str(int(v.group(1)))
        d['hi'] = str(int(v.group(2)))

    def obsc(self, s):

        pcp, sky = s.split()
        try:
            d = self._metar['obsc']
            d['str'].append(s)
            d['index'].append(self.index())
            d['pcp'].append(pcp)
            d['sky'].append(sky)

        except KeyError:
            self._metar['obsc'] = {'str': [s], 'index': [self.index()], 'pcp': [pcp], 'sky': [sky]}

    def vsky(self, s):

        v = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)
        d = self._metar['vsky'] = {'str': s, 'index': self.index(), 'uom': '[ft_i]',
                                   'cvr1': v.group(1), 'cvr2': v.group(3)}
        try:
            d['hgt'] = str(int(v.group(2)))

        except (TypeError, ValueError):
            #
            # Height not given, so find the first cloud layer in main body that matches cloud amount
            d['hgt'] = ''
            for amt in [d['cvr1'], d['cvr2']]:
                for layer in self._metar['sky']['str']:
                    if layer.startswith(amt):
                        try:
                            d['hgt'] = str(int(layer[-3:]))
                            break

                        except ValueError:
                            pass

                if len(d['hgt']) > 0:
                    break
            else:
                del self._metar['vsky']

    def cig2loc(self, s):

        c = self.lexer.tokens[self.lexer.cur_token.name][0].search(s)

        location = c.group('loc')
        value = str(int(s.split()[1]) * 100)
        try:
            d = self._metar['secondLocation']
            d['str'] = '%s %s' % (d['str'], s)
            d['index'].append(self.index())
            try:
                d[location].update({'ceilhgt': value, 'cuom': '[ft_i]'})
            except KeyError:
                d[location] = {'ceilhgt': value, 'cuom': '[ft_i]'}

        except KeyError:
            self._metar['secondLocation'] = {location: {'ceilhgt': value, 'cuom': '[ft_i]'}, 'index': [self.index()],
                                             'str': s}

    def pressureChgRapidly(self, s):

        self._metar['pchgr'] = {'str': s, 'index': self.index(),
                                'value': {'R': 'RISING', 'F': 'FALLING'}.get(s[-2])}

    def mslp(self, s):

        p = float(s[3:]) / 10.0

        if p >= 60.0:
            p += 900.0
        else:
            p += 1000.0
        #
        # If record high MSLP is mistaken for low pressure, it usually occurs
        # with extreme cold events. US record SLP: 1078.6 hPa
        try:
            if 960.0 <= p < 980.0 and (float(self._metar['temps']['air']) < -1.0 and
                                       int(self._metar['wind']['ff']) < 20):
                p += 100.0
            #
            # like-wise extreme low pressure can be mistaken for high pressure. US record SLP 924 hPa
            elif 1060.0 > p > 1020.0 and int(self._metar['wind']['ff']) > 20:
                p -= 100.0

        except KeyError:
            pass

        p = round(p, 1)
        self._metar['mslp'] = {'str': s, 'index': self.index(), 'uom': 'hPa', 'value': str(p)}

    def nospeci(self, s):

        self._metar['nospeci'] = {'str': s, 'index': self.index()}

    def aurbo(self, s):

        self._metar['aurbo'] = {'str': s, 'index': self.index()}

    def contrails(self, s):

        self._metar['contrails'] = {'str': s, 'index': self.index()}

    def snoincr(self, s):

        d = self._metar['snoincr'] = {'str': s, 'index': self.index(), 'period': '1', 'uom': '[in_i]'}
        d['value'], d['depth'] = s.split()[1].split('/', 1)

    def other(self, s):

        self._metar['event'] = {'str': s, 'index': self.index()}

    def pcpn1h(self, s):

        try:
            self._metar['pcpn1h'] = {'str': s, 'index': self.index(), 'uom': '[in_i]',
                                     'value': '%.2f' % (float(s[1:]) * 0.01), 'period': '1'}
            if s[1:] == '0000':
                self._metar['pcpn1h']['value'] = '0.01'
                self._metar['pcpn1h']['oper'] = 'M'

        except ValueError:
            self._metar['pcpn1h'] = {'str': s, 'index': self.index(), 'uom': 'N/A',
                                     'value': 'unknown', 'period': '1'}

    def pcpn6h(self, s):

        try:
            self._metar['pcpnamt'] = {'str': s, 'index': self.index(), 'uom': '[in_i]',
                                      'value': '%.2f' % (float(s[1:]) * 0.01)}
            if s[1:] == '0000':
                self._metar['pcpnamt']['value'] = '0.01'
                self._metar['pcpnamt']['oper'] = 'M'

        except ValueError:
            self._metar['pcpnamt'] = {'str': s, 'index': self.index(), 'uom': 'N/A',
                                      'value': 'unknown', 'period': '6'}

        hm = self._metar['itime']['str'][2:5]
        if hm in ['024', '025', '084', '085', '144', '145', '204', '205']:
            self._metar['pcpnamt']['period'] = '3'
        elif hm in ['054', '055', '114', '115', '174', '175', '234', '235']:
            self._metar['pcpnamt']['period'] = '6'
        else:
            if self._metar['itime']['tuple'].tm_hour in [3, 9, 15, 21]:
                self._metar['pcpnamt']['period'] = '3'
            else:
                self._metar['pcpnamt']['period'] = '6'

    def pcpn24h(self, s):

        try:
            self._metar['pcpn24h'] = {'str': s, 'index': self.index(), 'uom': '[in_i]',
                                      'value': '%.2f' % (float(s[1:]) * 0.01),
                                      'period': '24'}
            if s[1:] == '0000':
                self._metar['pcpn24h']['value'] = '0.01'
                self._metar['pcpn24h']['oper'] = 'M'

        except ValueError:
            self._metar['pcpn24h'] = {'str': s, 'index': self.index(), 'uom': 'N/A',
                                      'value': 'unknown', 'period': '24'}

    def iceacc(self, s):

        try:
            d = self._metar['iceacc%c' % s[1]] = {'str': s, 'index': self.index(), 'uom': '[in_i]',
                                                  'value': '%.2f' % (float(s[2:]) * 0.01),
                                                  'period': s[1]}
            if s[-3:] == '000':
                d['value'] = '0.01'
                d['oper'] = 'M'

        except ValueError:
            self._metar['iceacc%c' % s[1]] = {'str': s, 'index': self.index(), 'value': 'unknown', 'period': s[1]}

    def snodpth(self, s):

        self._metar['snodpth'] = {'str': s, 'index': self.index(), 'uom': '[in_i]', 'value': s[2:]}

    def lwe(self, s):

        try:
            self._metar['lwe'] = {'str': s, 'index': self.index(), 'uom': '[in_i]', 'period': '24',
                                  'value': '%.1f' % (float(s[3:]) * 0.1)}
        except ValueError:
            self._metar['lwe'] = {'str': s, 'index': self.index(), 'uom': '[in_i]', 'period': '24',
                                  'value': 'unknown'}

    def sunshine(self, s):

        self._metar['ssmins'] = {'str': s, 'index': self.index(),
                                 'value': s[2:]}

    def tempdec(self, s):

        d = self._metar['tempdec'] = {'str': s, 'index': self.index()}
        tt = round(float(s[2:5]) * 0.1, 1)
        if s[1] == '1':
            tt = -tt

        try:
            td = round(float(s[6:9]) * 0.1, 1)
            if s[5] == '1':
                td = -td

        except ValueError:
            td = '//'

        d.update({'air': str(tt), 'dewpoint': str(td)})
        try:
            self._metar['temps']['air'] = str(tt)
            self._metar['temps']['dewpoint'] = str(td)

        except KeyError:
            self._metar['temps'] = d

    def xmt6h(self, s):

        if not self.tokenOK():
            raise tpg.WrongToken

        if s[0] == '1':
            extrema = 'max'
        else:
            extrema = 'min'

        factor = 1.0
        if s[1] == '1':
            factor = -1.0

        if 'maxmin6h' not in self._metar:
            d = self._metar['maxmin6h'] = {'str': s, 'index': [self.index()], 'period': '6'}
        else:
            d = self._metar['maxmin6h']
            d['str'] = '%s %s' % (d['str'], s)
            d['index'].append(self.index())

        try:
            d[extrema] = '%.1f' % (0.1 * float(s[2:]) * factor)
        except ValueError:
            d[extrema] = s[2:]

    def xtrmet(self, s):

        maxfactor = 1.0
        if s[1] == '1':
            maxfactor = -1.0
        minfactor = 1.0
        if s[5] == '1':
            minfactor = -1.0

        d = self._metar['maxmin24h'] = {'str': s, 'index': self.index(), 'period': '24'}
        try:
            d['max'] = '%.1f' % (0.1 * float(s[2:5]) * maxfactor)
        except ValueError:
            d['max'] = s[2:]

        try:
            d['min'] = '%.1f' % (0.1 * float(s[6:]) * minfactor)
        except ValueError:
            d['min'] = s[6:]

    def prestendency(self, s):

        try:
            self._metar['ptndcy'] = {'str': s, 'index': self.index(),
                                     'character': s[1],
                                     'pchg': '%.1f' % (int(s[2:]) * 0.1)}
        except ValueError:
            self._metar['ptndcy'] = {'str': s, 'index': self.index()}

    def ssindc(self, s):

        try:
            d = self._metar['ssistatus']
            d['str'] = '%s %s' % (d['str'], s)
            d['index'].append(self.index())

        except KeyError:
            d = self._metar['ssistatus'] = {'str': s, 'index': [self.index()], 'sensors': {}}
        #
        # Identify failed sensor and possibly location
        location = 'none'
        tokens = s.replace('\n', ' ').split(' ')
        sensor = tokens.pop(0)

        if len(tokens) > 0:

            location = ' '.join(tokens)
            result = self._re_rwy.match(s)
            if result is not None:
                location = 'R%s' % result.group(1)

        d['sensors'].setdefault(location, []).append(sensor)

    def maintenance(self, s):

        self._metar['maintenance'] = {'index': self.index()}

    def finish(self):

        self.unparsed()
        return Annex3.finish(self)

    def unparsed(self):

        self.unparsedText = [list(x) for x in self.lexer.input.split('\n')]
        self.unparsedText.insert(0, [])
        #
        # Remove all tokens from input string that were successfully parsed.
        for key in self._metar:
            try:
                if type(self._metar[key]['index']) == tuple:
                    self.whiteOut(self._metar[key]['index'])
                elif type(self._metar[key]['index']) == list:
                    for index in self._metar[key]['index']:
                        self.whiteOut(index)
            except (KeyError, TypeError):
                pass
        #
        # Before the RMK token, if there is one, should be considered an error
        # After the RMK token, it is considered text added by the observer
        #
        remainder = ''.join([''.join(x) for x in self.unparsedText])
        rmk_pos = remainder.find('RMK')

        text = remainder[:rmk_pos].strip()
        if len(text):
            self._metar['unparsed'] = {'str': text}

        if rmk_pos != -1:
            text = remainder[rmk_pos + 3:].strip()
            if len(text):
                self._metar['additive'] = {'str': ' '.join(text.split())}

    def whiteOut(self, index):
        #
        # Starting, ending line and character positions
        try:
            slpos, scpos = [int(x) for x in index[0].split('.')]
            elpos, ecpos = [int(x) for x in index[1].split('.')]
        except AttributeError:
            slpos, scpos = [int(x) for x in index[0][0].split('.')]
            elpos, ecpos = [int(x) for x in index[-1][1].split('.')]

        if slpos == elpos:
            self.unparsedText[slpos][scpos:ecpos] = ' ' * (ecpos - scpos)
        else:
            self.unparsedText[slpos][scpos:] = ' ' * len(self.unparsedText[slpos][scpos:])
            self.unparsedText[elpos][:ecpos + 1] = ' ' * (ecpos + 1)
