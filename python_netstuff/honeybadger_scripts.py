#!/usr/bin/env python3
import requests
import json
import os
import sys
import pprint


def list_contacts():
  username = ""
  acctEmail = ""
  token= os.environ['HONEYBADGER_API_TOKEN']
  headers = {"Authorization": "Bearer %s" % token , 'Account-Email': acctEmail}
  usersUrl = "https://app.honeybadger.io/v2/teams"
  resp=requests.get(usersUrl, auth=(token,""), headers=headers)
  resp=resp.content
  return resp

def create_session():
  username = ""
  acctEmail = ""
  token= os.environ['HONEYBADGER_API_TOKEN']
  headers = {"Authorization": "Bearer %s" % token , 'Account-Email': acctEmail}
  s=requests.Session()
  s.auth=(token,"")
  s.headers.update(headers)
  return s


def getMembers(team):
  username = ""
  acctEmail = ""
  token= os.environ['HONEYBADGER_API_TOKEN']
  headers = {"Authorization": "Bearer %s" % token , 'Account-Email': acctEmail}
  usersUrl = "https://app.honeybadger.io/v2/teams/%s" % team
  resp=requests.get(usersUrl, auth=(token,""), headers=headers)
  resp=resp.content
  list=json.loads(resp)
  memberList=list['members']
  return memberList



def get_emails(contact_list,active_only=False):
  email_list=[]
  if contact_list['next'] is not None:
    print("Warning: could not retrieve all results. This script doesnt handle pagination yet.")
    sys.exit(1)
  for contact in contact_list['data']:
    try:
      if active_only:
        if contact['isActive']:
          email_list.append(contact['email'])
        else:
          continue
      else:
        email_list.append(contact['email'])
    except:
      continue
  return email_list


class honeybadger_contacts():
  email_list=[]
  def __init__(self):
    resp=list_contacts()
    self.contacts=json.loads(resp)
    self.session=create_session()
    self.email_list=self.list_emails()

  def check_member(self,target_email):
    resp=self.contacts
    teams=resp['results']
    results={}
    for team in teams:
      teamName=team['name']
      teamId=team['id']
      memberlist=getMembers(teamId)
      found,memberID=iterMember(memberlist,target_email)
      if found:
        results.update({memberID:{'teamId':teamId, 'teamName': teamName}})
        print('Found %s (%s) in team %s (%s)' % (target_email,memberID,teamName,teamId))
      else:
        print('%s not found in %s' % (target_email,teamName))
    print(results)
    return results


  def list_emails(self):
    resp=self.contacts
    teams=resp['results']
    finalList=[]
    for team in teams:
      teamId=team['id']
      memberlist=getMembers(teamId)
      finalList=compileMembersEmails(memberlist,finalList)
    return finalList


  def offboard(self,target_email):
    project_list=self.check_member(target_email)
    for uid in project_list.keys():
      teamId=project_list[uid]['teamId']
      teamName=project_list[uid]['teamName']
      try:
        print('curl -u AUTH_TOKEN: -X DELETE https://app.honeybadger.io/v2/teams/%s/team_members/%s' % (teamId,uid))
        check=input("want to delete %s [%s] in team %s [%s]?" % (target_email,uid,project_list[uid]['teamName'],project_list[uid]['teamId']))
        if check == "yes":
          resp=self.session.delete("https://app.honeybadger.io/v2/teams/%s/team_members/%s" % (teamId,uid))
          # 204 NO CONTENT
          # The server has successfully fulfilled the request and that there is 
          # no additional content to send in the response payload body.
          if resp.status_code != 204:
            print("Err: %s" % resp.status_code)
            raise
      except Exception as e:
        print(e)


def compileMembersEmails(memberlist,aux_list):
  for member in memberlist:
    if member['email'] not in aux_list:
      aux_list.append(member['email'])
  return aux_list

def iterMember(memberlist,target_email):
  for member in memberlist:
    if member['email'] == target_email:
      return True, member['id']
  return False, None

def deleteMemberFromTeam(memberID,teamID):
  print('todo')



def main():
  resp=list_contacts()
  resp=json.loads(resp)
  #print(json.dumps(json.loads(resp)))
  teams=resp['results']
  pp=pprint.PrettyPrinter(indent=2)
  #pp.pprint(teams[0])
  for team in teams:
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    teamName=team['name']
    teamId=team['id']
    memberlist=getMembers(teamId)
    found,memberID=iterMember(memberlist)
    if found:
      print('Found %s (%s) in team %s (%s)' % (memberID,teamName,teamId))
    else:
      print('% not found in %s' % (target_email,teamName))

if __name__ == "__main__":
  main()
