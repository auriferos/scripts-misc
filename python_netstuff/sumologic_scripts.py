import requests
import json
import os
import sys

def list_contacts():
  username = ""
  acctEmail = ""
  token_id= os.environ['SUMOLOGIC_API_KEY_ID']
  token= os.environ['SUMOLOGIC_API_KEY']
  headers = {"Authorization": "Bearer %s" % token , 'Account-Email': acctEmail, 'Content-type': 'application/json'}
  usersUrl = "https://api.sumologic.com/api/v1/users?limit=500"
  resp=requests.get(usersUrl, auth=(token_id, token), headers=headers)
  resp=resp.content
  return resp

def create_session():
  acctEmail = ""
  token_id= os.environ['SUMOLOGIC_API_KEY_ID']
  token= os.environ['SUMOLOGIC_API_KEY']
  headers = {"Authorization": "Bearer %s" % token , 'Account-Email': acctEmail, "Content-Type": "application/json"}
  s=requests.Session()
  s.auth = (token_id, token)
  s.headers.update(headers)
  return s



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


class sumologic_contacts():
  email_list=[]
  def __init__(self):
    resp=list_contacts()
    contacts=json.loads(resp)
    self.contacts=contacts
    self.email_list=get_emails(contacts,True)
    self.session=create_session()
    self.test()

  def test(self):
    self.session=create_session()
    resp=self.session.get("https://api.sumologic.com/api/v1/users?limit=500")

  def deactivate(self,target_email):
    user_id,firstName,lastName=self.emailToUserInfo(target_email)
    #magic strings suck, but 0000000000BC4065 is the 'deactivated' roleId
    data={"firstName": firstName, "lastName": lastName, "isActive": 'false', "roleIds": ['0000000000BC4065']}
    resp=self.session.put("https://api.sumologic.com/api/v1/users/%s" % user_id, json=data)
    #breakpoint()
    print("data:%s" % data)
    if resp.status_code != 200:
      print("ERR:%s" % resp.status_code)

  def offboard(self,target_email,replacement_email):
    target_id,target_first,target_last=self.emailToUserInfo(target_email)
    replacement_id,replacement_first,replacement_last=self.emailToUserInfo(replacement_email)
    data={"transferTo": replacement_id}
    print("data:%s" % data)
    resp=self.session.delete("https://api.sumologic.com/api/v1/users/%s" % (target_id), data=data)
    if resp.status_code != 200:
      print("ERR:%s" % resp.status_code)

  def emailToUserInfo(self,email):
    for contact in self.contacts['data']:
      if contact['email'] == email:
        return contact['id'],contact['firstName'],contact['lastName']

def main():
  resp=list_contacts()
  print(json.dumps(json.loads(resp)))

if __name__ == "__main__":
  main()
