#!/usr/bin/env python

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option, validators
import sys
import os
try:
    # python2
    import ConfigParser as configparser
    from StringIO import StringIO as BytesIO
    import urllib2 as urllib_functions
except:
    # python3
    import configparser
    from io import BytesIO
    import urllib.request as urllib_functions
from zipfile import ZipFile
import re
import socket
import struct

@Configuration(type='reporting')
class ASNGenCommand(GeneratingCommand):

    def generate(self):

        proxies = {'http': None, 'https': None}
        maxmind = {'license_key': None}

        try:
            config = configparser.ConfigParser()
            # first try to read the defaults (in case we are in a cluster with deployed config)
            config.read(os.path.join(os.getcwd(), '../default/asngen.conf'))
            # then try to read the overrides
            config.read(os.path.join(os.getcwd(), '../local/asngen.conf'))

            if config.has_section('proxies'):
                if config.has_option('proxies', 'https'):
                    if len(config.get('proxies', 'https')) > 0:
                        proxies['https'] = config.get('proxies', 'https')

            if config.has_section('maxmind'):
                if config.has_option('maxmind', 'license_key'):
                    if len(config.get('maxmind', 'license_key')) > 0:
                        maxmind['license_key'] = config.get('maxmind', 'license_key')

        except:
            raise Exception("Error reading configuration. Please check your local asngen.conf file.")

        if proxies['https'] is not None:
            proxy = urllib_functions.ProxyHandler(proxies)
            opener = urllib_functions.build_opener(proxy)
            urllib_functions.install_opener(opener)

        if maxmind['license_key'] is None:
            raise Exception("maxmind license_key is required")

        try:
            link = "https://download.maxmind.com/app/geoip_download" + "?"
            link += "edition_id=GeoLite2-ASN-CSV" + "&"
            link += "license_key=" + maxmind['license_key'] + "&"
            link += "suffix=zip"
            url = urllib_functions.urlopen(link)
        except:
            raise Exception("Please check app proxy settings and license_key.")

        if url.getcode()==200:
            try:
                zipfile = ZipFile(BytesIO(url.read()))
            except:
                raise Exception("Invalid zip file")
        else:
            raise Exception("Received response: " + url.getcode())

        for name in zipfile.namelist():
            entries = re.findall(b'^(\d+\.\d+\.\d+\.\d+)\/(\d+),(\d+),\"?([^\"\n]+)\"?', zipfile.open(name).read(), re.MULTILINE)
            for line in entries:
                yield {
                    'ip': line[0].decode('utf-8', 'ignore') + "/" + 
                          line[1].decode('utf-8', 'ignore'),
                    'asn': line[2].decode('utf-8', 'ignore'),
                    'autonomous_system': line[3].decode('utf-8', 'ignore')}

dispatch(ASNGenCommand, sys.argv, sys.stdin, sys.stdout, __name__)
