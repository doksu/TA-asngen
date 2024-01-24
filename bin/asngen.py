import sys,os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from splunklib.searchcommands import GeneratingCommand, Option, validators
from splunklib.searchcommands import Configuration, dispatch
import base64
import json
import configparser
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import re

SECRET_REALM = 'TA-asngen_realm'
SECRET_NAME = 'TA-asngen_admin'

@Configuration()
class ASNCommand(GeneratingCommand):

    def generate(self):
        proxies = {'http': None, 'https': None}
        license_key = None
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(os.path.join(os.path.dirname(__file__), "..", "local", "asn.conf"))
            self.get_proxies(config_parser, proxies)
            license_key = self.get_license_key()
        except:
            raise Exception("Error: Reading configuration file. Retry setting up the application or check asn.conf")
        if proxies['https'] is not None and proxies['https'] != 'undefined':
            urllib_proxies = urllib.request.ProxyHandler(proxies)
            opener = urllib.request.build_opener(urllib_proxies)
            urllib.request.install_opener(opener)

        if license_key is None:
            raise Exception("Error: Please provide a Maxmind license key.")

        try:
            link = "https://download.maxmind.com/app/geoip_download" + "?"
            link += "edition_id=GeoLite2-ASN-CSV" + "&"
            link += "license_key=" + license_key + "&"
            link += "suffix=zip"
            url = urllib.request.urlopen(link)
            
        except Exception as e:
            raise e
            #raise Exception("Error: Please check the app configurations under asn.conf. Couldn't connect to MaxMind")
                
        if url.getcode() == 200:
            try:
                zipfile = ZipFile(BytesIO(url.read()))
            except:
                raise Exception("Error: No Zip file found or invalid file.")
        else:
            raise Exception("Error: {}".format(url.getcode()))
        
        for name in zipfile.namelist():
            entries = re.findall(b'^(\d+\.\d+\.\d+\.\d+)\/(\d+),(\d+),\"?([^\"\n]+)\"?', zipfile.open(name).read(), re.MULTILINE)
            for line in entries:
                yield {'ip': line[0].decode("utf-8") + "/" + line[1].decode("utf-8"), 'asn': line[2].decode("utf-8"), 'autonomous_system': str(line[3].decode('utf-8', 'ignore'))}

    def get_proxies(self, config_parser, proxies):
        """Retrieve appropriate proxies if they exist"""
        if config_parser.has_section('proxies'):
                if config_parser.has_option('proxies', 'https'):
                    if len(config_parser.get('proxies', 'https')) > 0:
                        proxies['https'] = config_parser.get('proxies', 'https')
    
    def get_license_key(search_command):
        secrets = search_command.service.storage_passwords
        return next(secret for secret in secrets if (secret.realm == SECRET_REALM and secret.username == SECRET_NAME)).clear_password               
        
                

if __name__ == "__main__":
    dispatch(ASNCommand, sys.argv, sys.stdin, sys.stdout, __name__)
