#!/usr/bin/python
#import random
#for x in range(0,100):
#	number = random.randrange(1,180)
#	print number

# intended to bind against AD and modify reset pwdLastSet field a random number between a range.
# just as useful for dumping the ldap tree into a text file, or querying specific attributes.

import pprint
import ldap
from ldap import sasl
import ldap.modlist as modlist
import random


ldap_serv = "something.something.org"
base_dn = "dc=something,dc=org"
# username accepts active directory username if AD ldap instance.
username = 'cn=admin,dc=something,dc=org'
# passwd not used or needed if you've got a kerberos ticket.
passwd = 'lol no such luck'
target_attr = 'description'
search_filter = "uid=example.user"


#target_dn="cn=Dummy Account,ou=MIS,OU=Departments,dc=something,dc=org"

conn = ldap.open(ldap_serv)
conn.set_option(ldap.OPT_REFERRALS,0)
conn.protocol_version = ldap.VERSION3
scope = ldap.SCOPE_SUBTREE
retrieveAttributes = None


# either sasl or simple_bind
# sasl does magic 'under the covers'? Ought to use kerberos tokens if exist.
try:
	auth_tokens = ldap.sasl.gssapi()
	conn.sasl_interactive_bind_s(username, auth_tokens)

	#swap with above if you don't use kerberos
	#conn.simple_bind_s(username, passwd)

except:
	print "bind failed"
	exit

results = conn.search_s( base_dn, scope, search_filter, retrieveAttributes)

for i in range(0,len(results)):

	#new_target_attr_val = str(random.randrange(0,1000,10))
	# note: AD pwdLastSet field is an int measured in microseconds; ~8.6e12 represents 1 day

	new_target_attr_val = "China"
	target_dn = results[i][0]
	target_dict = {}
	target_dict = results[i][1]
	try:
		print "target: " + target_dn 
		#strip [' and '] from results
		target_attr_val = str(target_dict[target_attr]).translate(None,'['']')
		#print "target attr val: " + target_attr_val
		print target_attr_val
		old = { target_attr : target_attr_val }
		new = { target_attr : new_target_attr_val }
		ldif = modlist.modifyModlist(old,new)
		# note: it appears as though the ldif always says that the orig val = none?
		print ldif
		#conn.modify_s(target_dn,ldif)	
	except:
		print "error while querying " + target_dn
	

conn.unbind_s()

# for debugging, printing results, etc.
#pp=pprint.PrettyPrinter(indent=4)
#pp.pprint(results)
#print results
