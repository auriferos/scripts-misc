import requests
import json
import os
import re
import sys
def list_contacts():
  username = ""
  acctEmail = ""
  token= os.environ['VICTOROPS_API_TOKEN']
  token_id=os.environ['VICTOROPS_API_TOKEN_ID']
  headers = {"Accept": "application/json", "X-VO-Api-Id": token_id, "X-VO-Api-Key": token}
  usersUrl = "https://api.victorops.com/api-public/v1/user"
  resp=requests.get(usersUrl, headers=headers)
  resp=resp.content
  return resp

def create_session():
  username = ""
  acctEmail = ""
  token= os.environ['VICTOROPS_API_TOKEN']
  token_id=os.environ['VICTOROPS_API_TOKEN_ID']
  headers = {"Accept": "application/json", "X-VO-Api-Id": token_id, "X-VO-Api-Key": token}
  s=requests.Session()
  s.auth = (token_id, token)
  s.headers.update(headers)
  return s

def get_emails(contact_list):
  email_list=[]
  for user in contact_list['users'][0]:
    try:
      # this ones a bit of an odd duck, so regex to the rescue
      # most users have a email pattern like "email": "email@address.com",
      # BUT: Some follow the pattern of  "email": "First Last <name@domain.com>"
      # my guess is that the latter were created by SSO, not manually.
      m = re.search(r'[\w.+-]+@[\w.+-]+', user['email'])
      email_list.append(m.group(0))

    except:
      continue
  return email_list

class VO_session():
  email_list=[]
  def __init__(self):
    resp=list_contacts()
    contacts=json.loads(resp)
    self.session=create_session()
    self.contacts=contacts

  def list_incidents(self):
    #data={"limit": 100}
    #resp=self.session.get("https://api.victorops.com/api-reporting/v2/incidents",json=data)
    resp=self.session.get("https://api.victorops.com/api-public/v1/incidents")
    if resp.status_code != 200:
      print("ERR:%s" % resp.status_code)
      return
    return resp.text

  def get_api(self,api_path,data=""):
    resp=self.session.get(f"https://api.victorops.com{api_path}",json=data)
    if resp.status_code != 200:
      print("ERR:%s" % resp.status_code)
      return
    return resp.text

  def post_api(self,api_path,data=""):
  resp=self.session.get(f"https://api.victorops.com{api_path}",json=data)
  if resp.status_code != 200:
    print("ERR:%s" % resp.status_code)
    return
  return resp.text



class victorops_contacts():
  email_list=[]
  def __init__(self):
    resp=list_contacts()
    contacts=json.loads(resp)
    self.session=create_session()
    self.email_list=get_emails(contacts)
    self.contacts=contacts

  def test():
    print(self.email_list)

  def offboard(self,target_email,replacement_email):
    target_id,target_first,target_last=self.emailToUserInfo(target_email)
    replacement_id,replacement_first,replacement_last=self.emailToUserInfo(replacement_email)
    data={"replacement": "%s" % replacement_id, "replacementStrategy": "specifiedUser" }
    resp=self.session.delete("https://api.victorops.com/api-public/v1/user/%s" % (target_id), json=data)
    if resp.status_code != 200:
      print("ERR:%s" % resp.status_code)

  def emailToUserInfo(self,email):
    for contact in self.contacts['users'][0]:
      if contact['email'] == email:
        return contact['username'],contact['firstName'],contact['lastName']



def main():
  test=VO_incidents()
  #resp=json.loads()
  #get_emails(json.loads(resp)['contacts'])
  #test=json.loads(resp)['contacts']
  #get_emails(test)
  #print(json.dumps(json.loads(resp)))
  import pprint
  pp=pprint.PrettyPrinter(indent=4)
  pp.pprint(test.list_incidents())
  pp.pprint(test.show_incident(720))


if __name__ == "__main__":
  main()
