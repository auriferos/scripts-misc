#!/usr/bin/env python3

import time
import re
import sys


class log:

  def __init__(self):
    self.first=0
    self.last=0
    self.errors=0
    self.line_count=0
    self.visitor_list={}
    self.page_stats={}
    self.load_times_aggregated=[]
    self.total_transferred=0
    self.four_hundreds=[]
    self.five_hundreds=[]

  def clean(self,string):
    for char in '[]"':
      string=string.replace(char, "")
    string=string.replace("//","/")
    string=string.strip('\n')
    return string

  '''
    dict[page] {max:0,min:0,visits:0}
  '''

  def update_page_stats(self,url,time):
    self.load_times_aggregated.append(time)
    if url in self.page_stats.keys():
      self.page_stats[url]['visits'] +=1
      self.page_stats[url]['load_times'].append(time)
      if self.page_stats[url]['max'] < time:
        self.page_stats[url]['max'] = time
      elif self.page_stats[url]['min'] > time:
        self.page_stats[url]['min'] = time
    else:
      self.page_stats[url]={"max":time, "min":time, "visits": 1, 'load_times':[time]}


  def tabulate_errs(self,status_code):
    #err_regex=re.compile("[45][0-9]{2}")
    #err=err_regex.search(status_code)
    #if hasattr(err, "group"):
    #  self.errors += 1
    fives=re.compile("5[0-9]{2}")
    fours=re.compile("4[0-9]{2}")

    fours=fours.search(status_code)
    fives=fives.search(status_code)

    if hasattr(fives, "group"):
      self.errors += 1
      self.five_hundreds.append(status_code)

    elif hasattr(fours, "group"):
      self.errors += 1
      self.four_hundreds.append(status_code)


  def increment_page_count(url):
    if url not in page_visits.keys():
      page_visits[url] = 1
    else:
      page_visits[url] += 1


  def count_visitor(self,visitor):
    if visitor in self.visitor_list.keys():
      self.visitor_list[visitor] += 1
    else:
      self.visitor_list[visitor] = 1

  def count_transferred(self,bytes):
    self.total_transferred += int(bytes)

  def to_epoch(self,datestring):
    # check if zero padded
    epoch=time.mktime(time.strptime(datestring, '%d/%b/%Y:%H:%M:%S %z'))
    return epoch

  def to_human(self, timestamp):
    # dont want to have to mess with leap years, etc.
    days = timestamp // (24*3600)
    # modulus is useful
    remainder = timestamp % (24*3600)

    hours = remainder // 3600
    remainder = remainder % 3600

    minutes = remainder // 60
    remainder = remainder % 60

    seconds = remainder

    formatted="%s days, %s hours, %s minutes, %s seconds" % (days, hours, minutes, seconds)

    return formatted

  def calc_duration(self):
    total_time=self.last-self.first
    duration=self.to_human(total_time)
    return duration

  def show_errors(self):
    return str(self.errors)

  def show_transferred(self):
    return "%s bytes" % self.total_transferred

  def most_freq_visitor(self):
    most=0
    mvp='N/A'
    for visitor in self.visitor_list.keys():
      if self.visitor_list[visitor] > most:
        most=self.visitor_list[visitor]
        mvp=visitor
    return mvp

  def most_popular(self):
    most=0
    most_popular="N/A"
    for site in self.page_stats.keys():
      if self.page_stats[site]['visits'] > most:
        most=self.page_stats[site]['visits']
        most_popular=site
    return most_popular

  def parse(self,logfile):
    for line in open(logfile):
      try:
        line=self.clean(line)
        all=line.split(" ")
  
        # strip weird chars from strings for easier manipulation.
        cleaned=list(map(lambda x: self.clean(x), all))
  
        #instead of doing this split assignment, I considered using regex; Still regex is prone to false positives. Since this is a structured log, and we're assuming its a single stream, this should be enough.
        visitor=cleaned[0]
        date=cleaned[3]
        offset=cleaned[4]
        req_method=cleaned[5]
        req_url=cleaned[6]
        http_protocol=cleaned[7]
        return_code=cleaned[8]
        size=cleaned[9]
        # problem case caused by variable spaces in agent
        latency=int(line.split(" ")[-1:][0])
  
        #increment_page_count(req_url)
  
        #remember to reset counters on loops
        curr=0
        curr=self.to_epoch("%s %s" % (date, offset)) 
  
        if self.first == 0:
          self.first = curr
  
        elif curr > self.last:
          self.last=curr
  
        elif curr < self.first:
          self.first=curr
        self.update_page_stats(req_url,latency)
        self.count_visitor(visitor)
        self.line_count +=1
        self.count_transferred(size)
        self.tabulate_errs(return_code)

      except Exception as e:
        print(e)


t=log()
results=t.parse(sys.argv[1])
print('''
    Number of lines parsed: %s
    Duration of log file: %s

    Most requested page: %s
    Most frequent visitor: %s

    Min page load time: %s
    Average page load time: %s
    Max page load time: %s

    Number of errors: %s (400s:%s, 500s:%s)
    Total data transferred: %s
'''% (t.line_count,t.calc_duration(),t.most_popular(), t.most_freq_visitor(), min(t.load_times_aggregated), (sum(t.load_times_aggregated)/len(t.load_times_aggregated)), max(t.load_times_aggregated), t.show_errors(),len(t.four_hundreds),len(t.five_hundreds), t.show_transferred()) )


