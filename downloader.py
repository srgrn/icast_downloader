""" a simple script to get the packet publishing free book of the day into your account """
import argparse
import json
import logging
import os
import sys

import requests
from lxml import html
import yaml
import getpass

CONFIG = None
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'}
BASE_URL = 'https://books.icast.co.il/'
LOGIN_URL = BASE_URL + 'UserPages/LoginPage.aspx?direct=1'


def setup(args):
    log_level = 'WARNING'
    if args.debug:
        # import pdb
        log_level = 'DEBUG'
    log_format = '%(asctime)-15s - %(levelname)s - %(message)s'
    logging.basicConfig(format=log_format, level=log_level)
    logging.debug('Setup logging configuration')
    config = {}
    if args.config:
        logging.debug('loading config file')
        try:
            with open(args.config) as configfile:
                config = json.load(configfile)
        except IOError:
            logging.critical("Failed to load the file")
            sys.exit(1)
        except ValueError:
            logging.critical("Failed to read the config file probably not proper json")
            sys.exit(1)
        except Exception as e:
            raise e
        return config
    else:
        logging.debug('no config file specified')
    for key in os.environ:
        if "CONFIG_" in key:
            config[key.replace('CONFIG_').lower()] = os.environ.get(key)
    return config


def set_arg_in_config(args, name):
    if hasattr(args, name) and getattr(args, name) is not None:
        CONFIG[name] = getattr(args, name)


def get_login_session():
    data = {'ctl00$ScriptManager': 'ctl00$MainHolder$pnlLogin|ctl00$MainHolder$LoginBox$LoginButton',
            '__EVENTTARGET': 'ctl00$MainHolder$LoginBox$LoginButton',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '/wEPDwULLTE1NDI1NzQyMDAPFgIeC1JlZmVycmVyVVJMBRpodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsLxYCZg9kFgICAw9kFgICAw9kFgYCAQ9kFgwCAQ8WAh4HVmlzaWJsZWgWBAIDDw8WAh4HVG9vbFRpcAVw15TXnten15XXnSDXnNeU16rXoteT15vXnyDXkdee16bXkSDXlNeX16nXkdeV158sINeR16jXm9eZ16nXldeqINep16LXqdeZ16DXlSDXkdeQ16rXqCDXldek16jXmNeZ150g15DXmdep15nXmdedLmRkAgUPDxYCHwIFdteo16nXmdee16og15TXodek16jXmdedINep157Xoteg15nXmdeg15nXnSDXkNeV16rXoNeVINee157XqteZ16DXmdedINei15wg15TXnteT16Mg16nXoNeX15bXldeoINeQ15zXmdeU150g15HXlNee16nXmi5kZAICDw8WAh4LTmF2aWdhdGVVcmwFGmh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwvZGQCAw8PFgIfAwUkaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16jXmdedZGQCBA8WAh4LXyFJdGVtQ291bnQCDxYeAgEPZBYCZg8VBF9odHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov157Xkdem16It15nXldedLdeU157Xqdek15fXlC3XnNeo15XXm9ep15nXnS3XkdeQ16rXqDTXnteR16bXoiDXmdeV150g15TXntep16TXl9eUINec16jXldeb16nXmdedINeR15DXqteoQGh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/Xodek16jXmdedLdeX15PXqdeZ150V16HXpNeo15nXnSDXl9eT16nXmdedZAICD2QWAmYPFQQ+aHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eh16TXqNeV16og157Xp9eV16gT16HXpNeo15XXqiDXnten15XXqERodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov16HXpNeo15XXqi3Xnteq15XXqNeS157XqhnXodek16jXldeqINee16rXldeo15LXnteqZAIDD2QWAmYPFQRCaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9ee16rXly3Xldee16HXqteV16jXmdefF9ee16rXlyDXldee16HXqteV16jXmdefM2h0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/XoteZ15XXnwjXoteZ15XXn2QCBA9kFgJmDxUEOmh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/XoteZ15PXny3Xl9eT16kP16LXmdeT158g15fXk9epQmh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/Xodek16jXldeqLden15zXkNeh15nXqhfXodek16jXldeqINen15zXkNeh15nXqmQCBQ9kFgJmDxUENWh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/XlNeV157XldeoCteU15XXnteV16g4aHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eo15HXmS3Xnteb16gN16jXkdeZINee15vXqGQCBg9kFgJmDxUEQmh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/XnteT17TXkS3Xldek16DXmNeW15nXlBfXnteT17TXkSDXldek16DXmNeW15nXlEdodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov16HXpNeo15nXnS3XoteTLdep16LXqteZ15nXnRzXodek16jXmdedINei15Mg16nXoteq15nXmdedZAIHD2QWAmYPFQQ6aHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eS15nXnNeQ15ktMC0tNA7XkteZ15zXkNeZIDAtNDpodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov15LXmdec15DXmS01LS03DteS15nXnNeQ15kgNS03ZAIID2QWAmYPFQQ7aHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eS15nXnNeQ15ktOC0tMTAP15LXmdec15DXmSA4LTEwPGh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/XkteZ15zXkNeZLTExLS0xMxDXkteZ15zXkNeZIDExLTEzZAIJD2QWAmYPFQRDaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eS15nXnNeQ15ktMTMt15XXntei15zXlBjXkteZ15zXkNeZIDEzINeV157Xotec15RZaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9ee15XXntec16bXmS3Xntep16jXky3XlNeX15nXoNeV15otLdeZ15zXk9eZ150v157Xldee15zXpteZINee16nXqNeTINeU15fXmdeg15XXmiAtINeZ15zXk9eZ151kAgoPZBYCZg8VBGZodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov157Xldee15zXpteZLdee16nXqNeTLdeU15fXmdeg15XXmi0t15fXmNeZ15HXlC3Xldeq15nXm9eV1588157Xldee15zXpteZINee16nXqNeTINeU15fXmdeg15XXmiAtINeX15jXmdeR15Qg15XXqteZ15vXldefTWh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi/Xl9eV15HXlC3XnNeR15LXqNeV16ot15HXodek16jXldeqIteX15XXkdeUINec15HXkteo15XXqiDXkdeh16TXqNeV16pkAgsPZBYCZg8VBEBodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov15TXntec16bXqi3XlNem15XXldeqFdeU157XnNem16og15TXpteV15XXqkRodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov16HXldek16jXmdedLdee16HXpNeo15nXnRnXodeV16TXqNeZ150g157Xodek16jXmdedZAIMD2QWAmYPFQREaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eW15nXm9eo15XXny3Xotem157XkNeV16om15nXldedINeU15bXmdeb16jXldefINeV15TXotem157XkNeV16ovaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL3Nob2ER16HXpNeo15kg16nXldeQ15RkAg0PZBYCZg8VBDpodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov16TXqNehLdeh16TXmdeoLdek16jXoSDXodek15nXqCAtINeW15XXm9eZ150g15XXnteV16LXnteT15nXnVhodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov15TXkNeo15vXmdeV158t16HXpNeo15XXqi3XoteR16jXmdeqLdeR16fXldecL9eU15DXqNeb15nXldefIC0g16HXpNeo15XXqiDXoteR16jXmdeqINeR16fXldecZAIOD2QWAmYPFQRVaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eU16fXnNeY15XXqi3Xodek16jXmdeZ16ot15TXoteZ15XXldeo15nXnSrXlNen15zXmNeV16og16HXpNeo15nXmdeqINeU16LXmdeV15XXqNeZ151OaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9eU15DXldeg15nXkdeo16HXmdeY15Qg15TXpNeq15XXl9eUI9eU15DXldeg15nXkdeo16HXmdeY15Qg15TXpNeq15XXl9eUZAIPD2QWAmYPFQQzaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xp9eY15LXldeo15nXldeqL9ep15nXqNeUCNep15nXqNeUMmh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16fXmNeS15XXqNeZ15XXqi95YWhhZHV0CteZ15TXk9eV16pkAgUPDxYEHwMFJGh0dHA6Ly93d3cuaWNhc3QuY28uaWwvaG9tZXBhZ2UuYXNweB8CBbcB15TXm9eg16HXlSDXnNei15XXnNedINeU16TXldeT16fXkNeh15jXmdedLiDXkNec16TXmSDXqteV15vXoNeZ15XXqiDXqNeT15nXlSwg16nXmdeT15XXqNeZ150g16LXptee15DXmdeZ150sINep15nXoteV16jXmdedINeQ16fXk9ee15nXmdedINeV16rXldeb158g16fXldec15kg15zXlNeQ15bXoNeUINeR15fXmdeg150uZGQCBw8PFgIfAwU7aHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC9Vc2VyUGFnZXMvTG9naW5QYWdlLmFzcHg/ZGlyZWN0PTFkZAIDD2QWAmYPZBYIZg9kFgYCAQ9kFgYCAQ8WAh4EVGV4dAXtAzxhIGhyZWY9Imh0dHA6Ly9ib29rcy5pY2FzdC5jby5pbC8lRDclQTclRDclOTglRDclOTIlRDclOTUlRDclQTglRDclOTklRDclOTUlRDclQUEvJUQ3JUE4JUQ3JTkxJUQ3JTk5LSVENyU5RSVENyU5QiVENyVBOCI+16jXkdeZINee15vXqDwvYT48YSBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov16HXpNeo15XXqiDXnten15XXqCI+16HXpNeo15XXqiDXnten15XXqDwvYT48YSBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9en15jXkteV16jXmdeV16ov16HXldek16jXmdedLdee16HXpNeo15nXnSAJICI+16HXldek16jXmdedINee16HXpNeo15nXnTwvYT48YSBocmVmPSJodHRwOi8vYm9va3MuaWNhc3QuY28uaWwvJUQ3JUE3JUQ3JTk4JUQ3JTkyJUQ3JTk1JUQ3JUE4JUQ3JTk5JUQ3JTk1JUQ3JUFBLyVENyVBMSVENyVBNCVENyVBOCVENyU5OS0lRDclOUUlRDclQUElRDclOTciPteh16TXqNeZINee16rXlzwvYT5kAgUPZBYCZg8PFgIeBlVzZXJJRGZkFgRmD2QWBmYPDxYCHghJbWFnZVVybAVHaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC9hZG1pbi9VcGxvYWRzL0Jhbm5lcnMvc3Vic2NyaXB0aW9uX2Jhbm5lci5wbmdkZAIBDw8WAh8CBU3Xnten16nXmdeR15nXnSDXnNeh16TXqNeZ150g157Xlden15zXmNeZ150g16nXnCDXkNeZ15nXp9eh15gg15HXkNeg15PXqNeV15nXk2QWAmYPDxYCHwcFRmh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwvYWRtaW4vVXBsb2Fkcy9CYW5uZXJzL2dvb2dsZV9wbGF5X2Jhbm5lci5wbmdkZAICD2QWAmYPDxYCHwcFQmh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwvYWRtaW4vVXBsb2Fkcy9CYW5uZXJzL2FwcFN0b3JlQmFubmVyLnBuZ2RkAgIPFgIfAWhkAgcPZBYCAgIPZBYCAgEPFgIfBQVJPHAgY2xhc3M9IiBwYjE1Ij7Xodek16jXmdedINee15XXp9ec15jXmdedIC0g15DXmdeq15og15HXm9ecINee16fXldedPC9wPmQCAw8PFgIeCHRvb2x0aXBzBRIkKGZ1bmN0aW9uICgpIHt9KTtkFgJmD2QWAmYPZBYIAgEPD2QWAh4FY2xhc3MFFWJ0bl9zaWRlIG1sX2JhY2sgZmxyIGQCAw8PZBYCHwkFFWJ0bl9zaWRlIGZsbCBzZWxlY3RlZGQCBQ8WAh4Fc3R5bGUFDGRpc3BsYXk6bm9uZRYCZg8WAh8FBcUYPHVsIGNsYXNzPSJtZW51Ij48bGk+PGEgaWQ9ImJvb2tidXkwIiBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9eh16TXqC8yMS3XnteX16nXkdeV16ot16LXnC3XlNee15DXlC3XlC0yMSIgdGl0bGU9IjIxINee15fXqdeR15XXqiDXotecINeU157XkNeUINeULTIxIj48c3BhbiBjbGFzcz0icGljIj48aW1nIHNyYz0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC9ib29rc3BpYy85ZTcwYThjMS1kYjVkLTRmM2UtYTBlZS01OGVjMzM0MjM4OWEuanBnIiBhbHQ9IjIxINee15fXqdeR15XXqiDXotecINeU157XkNeUINeULTIxIiBzdHlsZT0id2lkdGg6ODBweCIvPjwvc3Bhbj48ZGl2IGNsYXNzPSJpYmxvY2siPjxzcGFuIGNsYXNzPSJpYmxvY2sgYmx1ZSBNZW9kZWRQYXNodXRfT0UtUmVndWxhciBmb250MzIiPjE8L3NwYW4+PGJyIC8+PHN0cm9uZz4yMSDXnteX16nXkdeV16og16LXnCDXlNee15AuLi48L3N0cm9uZz48YnIgLz7XmdeV15HXnCDXoNeXINeU16jXqNeZPC9kaXY+PC9hPjwvbGk+PGxpPjxhIGlkPSJib29rYnV5MSIgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16gv15vXnC3XnteULdep16fXqNeULdep150t15HXkNee16oiICB0aXRsZT0i15vXnCDXnteUINep16fXqNeUINep150g15HXkNee16oiPjxzcGFuIGNsYXNzPSJudW0gZmxyIj4yPC9zcGFuPjxkaXYgY2xhc3M9ImlibG9jayBmbHIgdzE0MCI+PHN0cm9uZz7Xm9ecINee15Qg16nXp9eo15Qg16nXnSDXkdeQ157Xqjwvc3Ryb25nPjxici8+15HXqNeZ158g15LXqNeZ16DXldeV15M8L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2J1eTIiIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoL9en15nXpteV16gt16rXldec15PXldeqLdeU15DXoNeV16nXldeqIiAgdGl0bGU9Iten15nXpteV16gg16rXldec15PXldeqINeU15DXoNeV16nXldeqIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+Mzwvc3Bhbj48ZGl2IGNsYXNzPSJpYmxvY2sgZmxyIHcxNDAiPjxzdHJvbmc+16fXmdem15XXqCDXqteV15zXk9eV16og15TXkNeg15XXqdeV16o8L3N0cm9uZz48YnIvPteZ15XXkdecINeg15cg15TXqNeo15k8L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2J1eTMiIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoL9ec15nXnNeT15nXnS3XmNeV15EiICB0aXRsZT0i15zXmdec15PXmdedINeY15XXkSI+PHNwYW4gY2xhc3M9Im51bSBmbHIiPjQ8L3NwYW4+PGRpdiBjbGFzcz0iaWJsb2NrIGZsciB3MTQwIj48c3Ryb25nPtec15nXnNeT15nXnSDXmNeV15E8L3N0cm9uZz48YnIvPteZ16TXoteqINeV15nXoNep15jXmdeZ158g15bXlNeoLCDXmdeo15XXnyDXp9eV15zXmNeV1588L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2J1eTQiIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoL9eg16TXqS3XlNeV157XmdeUIiAgdGl0bGU9Iteg16TXqSDXlNeV157XmdeUIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+NTwvc3Bhbj48ZGl2IGNsYXNzPSJpYmxvY2sgZmxyIHcxNDAiPjxzdHJvbmc+16DXpNepINeU15XXnteZ15Q8L3N0cm9uZz48YnIvPteo150g15DXldeo1588L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2J1eTUiIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoLzI0Ldep16LXldeqLdeR15fXmdeZLdeQ15nXqdeUIiAgdGl0bGU9IjI0INep16LXldeqINeR15fXmdeZ15Qg16nXnCDXkNeZ16nXlCI+PHNwYW4gY2xhc3M9Im51bSBmbHIiPjY8L3NwYW4+PGRpdiBjbGFzcz0iaWJsb2NrIGZsciB3MTQwIj48c3Ryb25nPjI0INep16LXldeqINeR15fXmdeZ15Qg16nXnCDXkNeZ16nXlDwvc3Ryb25nPjxici8+16nXmNek158g16bXldeV15nXkjwvZGl2PjxiciBjbGFzcz0iY2xlYXIiIC8+PC9hPjwvbGk+PGxpPjxhIGlkPSJib29rYnV5NiIgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16gv15LXmdeZ158t15DXmdeZ16giICB0aXRsZT0i15LXmdeZ158g15DXmdeZ16giPjxzcGFuIGNsYXNzPSJudW0gZmxyIj43PC9zcGFuPjxkaXYgY2xhc3M9ImlibG9jayBmbHIgdzE0MCI+PHN0cm9uZz7XkteZ15nXnyDXkNeZ15nXqDwvc3Ryb25nPjxici8+16nXqNec15XXmCDXkdeo15XXoNeY15Q8L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2J1eTciIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoL9eU15TXmdeh15jXldeo15nXlC3XqdecLdeU157Xl9eoIiAgdGl0bGU9IteU15TXmdeh15jXldeo15nXlCDXqdecINeU157Xl9eoIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+ODwvc3Bhbj48ZGl2IGNsYXNzPSJpYmxvY2sgZmxyIHcxNDAiPjxzdHJvbmc+15TXlNeZ16HXmNeV16jXmdeUINep15wg15TXnteX16g8L3N0cm9uZz48YnIvPteZ15XXkdecINeg15cg15TXqNeo15k8L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2J1eTgiIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoL9eU15fXmdeZ150t16nXnNeZLdeT15XXmC3Xp9eV150iICB0aXRsZT0i15TXl9eZ15nXnSDXqdec15kg15PXldeYINen15XXnSI+PHNwYW4gY2xhc3M9Im51bSBmbHIiPjk8L3NwYW4+PGRpdiBjbGFzcz0iaWJsb2NrIGZsciB3MTQwIj48c3Ryb25nPteU15fXmdeZ150g16nXnNeZINeT15XXmCDXp9eV1508L3N0cm9uZz48YnIvPtei16TXqNeUINeS15zXkdeo15gg15DXkdeg15k8L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaSBjbGFzcz0ibGFzdCI+PGEgaWQ9ImJvb2tidXk5IiBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9eh16TXqC/XlNeb16jXmdepIiAgdGl0bGU9IteU15vXqNeZ16kiPjxzcGFuIGNsYXNzPSJudW0gZmxyIj4xMDwvc3Bhbj48ZGl2IGNsYXNzPSJpYmxvY2sgZmxyIHcxNDAiPjxzdHJvbmc+15TXm9eo15nXqTwvc3Ryb25nPjxiciAvPtee15nXqden15Qg15HXny3Xk9eV15M8L2Rpdj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjwvdWw+ZAIHDxYCHwplFgICAQ8WAh8FBYMaPHVsIGNsYXNzPSJtZW51Ij48bGk+PGEgaWQ9ImJvb2thdWRpMCIgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16gvMjQt16nXoteV16ot15HXl9eZ15kt15DXmdep15QiIHRpdGxlPSIyNCDXqdei15XXqiDXkdeX15nXmdeUINep15wg15DXmdep15QiPjxzcGFuIGNsYXNzPSJwaWMiPjxpbWcgc3JjPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL2Jvb2tzcGljL2NiNmY0NjJiLTM3MDktNGVkMS1iYmNmLTUzYmM4YTA5NTQ5ZS5qcGciIGFsdD0iMjQg16nXoteV16og15HXl9eZ15nXlCDXqdecINeQ15nXqdeUIiBzdHlsZT0id2lkdGg6ODBweCIgLz48L3NwYW4+PHNwYW4gY2xhc3M9ImlibG9jayI+PHNwYW4gY2xhc3M9ImlibG9jayBibHVlIE1lb2RlZFBhc2h1dF9PRS1SZWd1bGFyIGZvbnQzMiI+MTwvc3Bhbj48YnIgLz48c3Ryb25nPjI0INep16LXldeqINeR15fXmdeZ15Qg16nXnCDXkNeZ16nXlDwvc3Ryb25nPjxiciAvPtep15jXpNefINem15XXldeZ15I8L3NwYW4+PC9hPjwvbGk+PGxpPjxhIGlkPSJib29rYXVkaTEiICBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9eh16TXqC/XoNek16kt15TXldee15nXlCIgdGl0bGU9Iteg16TXqSDXlNeV157XmdeUIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+Mjwvc3Bhbj48c3BhbiBjbGFzcz0iaWJsb2NrIGZsciB3MTQwIj48c3Ryb25nPteg16TXqSDXlNeV157XmdeUPC9zdHJvbmc+PGJyLz7XqNedINeQ15XXqNefPC9zcGFuPjxiciBjbGFzcz0iY2xlYXIiIC8+PC9hPjwvbGk+PGxpPjxhIGlkPSJib29rYXVkaTIiICBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9eh16TXqC/XmNei15XXqi3XkNeg15XXqSIgdGl0bGU9IteY16LXldeqINeQ16DXldepIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+Mzwvc3Bhbj48c3BhbiBjbGFzcz0iaWJsb2NrIGZsciB3MTQwIj48c3Ryb25nPteY16LXldeqINeQ16DXldepPC9zdHJvbmc+PGJyLz7XqdeV15zXnteZ16og15zXpNeZ15M8L3NwYW4+PGJyIGNsYXNzPSJjbGVhciIgLz48L2E+PC9saT48bGk+PGEgaWQ9ImJvb2thdWRpMyIgIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoL9eU16jXpNeq16fXkNeV16ot15PXldeTLdeQ16jXmdeULdeR15DXlden15nXoNeV16Et15TXmNeZ15HXmNeZIiB0aXRsZT0i15TXqNek16rXp9eQ15XXqiDXk9eV15Mg15DXqNeZ15QgKDYpINeR15DXlden15nXoNeV16Eg15TXmNeZ15HXmNeZIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+NDwvc3Bhbj48c3BhbiBjbGFzcz0iaWJsb2NrIGZsciB3MTQwIj48c3Ryb25nPteU16jXpNeq16fXkNeV16og15PXldeTINeQ16jXmdeUICg2KSDXkdeQ15XXp9eZ16DXldehINeU15jXmdeR15jXmTwvc3Ryb25nPjxici8+15nXoNelINec15XXmTwvc3Bhbj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2F1ZGk0IiAgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16gv16rXnNeV16nXlCIgdGl0bGU9Iteq15zXldep15QiPjxzcGFuIGNsYXNzPSJudW0gZmxyIj41PC9zcGFuPjxzcGFuIGNsYXNzPSJpYmxvY2sgZmxyIHcxNDAiPjxzdHJvbmc+16rXnNeV16nXlDwvc3Ryb25nPjxici8+157Xmdeb15wg15nXldeR15wt16TXmden16jXoden15k8L3NwYW4+PGJyIGNsYXNzPSJjbGVhciIgLz48L2E+PC9saT48bGk+PGEgaWQ9ImJvb2thdWRpNSIgIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXpNeoL9eU16jXpNeq16fXkNeV16ot15PXldeTLdeQ16jXmdeULdeR16LXqNeR15XXqi3XqNeV157XoNeZ15QiIHRpdGxlPSLXlNeo16TXqten15DXldeqINeT15XXkyDXkNeo15nXlCAoMSkg15HXoteo15HXldeqINeo15XXnteg15nXlCI+PHNwYW4gY2xhc3M9Im51bSBmbHIiPjY8L3NwYW4+PHNwYW4gY2xhc3M9ImlibG9jayBmbHIgdzE0MCI+PHN0cm9uZz7XlNeo16TXqten15DXldeqINeT15XXkyDXkNeo15nXlCAoMSkg15HXoteo15HXldeqINeo15XXnteg15nXlDwvc3Ryb25nPjxici8+15nXoNelINec15XXmTwvc3Bhbj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2F1ZGk2IiAgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16gv15TXqNep16ot16nXnC3XkNec15nXoSIgdGl0bGU9IteU16jXqdeqINep15wg15DXnNeZ16EiPjxzcGFuIGNsYXNzPSJudW0gZmxyIj43PC9zcGFuPjxzcGFuIGNsYXNzPSJpYmxvY2sgZmxyIHcxNDAiPjxzdHJvbmc+15TXqNep16og16nXnCDXkNec15nXoTwvc3Ryb25nPjxici8+16fXmdeZ15gg16fXldeV15nXnzwvc3Bhbj48YnIgY2xhc3M9ImNsZWFyIiAvPjwvYT48L2xpPjxsaT48YSBpZD0iYm9va2F1ZGk3IiAgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16gv16TXmdec15nXnS3XnNeQLdee16rXp9eR15zXmdedIiB0aXRsZT0i16TXmdec15nXnSDXnNeQINee16rXp9eR15zXmdedIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+ODwvc3Bhbj48c3BhbiBjbGFzcz0iaWJsb2NrIGZsciB3MTQwIj48c3Ryb25nPtek15nXnNeZ150g15zXkCDXnteq16fXkdec15nXnTwvc3Ryb25nPjxici8+15zXmdeW15Qg157XoNeY16bXs9eRPC9zcGFuPjxiciBjbGFzcz0iY2xlYXIiIC8+PC9hPjwvbGk+PGxpPjxhIGlkPSJib29rYXVkaTgiICBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9eh16TXqC/XlNeo16TXqten15DXldeqIC3Xk9eV15Mt15DXqNeZ15Qt15HXnteT15HXqC3XlNep15XXldeZ16bXqNeZIiB0aXRsZT0i15TXqNek16rXp9eQ15XXqiDXk9eV15Mg15DXqNeZ15QgKDMpINeR157Xk9eR16gg15TXqdeV15XXmdem16jXmSI+PHNwYW4gY2xhc3M9Im51bSBmbHIiPjk8L3NwYW4+PHNwYW4gY2xhc3M9ImlibG9jayBmbHIgdzE0MCI+PHN0cm9uZz7XlNeo16TXqten15DXldeqINeT15XXkyDXkNeo15nXlCAoMykg15HXnteT15HXqCDXlNep15XXldeZ16bXqNeZPC9zdHJvbmc+PGJyLz7Xmdeg16Ug15zXldeZPC9zcGFuPjxiciBjbGFzcz0iY2xlYXIiIC8+PC9hPjwvbGk+PGxpIGNsYXNzPSJsYXN0Ij48YSBpZD0iYm9va2F1ZGk5IiAgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/Xodek16gv15HXk9eo15ot15zXnteb15XXnNeqIiB0aXRsZT0i15HXk9eo15og15zXnteb15XXnNeqIj48c3BhbiBjbGFzcz0ibnVtIGZsciI+MTA8L3NwYW4+PHNwYW4gY2xhc3M9ImlibG9jayBmbHIgdzE0MCI+PHN0cm9uZz7XkdeT16jXmiDXnNee15vXldec16o8L3N0cm9uZz48YnIgLz7Xk9efINeU15XXpNeo15g8L3NwYW4+PGJyIGNsYXNzPSJjbGVhciIgLz48L2E+PC9saT48L3VsPmQCBQ9kFgQCAQ8WAh8FBekDPGxpPjxhIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXldek16jXmdedL9eQ16jXmdeaLden16HXmNeg16giPteQ16jXmdeaINen16HXmNeg16g8L2E+PC9saT48bGk+PGEgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/XodeV16TXqNeZ150v16nXmNek158t16bXldeV15nXkiI+16nXmNek158g16bXldeV15nXkjwvYT48L2xpPjxsaT48YSBocmVmPSJodHRwczovL2Jvb2tzLmljYXN0LmNvLmlsL9eh15XXpNeo15nXnS/XkNeT15XXlC3XkdeV15zXlCI+15DXk9eV15Qg15HXldec15Q8L2E+PC9saT48bGk+PGEgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/XodeV16TXqNeZ150v15zXmdei15Mt16nXlNedIj7XnNeZ16LXkyDXqdeU1508L2E+PC9saT48bGk+PGEgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/XodeV16TXqNeZ150v15DXk9eZ15HXlC3Xktek158iPteQ15PXmdeR15Qg15LXpNefPC9hPjwvbGk+ZAIDDxYCHwUFjQQ8bGk+PGEgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/XodeV16TXqNeZ150v16nXlNeo15Qt15HXnNeQ15UiPtep15TXqNeUINeR15zXkNeVPC9hPjwvbGk+PGxpPjxhIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXldek16jXmdedL9eV16jXky3Xqdeg15HXnCI+15XXqNeTINep16DXkdecPC9hPjwvbGk+PGxpPjxhIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXldek16jXmdedL9eT15XXqNeV158t16nXoNei16giPteT15XXqNeV158g16nXoNei16g8L2E+PC9saT48bGk+PGEgaHJlZj0iaHR0cHM6Ly9ib29rcy5pY2FzdC5jby5pbC/XodeV16TXqNeZ150v15PXoNeULdeQ15zXoteW16gt15TXnNeV15kiPteT16DXlCDXkNec16LXlteoINeU15zXldeZPC9hPjwvbGk+PGxpPjxhIGhyZWY9Imh0dHBzOi8vYm9va3MuaWNhc3QuY28uaWwv16HXldek16jXmdedL9ei15XXpNeo15Qt16LXldek16gt15DXldeo158iPtei15XXpNeo15Qg16LXldek16gg15DXldeo1588L2E+PC9saT5kAgEPFgIfBWVkAgIPZBYCAgEPZBYCZg8WAh8FBVw8ZGl2IHN0eWxlPSJESVJFQ1RJT046IHJ0bCI+15TXqNep157XlSDXoteb16nXmdeVINecLWlDYXN0Jm5ic3A715zXktee16jXmSDXkdeX15nX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',
            '__VIEWSTATEGENERATOR': '5B5482AA',
            '__PREVIOUSPAGE': 'DbMgHv4Z4KprXAXo0PaPMHi285uAfsubfYahBsQv00JxcOcG7HAF5Y_HQY9ZJOwFHbMa0oHmVHBKjrrI0dDqRTps4Xrx7Tx7apP452pv0BWPt9ovs689rjBTX4Ys4Xbn0',
            '__EVENTVALIDATION': '/wEdABngSSpgtVBhw96Yrq5OYLLnBYSGEKXzJhINnmER3jLq2arx0XKrWyOXqofnZTu8DLG+XBI5Aeu1p93IKvYYQ2Ah2Rv+KjhiTMk4Wo1pLsCLmiENqy3v/ICGxQ7FP5PVRARtFJY843nHCXBAWcEkS/S2R1k/ZSDnLIxagSy4y5ibnv0MG8cSUVzHu4v5tAJ6FQ+qjDgMfXd5/1+vc+qXpgVIp5AAqmtVubpdh3Ucpkurxa83eamUfHHX6wb05xnFtOvRZ7HTAatRuHUC4M398Xcj2pntP3K46GR7eOflsSs0cdULnNiWNaHwKJtiWy4ShVQqM/S92odCs91JPwYC0tyCsD3Gs2Lfbi3BIlgMnJ4tv9CoR82hDUuBYhWIeovGa5OYR/owbub1pcUvMI69qy2caab98G9nvWWca8JynTNYPF4ShptrlP4azTEUuQC7FUZjuxJLUrCBLXWp7arp29T3d8ErUUS5w4mRz98qnTIdQBJ+WBgS8+eqdZWlgaBafgjMx5/WiwN85pWmuEymiFcwtiNc5ysQeN6CERV3grUmS9B+k9QD8I6itjJPwTHmq9c=',
            'SearchText': 'סופר / קריין / ספר',
            'ctl00$MainHolder$txtName': '',
            'ctl00$MainHolder$txtMail': '',
            'ctl00$MainHolder$txtPass': '',
            'ctl00$MainHolder$txtPassConfirm': '',
            'ctl00$MainHolder$txtCapcha': '',
            'ctl00$MainHolder$LoginBox$UserName': CONFIG['email'],
            'ctl00$MainHolder$LoginBox$Password': CONFIG['password'],
            'ctl00$MainHolder$txtSendMail': '',
            'ctl00$MainHolder$SiteFooter$txtMailSend': '',
            '__ASYNCPOST': 'true'}
    session = requests.session()
    session.post(LOGIN_URL, data=data, headers=HEADERS, allow_redirects=True)
    return session


def get_book(session, url, target):
    r = session.get(url)
    root = html.fromstring(r.text)
    script = root.xpath('//*[@id="colomn_main2"]/div/span/script[1]')
    pre_json = script[0].text

    pre_json = pre_json.replace("var player = new BooksPlayer(", '')[:-3]
    # print(pre_json)
    json_obj = yaml.load(pre_json.replace('\t', '').replace('free:false,', '').strip())
    if not target:
        book_title_clean = root.xpath('/html/head/title')[0].text.replace('\r\n', '').replace('\t', '').replace(':', '').replace('?', '')
        target = os.path.join('./books/', book_title_clean)
    if not os.path.isdir(target):
        os.mkdir(target)
        logging.info('creating destination for downloaded books')
    else:
        logging.info('using {} as destination'.format(target))

    digits_number_in_item_count = len(str(len(json_obj['list'])))
    item_counter = 1
    for item in json_obj['list']:
        filename = item['name'] + '.mp3'
        if 'הודעת זכויות' in filename:
            continue
        filename = str(item_counter).zfill(digits_number_in_item_count) + ' - ' + filename.replace(':', '-').replace('?', '')
        filepath = os.path.join(target, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as book_file:
                response = session.get(item['mp3'],
                                       stream=True)
                for chunk in response:
                    book_file.write(chunk)
        item_counter += 1
    logging.info('Finished downloading book')
    return


def scrape_search(session, search_url):
    response = session.get(search_url, headers=HEADERS, allow_redirects=True)
    with open('tmp.txt', 'w', encoding='utf-8') as file:
        file.write(response.text)
    root = html.fromstring(response.text)
    books = []
    for i in range(6, 1000, 2):
        book_url = root.xpath(f'//*[@id="MainHolder_pnlSearch"]/div[{i}]/div[2]/a[1]')
        if book_url:
            books.append({'url': book_url[0].attrib['href']})

    return books


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--config', help='configuration file to load')
    parser.add_argument('-D', '--debug', help='enable debug mode', action='store_true')
    parser.add_argument('-e', '--email', help='your icast account email')
    parser.add_argument('-p', '--password', help='your icast account password')
    parser.add_argument('-t', '--target', help='folder to keep downloaded files in', default='./books')
    parser.add_argument('-u', '--url', help='Audio book url')
    args = parser.parse_args()

    global CONFIG
    CONFIG = setup(args)
    set_arg_in_config(args, 'password')
    if CONFIG.get('password') is None:
        CONFIG['password'] = getpass.getpass()

    set_arg_in_config(args, 'email')

    # books = [
             # {'name': 'אהבה זה כל הספר',
             #  'url': 'http://books.icast.co.il/%D7%A1%D7%A4%D7%A8/%D7%90%D7%94%D7%91%D7%94-%D7%96%D7%94-%D7%9B%D7%9C-%D7%94%D7%A1%D7%A4%D7%A8'},
             # {'name': 'קהלת הפילוסוף המקראי',
             #  'url': 'http://books.icast.co.il/%D7%A1%D7%A4%D7%A8/%D7%A7%D7%94%D7%9C%D7%AA-%D7%94%D7%A4%D7%99%D7%9C%D7%95%D7%A1%D7%95%D7%A3-%D7%94%D7%9E%D7%A7%D7%A8%D7%90%D7%99'},
             # {'name': 'שיחות על תורת המספרים',
             #  'url': '%D7%A1%D7%A4%D7%A8/%D7%A9%D7%99%D7%97%D7%95%D7%AA-%D7%A2%D7%9C-%D7%AA%D7%95%D7%A8%D7%AA-%D7%94%D7%9E%D7%A9%D7%97%D7%A7%D7%99%D7%9D'},
             # {'name': 'סודותיו של מורה הנבוכים',
             #  'url': 'http://books.icast.co.il/%D7%A1%D7%A4%D7%A8/%D7%A9%D7%99%D7%97%D7%95%D7%AA-%D7%A2%D7%9C-%D7%AA%D7%95%D7%A8%D7%AA-%D7%94%D7%9E%D7%A9%D7%97%D7%A7%D7%99%D7%9D'},
             # {'name': 'המוח המשותף',
             #  'url': 'http://books.icast.co.il/%D7%A1%D7%A4%D7%A8/%D7%94%D7%9E%D7%95%D7%97-%D7%94%D7%9E%D7%A9%D7%95%D7%AA%D7%A3'},
             # {'name': 'דודי שמחה',
             #  'url': 'http://books.icast.co.il/%D7%A1%D7%A4%D7%A8/%D7%93%D7%95%D7%93%D7%99-%D7%A9%D7%9E%D7%97%D7%94'},
             # {'name': 'קיצור תולדות האנושות',
             #  'url': 'http://books.icast.co.il/%D7%A1%D7%A4%D7%A8/%D7%A7%D7%99%D7%A6%D7%95%D7%A8-%D7%AA%D7%95%D7%9C%D7%93%D7%95%D7%AA-%D7%94%D7%90%D7%A0%D7%95%D7%A9%D7%95%D7%AA'}
             # ]

    session = get_login_session()
    books = scrape_search(session, 'http://books.icast.co.il/%D7%A1%D7%95%D7%A4%D7%A8%D7%99%D7%9D/%D7%93%D7%A2%D7%90%D7%9C-%D7%A9%D7%9C%D7%95')

    for book in books:
        # target = './books/' + book['name']
        get_book(session, book['url'], '')


if __name__ == '__main__':
    main()
