#!/usr/bin/env python3

######
# python utility to facilitate active directory stuff
######

import pprint
from ldap3 import Server, Connection, Tls, SASL, KERBEROS
import ssl
import random
from os import getlogin
import sys


class ldapsearch():
  results={}

  def __init__(self,search_filter,search_base="dc=yourDomain,dc=com"):
    username = getlogin()
    attrs=['*']
    tls = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
    server = Server('ldap://yourDomainController.com', use_ssl=True, tls=tls)
    c = Connection(server, authentication=SASL, sasl_mechanism=KERBEROS)
    c.bind()
    c.search(search_base, search_filter, attributes=attrs)
    return c
    self.results=c.entries
    c.unbind()


def search(search_filter,search_base="dc=yourDomain,dc=com"):
    username = getlogin()
    attrs=['*']
    tls = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
    server = Server('ldap://yourDomainController.com', use_ssl=True, tls=tls)
    c = Connection(server, authentication=SASL, sasl_mechanism=KERBEROS)
    c.bind()
    c.search(search_base, search_filter, attributes=attrs)
    return c

def managerDnToEmail(dn):
  c=search('(distinguishedName=%s)' % dn)
  return c.entries[0].mail

def main():
  #placeholder functions
  #  c=search('(cn=%s)' % sys.argv[1])
  #  c=search('(sn=%s)' % sys.argv[1])
  c=search(sys.argv[1])
  for entry in c.entries:
    for member in entry.member:
      print(member)

if __name__ == "__main__":
  main()
