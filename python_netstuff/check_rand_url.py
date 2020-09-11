#!/usr/bin/python

import httplib
import httplib2
import random
import argparse
import sys
import re

# regex to grab domain but not path:
#	[._\-a-zA-Z0-9]*\.[a-zA-Z]+

from BeautifulSoup import BeautifulSoup, SoupStrainer

def split_path(url):
    if 'https:' in url:
        url=url.replace('https://','')
        url=url.replace('https:','')
    elif 'http:' in url:
        url=url.replace('http://','')
        url=url.replace('http:','')
    string=re.compile("[._\-a-zA-Z0-9]*\.[a-zA-Z]+")
    site=string.match(url).group()
    path=url.replace(site,'')
    if path == '':
        path='/'
    return site,path


def get_status_code(host, path="/"):
    """ This function retreives the status code of a website by requesting
        HEAD data from the host. This means that it only requests the headers.
        If the host cannot be reached or something else goes wrong, it returns
        None instead.
    """
    try:
        conn = httplib.HTTPConnection(host)
        conn.request("HEAD", path)
        return conn.getresponse().status
    except StandardError:
        return None

parser = argparse.ArgumentParser(description="Check random links on page of website")
parser.add_argument('-s', '--site', help="Site to check")
args=parser.parse_args()

if 'http://' not in args.site and 'https://' not in args.site:
    if 'http:' in args.site or 'https:' in args.site:
        args.site=args.site.replace(':','://')
    else:
        args.site='http://'+args.site

site,path=split_path(args.site)

statuscode=get_status_code(site,path)
if statuscode != 200:
        print " Warning, statuscode returned %d" % statuscode
        if statuscode == 404:
                sys.exit(2) # prints 200
        sys.exit(3)
else:
    http = httplib2.Http()
    status, response = http.request(args.site)

    results=[]
    for link in BeautifulSoup(response, parseOnlyThese=SoupStrainer('a')):
            if link.has_key('href') and str(args.site) in link['href']:
                results.append(link['href'])
        if link.has_key('href') and link['href'][:1] =='/':
            results.append(args.site+link['href'])
        elif link.has_key('href') and 'http' not in link['href'] and 'https' not in link['href']:
            results.append(args.site+'/'+link['href'])
    if len(results) <=0:
        print "Warning, no obvious a href links were found on the front page"
        print "This can becaused by relative links not getting parsed by regex"
        sys.exit(1)    

    site,path=split_path(results[random.randrange(1,len(results),1)])
    statuscode=get_status_code(site,path)
    if statuscode != 200:
        print 'warning, status code returned status %s' % statuscode
        sys.exit(3)
    else:
        print 'status code returned %s for %s and %s%s' % (statuscode, args.site, site, path)
        sys.exit(0)    
