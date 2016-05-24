#!/usr/bin/python

# id like to make a script that counts incidents per IP per rule

#       rule:
#               ip:count
import socket
import pprint
import sys
import argparse
import re

def getname(address):
        try:
                return socket.gethostbyaddr(address)[0]
        except:
                return address

def populate_dicts():
        rule=""
        priority=0
        for line in open(args.file):
                line=line.strip()
                if args.b:
                        ip=re.findall("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", line)
                else:
                        ip=re.findall("10\.[0-9]+\.[0-9]+\.[0-9]+", line)               
                if '[**]' in line:
                        rule=str(line)
                        rule=rule[:-5]
                        rule=rule[5:]
                if '[Priority:' in line:
                        priority=line[-2:-1]
                if not rule in rule_dict:
                        rule_dict[rule]={}

                if ip:
                        for addr in ip:


                                if not addr in addr_dict:
                                        addr_dict[addr]=getname(addr)
                                if addr in addr_dict:
                                        addr=addr_dict[addr]

                                if not addr in rule_dict[rule]:
                                        rule_dict[rule][addr]=1
                                else:
                                        rule_dict[rule][addr]+=1
                if priority:
                        rule_dict[rule]['Priority']=priority

parser = argparse.ArgumentParser(description="Count Incident Rates")
parser.add_argument('-f', '--file', help='File to inspect', 
                default='/var/log/snort/alert')
parser.add_argument('-i', '--ip', help='Specify target IP address')
parser.add_argument('-b', action='store_true', help='include Both internal and external addresses, default internal only')
args=parser.parse_args()

startFlag=False
second_preceding=""
first_preceding=""

rule_dict={}
addr_dict={}


        
populate_dicts()

pp=pprint.PrettyPrinter(indent=4)

for priority in range(1,4):
        print '\n******[Priority: ' + str(priority) + ']******'
        for key, value in rule_dict.iteritems():
                try:    
                        if rule_dict[key]['Priority'] == str(priority):
                                #rule_dict[key].pop('Priority', None)
                                print "\n   " + key
                                for ip, count in rule_dict[key].items():
                                        if ip == 'Priority':
                                                pass
                                        else:
                                                print "      " + ip + ":" + str(count) 
                except:
                        print "\n whoops; skipping this one .... Julian scripts like [REDACTED]." 


pp=pprint.PrettyPrinter(indent=4)

#pp.pprint(rule_dict['Priority'].values().index('1'))

#pp.pprint(rule_dict)
