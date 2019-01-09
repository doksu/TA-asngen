#!/usr/bin/env python

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option, validators
import sys
import os
import ConfigParser
from StringIO import StringIO
from zipfile import ZipFile
import urllib2
import re
import socket
import struct

@Configuration(type='reporting')
class ASNGenCommand(GeneratingCommand):

    def generate(self):

        proxies = {'http': None, 'https': None}

        try:
            configparser = ConfigParser.ConfigParser()
            configparser.read(os.path.join(os.environ['SPLUNK_HOME'], 'etc/apps/TA-asngen/local/asngen.conf'))

            if configparser.has_section('proxies'):
                if configparser.has_option('proxies', 'https'):
                    if len(configparser.get('proxies', 'https')) > 0:
                        proxies['https'] = configparser.get('proxies', 'https')

        except:
            pass

        if proxies['https'] is not None:
            proxy = urllib2.ProxyHandler(proxies)
            opener = urllib2.build_opener(proxy)
            urllib2.install_opener(opener)

        try:
            url = urllib2.urlopen("https://geolite.maxmind.com/download/geoip/database/GeoLite2-ASN-CSV.zip")
        except:
            raise Exception("Please check app proxy settings")

        if url.getcode()==200:
            try:
                zipfile = ZipFile(StringIO(url.read()))
            except:
                raise Exception("Invalid zip file")
        else:
            raise Exception("Received response: " + url.getcode())

        for name in zipfile.namelist():
            entries = re.findall(r'^(\d+\.\d+\.\d+\.\d+)\/(\d+),(\d+),(.*)', zipfile.open(name).read(), re.MULTILINE)

        for line in entries:
            yield {'ip': line[0] + "/" + line[1], 'asn': line[2], 'autonomous_system': line[3].decode('utf-8', 'ignore')}

dispatch(ASNGenCommand, sys.argv, sys.stdin, sys.stdout, __name__)
