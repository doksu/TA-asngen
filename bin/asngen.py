#!/usr/bin/env python

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option, validators
import sys
import os
import ConfigParser
from StringIO import StringIO
from zipfile import ZipFile
from urllib import urlopen
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
                if configparser.has_option('proxies', 'http'):
                    if len(configparser.get('proxies', 'http')) > 0:
                        proxies['http'] = configparser.get('proxies', 'http')
                if configparser.has_option('proxies', 'https'):
                    if len(configparser.get('proxies', 'https')) > 0:
                        proxies['https'] = configparser.get('proxies', 'https')

        except:
            pass

        if proxies['http'] is not None or proxies['https'] is not None:
            proxy = ProxyHandler(proxies)
            opener = build_opener(proxy)
            install_opener(opener)

        try:
            url = urlopen("https://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum2.zip")
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
            entries = re.findall(r'^(\d+),(\d+),\"AS(\d+) ([^\"]+)\"', zipfile.open(name).read(), re.MULTILINE)

        for line in entries:
            diff = (int(line[1]) - int(line[0])) -1
            ip = socket.inet_ntoa(struct.pack('!L', int(line[0])))

            # there's almost certainly a more elegant way of doing this but it works
            if diff<2**2:
                mask = 30
            elif diff<2**3:
                mask = 29
            elif diff<2**4:
                mask = 28
            elif diff<2**5:
                mask = 27
            elif diff<2**6:
                mask = 26
            elif diff<2**7:
                mask = 25
            elif diff<2**8:
                mask = 24
            elif diff<2**9:
                mask = 23
            elif diff<2**10:
                mask = 22
            elif diff<2**11:
                mask = 21
            elif diff<2**12:
                mask = 20
            elif diff<2**13:
                mask = 19
            elif diff<2**14:
                mask = 18
            elif diff<2**15:
                mask = 17
            elif diff<2**16:
                mask = 16
            elif diff<2**17:
                mask = 15
            elif diff<2**18:
                mask = 14
            elif diff<2**19:
                mask = 13
            elif diff<2**20:
                mask = 12
            elif diff<2**21:
                mask = 11
            elif diff<2**22:
                mask = 10
            elif diff<2**23:
                mask = 9
            elif diff<2**24:
                mask = 8
            elif diff<2**25:
                mask = 7
            elif diff<2**26:
                mask = 6
            elif diff<2**27:
                mask = 5
            elif diff<2**28:
                mask = 4
            elif diff<2**29:
                mask = 3
            elif diff<2**30:
                mask = 2

            yield {'ip': ip + "/" + str(mask), 'start': line[0], 'end': line[1], 'asn': line[2], 'autonomous_system': line[3].decode('utf-8', 'ignore')}

dispatch(ASNGenCommand, sys.argv, sys.stdin, sys.stdout, __name__)
