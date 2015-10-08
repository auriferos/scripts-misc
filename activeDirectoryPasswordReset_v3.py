#!/usr/bin/python
import random
#for x in range(0,100):
#	number = random.randrange(1,180)
#	print number
import sys
import pprint
import ldap
from ldap import sasl
import ldap.modlist as modlist
import random


############################3
#
#	Todo:
#	- I should probably make ldap_conn
#


def string_to_int(string_int):
	try:
		return int(string_int.strip("'"))
	except:
		print "Could not strip single quotes"
		return

def init_dict(dict_like_object):
	new_dict = dict(dict_like_object)
	return new_dict

def expire_bitvector(bitvector):
	# userAccountControl attr is a bitvector.
	# the 'dont_expire_pw' flag maps to 65536 (x10000 in hex).
	# Let's run a bitwise '&' against fffeffff to remove that flag.
	return bitvector & 4294901759	

def remove_pw_dont_expire(ldap_conn, distinguished_name, user_attr_dict):
	target_attribute='userAccountControl'
	# by default this returns a list; we transform into a string so we can strip [''], then turn it
	# into an integer
	string_bitvector=str(user_attr_dict[target_attribute])
	int_bitvector=int(string_bitvector.translate(None,"['']"))
	new_bitvector=str(expire_bitvector(int_bitvector))
	change_attribute(ldap_conn, distinguished_name, new_bitvector, user_attr_dict, target_attribute)

def toggle_pwd_last_set(ldap_conn, distinguished_name, user_attr_dict):
	target_attribute='pwdLastSet'
	is_expired='0'
	not_expired='-1'
	change_attribute(ldap_conn, distinguished_name, is_expired, user_attr_dict, target_attribute)
	change_attribute(ldap_conn, distinguished_name, not_expired, user_attr_dict, target_attribute)

def change_attribute(ldap_conn, distinguished_name, new_attr_val, user_attribute_dictionary, target_attribute):
	curr_attr_val=user_attribute_dictionary[target_attribute]
	ldif=make_ldif(new_attr_val, curr_attr_val, target_attribute)
	ldap_conn.modify_s(distinguished_name, ldif)
	#print distinguished_name
	#print ldif

def make_ldif(new_attr_val, curr_attr_val, attr_name):
	old = { attr_name : curr_attr_val }
        new = { attr_name : new_attr_val }
	return modlist.modifyModlist(old,new)



###########################################################################
#
#				main
############################################################################

ldap_serv = "my.ldap.serv.org"
base_dn = "dc=serv,dc=org"
username = 'me'
# username accepts active directory username if AD ldap instance.
#set password if simple bind is desired (deprecated)
passwd = 'lol no such luck'

#target_dn="cn=Dummy Account,ou=MIS,OU=Departments,dc=something,dc=org"

conn = ldap.open(ldap_serv)
conn.set_option(ldap.OPT_REFERRALS,0)
conn.protocol_version = ldap.VERSION3
scope = ldap.SCOPE_SUBTREE
target_attr = 'pwdLastSet'

if len(sys.argv) != 2 :
	print 'usage: activeDirectoryPasswordReset_v3.py sAMAccountName'
	sys.exit(1)

search_filter = '(&(objectClass=User)(sAMAccountName=' + sys.argv[1]+ '))'

retrieveAttributes = None

try:
	auth_tokens = ldap.sasl.gssapi()
	conn.sasl_interactive_bind_s(username, auth_tokens)
	#if using simple bind... 
	#conn.simple_bind_s(username, passwd)
except:
	print "bind failed"
	exit

results = conn.search_s( base_dn, scope, search_filter, retrieveAttributes)
if len(results) == 0:
	print "Err: No results found for " + sys.argv[1]
	conn.unbind_s()
	sys.exit(1)

for i in range(0,len(results)):


	if len(results[i][1]) <= 10 :
		#stupidly bad pseudocheck; real users have long entries,
		# but not sure about edge cases. 
		continue
	
	target_dn = str(results[i][0])
	target_dict = init_dict(results[i][1])

	#it's important to toggle before removing the dont expire;
	# otherwise the account immediately locks out.
	toggle_pwd_last_set(conn,target_dn,target_dict)
	remove_pw_dont_expire(conn,target_dn,target_dict)

	

conn.unbind_s()

# for debugging, printing results, etc.
#pp=pprint.PrettyPrinter(indent=4)
#pp.pprint(target_dict)
#print results
