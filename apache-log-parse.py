#!/usr/bin/env python3

###############################################################################
'''
Assumptions:
  We're assuming a single source log stream, not mixed logs from multiple sources,
like you see sometimes in /var/log/messages.

Using regex searchs could probably handle that, but it can be prone to false
positives if log formats are similar, plus I figured it would be slower.

I'm also assuming it's more interesting to know page stats on a per-page basis,
because thresholds for whats considered an outlier might vary greatly by page.

Limitations:
  As mentioned before, this wont handle malformed logs gracefully, nor mixed
log streams.

Its also not particularly fast- It takes 2 seconds to parse 10mb, so it would
take over 3m to parse a GB, and thats assuming linear scaling! (which it
definitely would not)


Testing:
I did my testing on a subset of this dataset, and once the full thing worked
I went about searching for some expected edge cases; The main edge I found was
handling "//", since repeated slashes have no functional purpose/difference.


'''
###############################################################################


import time
import re
import sys


class log:
    def __init__(self):
        self.first = 0
        self.last = 0
        self.errors = 0
        self.line_count = 0
        self.visitor_list = {}
        self.page_stats = {}
        self.load_times_aggregated = []
        self.total_transferred = 0
        self.four_hundreds = []
        self.five_hundreds = []

    def clean(self, string):
        # explained below, but prevents double counting, and makes substrings
        # easier to handle.
        # Originally I just replaced // with /, but i realized //// might be a
        # possibility too!
        for char in '[]"':
            string = string.replace(char, "")
        repeats = re.compile("[/]+")
        substring = repeats.findall(string)
        for s in substring:
            string = string.replace(s, "/")
        string = string.strip('\n')
        return string

    def summarize_stats(self, page):
        load_times = self.page_stats[page]['load_times']
        p_avg = int(sum(load_times) / len(load_times))
        p_min = min(load_times)
        p_max = max(load_times)
        return p_min, p_avg, p_max

    '''
    reference in case i wanted to track averages by page.
    dict[page] {max:0,min:0,visits:0,load_times:[]}
    '''

    def update_page_stats(self, url, time):
        self.load_times_aggregated.append(time)
        if url in self.page_stats.keys():
            self.page_stats[url]['visits'] += 1
            self.page_stats[url]['load_times'].append(time)
            if self.page_stats[url]['max'] < time:
                self.page_stats[url]['max'] = time
            elif self.page_stats[url]['min'] > time:
                self.page_stats[url]['min'] = time
        else:
            self.page_stats[url] = {
                "max": time,
                "min": time,
                "visits": 1,
                'load_times': [time]}

    def tabulate_errs(self, status_code):
        fives = re.compile("5[0-9]{2}")
        fours = re.compile("4[0-9]{2}")

        fours = fours.search(status_code)
        fives = fives.search(status_code)

        # re will only have a group attr if the search found something.
        # I like the look better than just appending ".group[0]" everywhere
        # Unrelated, but I keep all the status codes in case you want to drill
        # deeper.
        if hasattr(fives, "group"):
            self.errors += 1
            self.five_hundreds.append(status_code)

        elif hasattr(fours, "group"):
            self.errors += 1
            self.four_hundreds.append(status_code)

    def count_visitor(self, visitor):
        if visitor in self.visitor_list.keys():
            self.visitor_list[visitor] += 1
        else:
            self.visitor_list[visitor] = 1

    def to_epoch(self, datestring):
        epoch = time.mktime(time.strptime(datestring, '%d/%b/%Y:%H:%M:%S %z'))
        return epoch

    def to_human(self, timestamp):
        # dont want to have to mess with leap years, etc, so I'm keeping it
        # very basic (some log files are really long spanning, ok?)
        days = timestamp // (24 * 3600)
        # modulus is useful
        remainder = timestamp % (24 * 3600)

        hours = remainder // 3600
        remainder = remainder % 3600

        minutes = remainder // 60
        remainder = remainder % 60

        seconds = remainder

        formatted = "%s days, %s hours, %s minutes, %s seconds" % (
            days, hours, minutes, seconds)

        return formatted

    def most_freq_visitor(self):
        most = 0
        mvp = 'N/A'
        for visitor in self.visitor_list.keys():
            if self.visitor_list[visitor] > most:
                most = self.visitor_list[visitor]
                mvp = visitor
        return mvp

    def most_popular(self):
        # this could definitely go in the main parse loop, but eh, I like
        # splitting some stuff out for readability and simplicity.
        most = 0
        most_popular = "N/A"
        for site in self.page_stats.keys():
            if self.page_stats[site]['visits'] > most:
                most = self.page_stats[site]['visits']
                most_popular = site
        return most_popular

    def parse(self, logfile):
        for line in open(logfile):
            try:

                '''
                This serves 2 purposes; strip brackets and the like for easier
                manipulation; and replace "//" with "/", so pages get counted
                properly.
                '''
                line = self.clean(line)

                '''
                This split method is admittedly fragile, and I considered
                using regex, but decided against it, for readability mostly.
                Since this is a structured log, consuming from a single
                source, it should be enough.
                And if you're using a script to determine the origin of log
                streams instead of metadata or origin, something has probably
                gone wrong.
                '''
                all = line.split(" ")

                visitor = all[0]
                date = all[3]
                offset = all[4]
                req_method = all[5]
                req_url = all[6]
                http_protocol = all[7]
                return_code = all[8]
                size = all[9]

                '''
                Downside of the split method above; Solves edge cases caused
                by variable spaces in agent string.
                '''
                latency = int(line.split(" ")[-1:][0])

                curr = 0
                curr = self.to_epoch("%s %s" % (date, offset))

                # handle edge case of first run.
                if self.first == 0:
                    self.first = curr
                elif curr > self.last:
                    self.last = curr

                elif curr < self.first:
                    self.first = curr
                self.update_page_stats(req_url, latency)
                self.count_visitor(visitor)
                self.line_count += 1
                self.total_transferred += int(size)
                self.tabulate_errs(return_code)

            except Exception as e:
                # Alert if you hit errors;
                sys.stderr.write('ERROR: %s, exiting' % e)
                sys.exit(1)

def run_parser(log_file):
    t = log()
    results = t.parse(log_file)
    # It would by DRY'er to only use the function call, but since I use this value
    # a lot I'd rather not run it multiple times.
    MP = t.most_popular()
    MP_min, MP_avg, MP_max = t.summarize_stats(MP)
    # I cast the average to int because who cares about fractions of milliseconds?
    # (Aside from high speed traders)
    print('''
        Number of lines parsed: %s
        Duration of log file: %s

        Most requested page (MP): %s
        Most frequent visitor: %s

        Min page load time: %s (%s for MP)
        Average page load time: %s (%s for MP)
        Max page load time: %s (%s for MP)

        Number of errors: %s (400s:%s, 500s:%s)
        Total data transferred: %s
    ''' % (t.line_count,
           (t.last - t.first),
           MP,
           t.most_freq_visitor(),
           min(t.load_times_aggregated),
           MP_min,
           int((sum(t.load_times_aggregated) / len(t.load_times_aggregated))),
           MP_avg,
           max(t.load_times_aggregated),
           MP_max,
           t.errors,
           len(t.four_hundreds),
           len(t.five_hundreds),
           t.total_transferred))




if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: apache-log-parse.py ./log_file")
        sys.exit(1)
    run_parser(sys.argv[1])
