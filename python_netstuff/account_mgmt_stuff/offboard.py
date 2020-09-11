#!/usr/bin/env python3

import sys
import pdb
import p3_ldapsearch
from statuspage_scripts import statuspage_contacts
from sumologic_scripts import sumologic_contacts
from victorops_scripts import victorops_contacts
from honeybadger_scripts import honeybadger_contacts
import yaml

# 512 is 'active'; and we only want users with associated email addresses.
inactiveActiveDirectoryUsers=p3_ldapsearch.search('(&(!(userAccountControl=512))(mail=*))')
WL_path="./whitelist"


inactive_user_emails=[]
things_to_be_alarmed_about=[]
user_details={}

statuspage_emails=statuspage_contacts()
sumologic_emails=sumologic_contacts()
victorops_emails=victorops_contacts()
honeybadger_emails=honeybadger_contacts()

def load_yaml_file(path):
  try:
    with open(path) as stream:
      yaml_stuff=yaml.load(stream, Loader=yaml.FullLoader)
      return yaml_stuff
  except Exception as e:
    print(e)
    exit(1)


for user in inactiveActiveDirectoryUsers.entries:
  try:
    inactive_user_emails.append(user.mail)
    mail=str(user.mail)
    #ldapsearches take a second, and user entries can be hundreds long, so unless
    # you want to wait 10m, find managers of a more refined list.

    user_details[mail] = {'manager': str(user.manager)}

  except Exception as e:
    #print(e)
    continue

for user in statuspage_emails.email_list:
  try:
    if user in user_details.keys():
      things_to_be_alarmed_about.append({"statuspage": {user:user_details[user]}})
  except:
    continue
#Not redundant- this ones for *subs*
for subscriber in statuspage_emails.subscribers:
  try:
    if 'email' in subscriber.keys():
      if str(subscriber['email']) in user_details.keys():
        print("%s is a subscriber, change that here: https://manage.statuspage.io/pages/9ybvtwjysk33/notifications" % subscriber['email'])
  except Exception as e:
    #pdb.set_trace()
    print('+++')
    print('some weird issue with %s: %s' % (subscriber['email'],e))
    print(subscriber)
    print('+++')


for user in sumologic_emails.email_list:
  try:
    if user in user_details.keys():
      #managerEmail=p3_ldapsearch.managerDnToEmail(user_details[user]['manager'])
      #breakpoint()
      things_to_be_alarmed_about.append({"sumologic": {user:user_details[user]}})
  except:
    continue

for user in honeybadger_emails.email_list:
  try:
    if user in user_details.keys():
      things_to_be_alarmed_about.append({"honeybadger": {user:user_details[user]}})
  except:
    continue

for user in victorops_emails.email_list:
  try:
    if user in user_details.keys():
      things_to_be_alarmed_about.append({"victorops": {user:user_details[user]}})
  except:
    continue

'''
ldapsearches are time expensive;
because a second search must be run to find the manger email, we try to minimize the number of those lookups.
That's why I'm running sequential loops here.
'''

#inactiveActiveDirectoryUsers
if len(things_to_be_alarmed_about) > 0:
  for concerning_thing in things_to_be_alarmed_about:
    tool=next(iter(concerning_thing))
    user=next(iter(concerning_thing[tool]))
    mgmt=concerning_thing[tool][user]['manager']
    managerEmail=p3_ldapsearch.managerDnToEmail(mgmt)

    whitelist=load_yaml_file(WL_path)
    if user in [whitelist[i]['useremail'] for i in range(len(whitelist))]:
      continue

    approval=input("%s: Delete or deactivate %s? [n]" % (tool,user))
    if approval != "yes":
      continue

    if tool=="sumologic":
      if managerEmail not in sumologic_emails.email_list:
        print("Could not reassign %s to %s (manager has no email in sumologic), deactivated instead." % (user,managerEmail))
        sumologic_emails.deactivate(user)
      else:
        replacement=input("Assign content to user: [%s]" % managerEmail)
        if replacement=="":
          replacement=managerEmail
        print('"deleting" user %s, assigning to %s' % (user,managerEmail))
        sumologic_emails.offboard(user, replacement)

    if tool=="victorops":
      if managerEmail not in victorops_emails.email_list:
        print("Could not reassign %s to %s (manager has no email in sumologic)." % (user,managerEmail))
        while True:
          #an annoying check, but we want an escape hatch in case of an endless loop.
          check=input("%s: Skip deletion of %s? [n]" % (tool,user))
          if check != "n":
            replacement=input("Assign to which email?")
            if replacement not in victorops_emails.email_list:
              print("Could not reassign %s to %s (%s has no email in sumologic)." % (user,replacement,replacement))
            else:
              print('Deleting user %s, assigning to %s' % (user,replacement))
              victorops_emails.offboard(user, replacement)
              break
          else:
            break


      else:
        check=input("%s: Skip deletion of %s? [n]" % (tool,user))
        if check != "yes":
          print('Deleting user %s, assigning to %s' % (user,managerEmail))
          victorops_emails.offboard(user, managerEmail)

    if tool=="statuspage":
      statuspage_emails.offboard(user)
      statuspage_emails.checkForSubscriptions(user)

    if tool=="honeybadger":
      # i know its bad semantic coupling, but the honeybadger has its own logic
      # loop since it has to iterate over multiple teams, which is why we dont
      # double check here.
      honeybadger_emails.offboard(user)



    #print("%s manager: %s" % (concerning_thing.keys()[0], concerning_thing))
else:
  print("Wow, things are clean! (Or broken!) I found no accounts to be concerned about.")

