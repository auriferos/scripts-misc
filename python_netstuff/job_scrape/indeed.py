import requests
import os
import xml.etree.ElementTree as eTree
import re
from bs4 import BeautifulSoup
#from BeautifulSoup import BeautifulSoup

def strip_summary(url):
    response=requests.get(url)
    if response.status_code != 200:
        raise LookupError('did not get 200 response for strip_sumamry url')
    soup=BeautifulSoup(response.content)    
    snippets=soup.find('td', {"class":"snip"})
    return snippets


def strip_paragraph(soup_tag, paragraph_index):
    paragraphs=list(soup_tag.stripped_strings)
    if len(paragraphs) > 0:
        #mystr=list(paragraphs)[paragraph_index].encode('utf8', errors='ignore')
        return list(paragraphs)[paragraph_index].encode('utf8', errors='ignore')
    else:
        return "No <p> tags in this post......"
        #used to throw error, but some people just suck at formatting their listings






def search_indeed(
    query_str, 
    version=2,             
    ZIP=94949, 
    location='Novato, Ca',         #we primarily use zip, #but will add switch later...
    radius=30,            #geo radius (miles?)        
    start=0,            #index of first result (necessary for queries over 'limit'?)'''
    limit=5,            #results per response

    fromage=1,             #max_age of posts in days
    userip='138.68.31.216',        #just gonna use personal ip for now...
    useragent='Python-requests/2.6.0'):


    assert type(ZIP) is int, "ZIP is an INTERGER"

    listings={}


    indeed_api_id=os.environ['INDEED_API_ID']

    qstr='publisher=%s&q=%s&l=%s&sort=&radius=%s&st=&jt=&start=&limit=%s&fromage=%s&filter=&latlong=1&co=us&chnl=&userip=%s&useragent=%s&v=%s' % (indeed_api_id, query_str, ZIP, radius, limit, fromage, userip, useragent, version)



    response=requests.get('http://api.indeed.com/ads/apisearch?%s' % qstr)

    if response.status_code == 404:
        empty_list={}
        raise LookupError('search_api query 404d; perhaps API has changed?')
        return empty_dict

    root=eTree.fromstring(response.content)

    
    for child in root.iter(tag='result'):

        company=child.find('company').text.encode('utf8')
        listing=child.find('jobtitle').text.encode('utf8')
        url_unclean=child.find('url').text.encode('utf8')
        ''' 'http://[./a-z0-9?=]+' regex finds up until first &; generally this includes jobkey'''
    
        url=re.search('http://[./a-z0-9?=]+', url_unclean).group(0)
        snippet=child.find('snippet').text.encode('utf8')
        location=child.find('formattedLocationFull').text.encode('utf8')
        jobkey=child.find('jobkey').text.encode('utf8')
    
        '''the builtin snippet sucks, so let's use the first
        paragraph instead'''
        post_body=strip_summary(url)
        snippet=strip_paragraph(post_body, 0)        

        if jobkey is None:
            continue

        listings[jobkey]=[listing,url,location,snippet,company]


    return listings

