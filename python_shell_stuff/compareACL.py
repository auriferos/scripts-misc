#!/usr/bin/python
import os
import subprocess
import re

# Check if a set of ACL's is homogeneous (parents dont differ from children)

def mismatch(parent_acl, child_acl):
	set1=set(parent_acl.splitlines())
	set2=set(child_acl.splitlines())
	remove_pattern=re.compile("# file: .*")	

	set1, parent_dir=remove_from_set( parent_acl, set1, remove_pattern)
	set2, child_dir=remove_from_set( child_acl, set2, remove_pattern)

	if set1 != set2 :
		print "Parent Dir:"
		print parent_dir
		print "Parent ACL:" 
		print "    " + str(set.difference(set1,set2))
		print "Sub Dir:"
		print child_dir 
		print "Child ACL:"
		print "    " + str(set.difference(set2,set1))
		print ""

def remove_from_set( mylist, myset, mypattern):
	for line in mylist.splitlines():
		if mypattern.search(line):
			myset.remove(line)
			badline=line
	return myset, badline

def rACLCheck(currDir, parent_acl):
# recursively check if parent_acl equals subdir_acls
	curr_acl=subprocess.check_output(["getfacl", currDir ])
	for listing in os.listdir(currDir):
		listing_abs = os.path.join(currDir, listing)
		if os.path.isdir(listing_abs):
			try:
				rACLCheck(listing_abs,curr_acl)
			except:
				print "Error: Could not run rACLCheck against " + listing_abs
		#mismatch(curr_acl,parent_acl)
		mismatch(parent_acl,curr_acl)

		
# lingering questions: symlinks a problem?
# eliminate annoying getfacl error messages?

	
topACL=subprocess.check_output(["getfacl", "./"])
top=os.getcwd()
rACLCheck(top, topACL)
