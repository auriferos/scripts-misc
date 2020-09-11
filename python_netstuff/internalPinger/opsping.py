#!/usr/bin/python

import json 
import yaml
import multiprocessing
import datetime
import time
import signal
import sys
import requests

webhook_url="https://hooks.slack.com/services/something/Something"
statuspage_orgID='something'
statuspage_url=f"https://manage.statuspage.io/pages/{statuspage_orgID}/incidents"

def log(host_name, message, log_location):
  try:
    print message
    logfile=open(log_location,'a+')
    timestamp=datetime.datetime.now()
    full_message='{0}:{1}: {2}\n'.format(timestamp,host_name,message)
    logfile.write(full_message)
    logfile.close()
    return True
  except Exception, e:
    print e
    return False

def post_to_slack(status, host_name, status_msg='', **kwargs):
  status_endpoint=host_name+kwargs.get('path', '/')
  state_message='%s is in a %s state.' % (host_name,status)
  if status=='operational':
    emoji=':party-parrot:'
    color='good'
    state_message=" %s " % state_message + " %s " % emoji
  elif status=='partial_outage':
    emoji=':parrot-sad:'
    color='warning'
    state_message=" %s " % state_message + " %s" % emoji
  else:
    emoji=':siren:'
    state_message=" %s " % state_message + " %s " % emoji
    color='danger'
  body={"channel": "alerts-warning", \
    "display_name" : "Cowbell", \
    "username" : "Cowbell", \
    "name" : "Cowbell", \
    "icon_emoji": emoji, \
    "text": 'We detected that %s \n<%s|Visit statuspage>---<%s|Status Endpoint>\n[Sent by pingScript]' % (state_message, statuspage_url,status_endpoint),\
    "attachments": [ \
      { \
        "color": color, \
        "text": "%s" % status_msg, \
      }\
    ]\
  }
  try:
    requests.post(webhook_url, data=json.dumps(body))
    return True
  except Exception, e:
    print e
    return False

def notify(status,status_msg='',timedelta=0,**kwargs):
  # https://doers.statuspage.io/api/v1/components/
  # status can take values of operational|degraded_performance|partial_outage|major_outage
  # page_id just seems to be an account level shared value AFAIK, component_id is what *matters*

  # Gotchas:
  #
  # you'll run into fork() errors on High Sierra, see 
  # https://blog.phusion.nl/2017/10/13/why-ruby-app-servers-break-on-macos-high-sierra-and-what-can-be-done-about-it/

  
  hostname=kwargs.get('hostname')
  status_link=kwargs.get('status_link')
  page_id=kwargs.get('page_id', statuspage_orgID)
  component_id=kwargs.get('component_id')
  log_location=kwargs.get('log_location','./opsping.log')
  api_key=kwargs.get('api_key', os.environ[pingdom_api_key])
  headers={'Authorization': 'OAuth %s' % api_key}
  url='https://api.statuspage.io/v1/pages/%s/components/%s.json' % (page_id, component_id)
  data=[
    ('component[status]', status),
  ]

  if timedelta > 0:
    log('localhost', '%s changed state to %s after %s seconds' % (hostname,status,timedelta), log_location)

  post_to_slack(status, hostname,status_msg,**kwargs) 

  dryrun=True
  if dryrun:
    log('localhost', 'DRYRUN SET IN NOTIFY(); DID NOT NOTIFY ABOUT COMPONENT %s (%s) STATUS %s' % (component_id, hostname, status), log_location)
    return True

  pr=requests.patch(url, headers=headers, data=data)
  if pr.status_code != 200:
    log('localhost', 'error during POST: %s' % pr.content, log_location)
    return False
  else:
    return True



def get_response_code(addr,timeout,loop=0,**kwargs):
  # just checks http response codes
  if loop >= 10:
    return False, 'redirect loop detected! %s' % addr, 0
  # Order is important! httpconnection can't parse 'http://url.com/', and requires 'url.com'
  try:
    path=kwargs.get('path', '/')
    req=requests.get(addr+path, timeout=timeout)
    response_code=req.status_code
    if response_code == 301 or response_code == 302:
        log(addr, 'Redirect from %s to %s detected' % (addr, req.url))
        loop += 1
        success,msg=get_response_code(req.url,timeout,loop,**kwargs)
        return success,msg, response_code
    if response_code != 200:
      err = "%s returned %i" % (addr, response_code)
      return False, err, response_code
    else:
      return True, 'Returned a 200 status code.', response_code
  except Exception, e:
    #print '%s' % e
    return False, e, 0

def socket_connect(addr, port, timeout):
  # filler function for when we're checking more than http response codes
  try:
    return True, 'No error'
  except:
    return False, 'Made Up Error'


def pinger(host_name,**kwargs):
  #ID of statuspage.io component to update, defaults to ZZZ's id for testing purposes
  component_id = kwargs.get( 'component_id')
  #how often to check, in seconds
  frequency = kwargs.get('frequency', 30)
  # method for checking status
  method = kwargs.get('method', 'socket')
  # how long to wait before checking again.
  wait_on_failure = kwargs.get('wait_on_failure', 3600)
  # how long to wait
  log_location=kwargs.get('log_location', './opsping.log')
  max_retires=kwargs.get('max_retries', 3)

  case= {
    'socket' : socket_connect,
    'curl' : get_response_code
  }
  query_function = case.get(method)
  #presumed health.
  healthy=True
  t1=datetime.datetime.now()
  tries_since_good_response=0
  while True:
    try:
      good_response, err_message, response_code = query_function(host_name, **kwargs)
#      good_response, err_message = query_function(host_name, timeout, **kwargs)
      if good_response:
        tries_since_good_response=0
        if healthy == False:
          # only make API call when health status _changes_; eg, first healthy response after its been unhealthy for a while;
          # TODO: add ability to discern outage severity
          t2=datetime.datetime.now()
          delta=t2-t1
          total_s=delta.total_seconds()
          if notify('operational', err_message, total_s, **kwargs):
            healthy=True
            t1=datetime.datetime.now()
            log(host_name, 'Recovered!' , log_location)
          else:
            log(host_name, 'Failed to contact statuspage.io' , log_location)

        time.sleep(frequency)

      else: # if non-200 response code:
        tries_since_good_response += 1
        if healthy == True and tries_since_good_response > max_retires: # only make api and log calls when status has swapped
          log(host_name, err_message, log_location)
          t2=datetime.datetime.now()
          delta=t2-t1
          total_s=delta.total_seconds()
          if notify('major_outage', err_message, total_s, **kwargs):
            healthy=False #only update health status when third party successfully acknowledges
            t1=datetime.datetime.now()
            time.sleep(wait_on_failure)
            continue
          else:
            log(host_name, 'Failed to contact statuspage.io' , log_location)

        time.sleep(frequency) # if api call fails, don't wait full failure period 
         
    except Exception, e:
      log('localhost', e, log_location)
      time.sleep(wait_on_failure)
      continue
  return False

def load_hosts_file(path):
  try:
    with open(path) as stream:
      hosts=yaml.load(stream)
      return hosts
  except exception, e:
    print e
    exit(1)


def main():
  hosts=load_hosts_file('./hosts.yaml')

  # largely plagarized from here: http://stackabuse.com/parallel-processing-in-python/
  manager=multiprocessing.Manager()
  tasks = manager.Queue()
  results = manager.Queue()
  num_processes=len(hosts)
  pool=multiprocessing.Pool(processes=num_processes)

  # we'll give each host its own thread.


  for i in range(num_processes):
    process_name =(hosts[i]['hostname'])
    # args are freeform loaded from hosts file, but not all will work ...
    keywords=hosts[i]
    # think double parens are necessary to prevent python from treating str var as list?
    new_process = multiprocessing.Process(target=pinger, args=(process_name,), kwargs=keywords)
    new_process.start()

if __name__ == "__main__":
  main()


