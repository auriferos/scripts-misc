import requests
import json
import os

yourOrgId="fizzbuzz"

def list_contacts():
  token= os.environ['STATUSPAGE_API_TOKEN']
  headers = {"Authorization": "OAuth %s" % token }
  usersUrl = f"https://api.statuspage.io/v1/organizations/{yourOrgId}/users.json"
  resp=requests.get(usersUrl, headers=headers)
  resp=resp.content
  return resp

def create_session():
  token= os.environ['STATUSPAGE_API_TOKEN']
  headers = {"Authorization": "OAuth %s" % token }
  s=requests.Session()
  s.headers.update(headers)
  return s


def create_session():
  token= os.environ['STATUSPAGE_API_TOKEN']
  headers = {"Authorization": "OAuth %s" % token }
  s=requests.Session()
  s.headers.update(headers)
  return s

def get_emails(contact_list):
  email_list=[]
  for contact in contact_list:
    try:
      email_list.append(contact['email'])
    except:
      continue
  return email_list

class statuspage_contacts():
  email_list=[]
  def __init__(self):
    resp=list_contacts()
    contacts=json.loads(resp)
    self.email_list=get_emails(contacts)
    self.session=create_session()
    self.contacts=contacts
    self.session=create_session()
    self.subscribers=self.get_subscribers()

  def get_subscribers(self):
    subs=self.session.get(f"https://api.statuspage.io/v1/pages/{yourOrgId}/subscribers.json")
    return json.loads(subs.content)

  def test():
    print(self.email_list)

  def offboard(self,target_email):
    target_id,target_first,target_last,organization=self.emailToUserInfo(target_email)
    resp=self.session.delete(f"https://api.statuspage.io/v1/organizations/{organization}/users/{target_id}")
    if resp.status_code != 200:
      print("ERR:%s" % resp.status_code)

  def emailToUserInfo(self,email):
    for contact in self.contacts:
      if contact['email'] == email:
        return contact['id'],contact['first_name'],contact['last_name'],contact['organization_id']

  def checkForSubscriptions(self,email):
    for subscriber in self.subscribers:
      if subscriber['email'] == email:
        print(f"{email} is a subscriber, change that here: https://manage.statuspage.io/pages/{yourOrgId}/notifications")

  def unsub_all(self,subscriber):
    print('todo')

def main():
  resp=list_contacts()
  print(json.dumps(json.loads(resp)))

if __name__ == "__main__":
  main()
