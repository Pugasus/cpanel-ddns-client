#   A ddns client to update a dns record hosted on a cPanel server
#   Intended to be setup as a cron job
#
#   Copyright (C) 2017 Alex Perusco
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   You should have received a copy of the GNU General Public License
#   along with this program. If not, see <http://www.gnu.org/licenses/gpl.html>.

import requests
import sys
import json
import socket
import re
from cpanelapi import client
import datetime

print "{}: Checking DDNS".format(datetime.datetime.now())

#### Globals ####
cPanelHostname = "cpanelserver.com"
cPanelUsername = "cpanelUsername"
cPanelPassword = "cpanelPassword"
domain = "example.com"
subdomain = "sub"
ttl = 60

#First setup requests headers so it has a valid User-Agent

headers = requests.utils.default_headers()
headers.update(
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
)

#Get our current IP
try:
    r = requests.get("http://icanhazip.com", headers=headers) 
    r.raise_for_status()
except requests.exceptions.RequestException as e:
    print "{}: Failed to get our current IP".format(datetime.datetime.now())
    print e
    sys.exit(1)

myIP = r.text.strip()
print "{}: My IP is {}".format(datetime.datetime.now(), myIP)

#Check DNS we need to match against
try:
    currentDNS = socket.gethostbyname(subdomain + "." + domain)
except socket.error as e:
    print "Failed to lookup DNS"
    print e
    sys.exit(1)

print "{}: {}.{} resolves to {}".format(datetime.datetime.now(), subdomain, domain, currentDNS)

#Check if IP and DNS match and update if necessary
if myIP != currentDNS:
    print "{}: IPs DONT match".format(datetime.datetime.now())
    #Check we have a valid IP
    if re.match("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", myIP) is not None:

        #Initialise cPanel api client
        cpapi = client.Client(cPanelUsername, cPanelHostname, password=cPanelPassword, ssl=True, cpanel=True)
        
        #Fetch zone to check which line in the zone file we need to update
        try:
             fetchResult = cpapi.api2("ZoneEdit", "fetchzone", domain=domain, name=subdomain + "." + domain + ".")
             lineToEdit = fetchResult['cpanelresult']['data'][0]['record'][0]['line']
        except requests.exceptions.RequestException as e:
             print "{}: cPanel fetch zone API call failed".format(datetime.datetime.now())
             print e
             sys.exit(1)

        #Catch IndexError. This means fetchResult had an empty list for 'record'
        except IndexError:
            print "{}: cPanel fetch zone API call returned no record".format(datetime.datetime.now())
            print "{}: Can't find the record we need to update!".format(datetime.datetime.now())
            sys.exit(1)

        #Execute dns update
        try:
            editResult = cpapi.api2("ZoneEdit", "edit_zone_record", line=lineToEdit, domain=domain, name=subdomain, type="A", ttl=ttl, address=myIP)
        except requests.exceptions.RequestException as e:
            print "{}: cPanel edit zone API call failed".format(datetime.datetime.now())
            print e
            sys.exit(1)

        print "{}: cPanel zone edit API call result is {}".format(datetime.datetime.now(), editResult['cpanelresult']['data'][0])
        
    else:
        print "{}: Could not update DNS, my IP was an invalid address".format(datetime.datetime.now())
        sys.exit(1)
else:
    print "{}: IPs match".format(datetime.datetime.now())

sys.exit(0)

