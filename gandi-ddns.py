#!/usr/bin/python

import xmlrpclib
import urllib2
import sys

# gandi.net API (Production) key
apikey = '<apikey>'
# Domains, A-names to be updated
# XXX THIS IS ONLY AN EXAMPLE, EDIT TO SUIT YOUR NEEDS
domains = { '<domain1>': [ '@' ]
          , '<domain2>': [ '<a_name2>' ]
          }

# TTL (seconds = 5 minutes to 30 days)
ttl = 900
# Production API
api = xmlrpclib.ServerProxy('https://rpc.gandi.net/xmlrpc/', verbose=False)
# Used to cache the zone_ids for future calls
zone_ids = {}

def get_zone_id(domain):
  """ Get the gandi.net ID for the current zone version"""

  global zone_ids

  # If we've not already got the zone ID, get it
  if not domain in zone_ids:
    # Get domain info then check for a zone
    domain_info = api.domain.info(apikey, domain)
    current_zone_id = domain_info['zone_id']

    if current_zone_id == 'None':
      print 'No zone for ', domain, ' - make sure domain is set to use gandi.net name servers.'

    zone_ids[domain] = current_zone_id

  return zone_ids[domain]

def get_zone_ip(domain, name):
  """Get the current IP from the A record in the DNS zone """

  current_zone = api.domain.zone.record.list(apikey, get_zone_id(domain), 0)
  ip = '0.0.0.0'
  # There may be more than one A record - we're interested in one with 
  # the specific name (typically @ but could be sub domain)
  for d in current_zone:
    if d['type'] == 'A' and d['name'] == name:
      ip = d['value']

  return ip

def get_ip():
  """ Get external IP """

  try:
    # Could be any service that just gives us a simple raw ASCII IP address (not HTML etc)
    result = urllib2.urlopen("http://ipv4.myexternalip.com/raw", timeout=3).read()
  except Exception:
    print 'Unable to external IP address.'
    sys.exit(2);

  return result

def change_zone_ip(new_ip, domain, name):
  """ Change the zone record to the new IP """

  zone_record = {'name': name, 'value': new_ip, 'ttl': ttl, 'type': 'A'}

  new_zone_ver = api.domain.zone.version.new(apikey, get_zone_id(domain))

  # clear old A record (defaults to previous verison's
  api.domain.zone.record.delete(apikey, get_zone_id(domain), new_zone_ver,{'type':'A', 'name': a_name})

  # Add in new A record
  api.domain.zone.record.add(apikey, get_zone_id(domain), new_zone_ver, zone_record)

  # Set new zone version as the active zone
  api.domain.zone.version.set(apikey, get_zone_id(domain), new_zone_ver)


for domain in domains:
  for a_name in domains[domain]:
    print a_name, domain
    zone_ip = get_zone_ip(domain, a_name)
    current_ip = get_ip()

    if (zone_ip.strip() == current_ip.strip()):
      continue

    else:
      print domain, 'DNS Mistmatch detected: A-name:', a_name, 'A-record: ', zone_ip, ' WAN IP: ', current_ip
      change_zone_ip(current_ip, domain, a_name)
      zone_ids = {}
      zone_ip = get_zone_ip(domain, a_name)
      print domain, 'DNS A-name', a_name, 'update complete - set to', zone_ip

