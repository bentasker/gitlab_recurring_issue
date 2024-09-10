#!/usr/bin/env python3
#
# Process a configuration file providing ticket templates and schedules
# then, if necessary, raise tickets in Gitlab projects
#
#
'''
Copyright (c) 2024 B Tasker

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import gitlab
import os
import sys
import yaml

from datetime import datetime as dt
from datetime import date
from datetime import timedelta

def loadConfig(cfg_file):
    with open(cfg_file, 'r') as f:
        cfg = yaml.safe_load(f)

    # TODO: populate defaults
    return cfg


def createTicket(ticket):
    ''' Create a Gitlab ticket based on a provided dict
    '''
    
    if "title" not in ticket or "description" not in ticket:
        print("Error, title and description must be provided")
        return False
    
    
    # Get a project by name and namespace
    if "project" not in ticket or len(ticket['project']) < 1:
        print(f"Error, Project not provided for: {ticket['title']}")
        return False
    
    project = gl.projects.get(ticket['project'])

    labels = CFG['labels'] if "labels" in CFG else []
    if "labels" in ticket:
        labels = labels + ticket["labels"]


    if DRY_RUN:
        return dry_run_print(ticket, labels)

    # Create the ticket
    issue = project.issues.create({
            'title': ticket['title'],
            'description': ticket['description']
        })

    issue.labels = list(set(labels))

    if "assignee" in ticket and len(ticket['assignee']) > 0:
        # Get details of the user we want to assign to
        user = gl.users.list(username=ticket['assignee'])[0]
        if user:
            issue.assignee_ids = [user.id]            

    # Save any changes
    issue.save()
    print(f"Created issue {issue.iid} in project {ticket['project']}: {ticket['title']}")
    

def dry_run_print(ticket, labels):
    ''' Print out details of the ticket that we would have created
    '''
    
    print((
        "----\n"
        f'project: {ticket["project"]}\n'
        f'title: {ticket["title"]}\n'
        f'labels: {labels}\n'
        f'description: {ticket["description"]} \n'
        ))
    
    
def shouldRun(ticket, date_matches):
    ''' Take a ticket dict and a dict of the current date 
    in order to evaluate the ticket's schedule and identify
    whether it should run
    '''
    
    if "schedule" not in ticket:
        print("Error: ticket has no schedule")
        return False
    
    sched = ticket["schedule"]
    
    if "every" in ticket["schedule"]:
        every = sched["every"].lower()
        every_list = [every]
        
        if "/" in every:
            every_list = every.split("/")
        
        for e in every_list:
            # Check whether we match an every rule
            if e == "run":
                return True
            # Day of week
            elif e in date_matches["dayw_list"]:
                return True
    
    # We didn't match an every, so check for explicit date matches
    if "day" in sched:
        day = str(sched["day"]).lower()
        month = str(sched["month"]).lower() if "month" in sched else "*"
        
        day_list = [day]
        if "/" in day:
            day_list = day.split("/")
        
        # Check whether multiple months have been provided
        month_list = [month]
        if "/" in month:
            # Multiple months have been provided
            month_list = month.split("/")
        
        for d in day_list:
            for m in month_list:        
                if d == date_matches["DoM"] and m in date_matches["month_list"]:
                        return True
    
    if "nth" in sched:
        if "weekday" not in sched["nth"] or "n" not in sched["nth"]:
            print("Error: nth requires both n and weekday")
            return False
        
        # Turn the weekday value into an integer
        dow = WEEK.index(sched["nth"]["weekday"].lower())
        
        # Calculate the first instance of that weekday
        n1 = first_dow(int(date_matches["Y"]), int(date_matches["M"]), dow)

        # Now we need to advance that to match `n`. Currently we already have the value
        # for n = 1, so subtract 1 from n and then multiply by 7 days
        days = (int(sched["nth"]["n"]) - 1) * 7
        
        target_date = n1 + timedelta(days=days)
        
        if date_matches["datestr"] == target_date.strftime("%Y-%m-%d"):
            #print(f'It is the {sched["nth"]["n"]}th {sched["nth"]["weekday"]}') 
            return True
    
    # We didn't match anything
    return False
        

def first_dow(year, month, dow):
    ''' Calculate the date of the first x-day of the month
    where x is in the range 0 (mon) - 6 (sun)
    '''
    
    # Do we need to convert a name to an integer?
    if not isinstance(dow, int):
        dow = WEEK.index(dow.lower())

    # Get the date of the 1st day of that month
    d1 = dt(year, month, 1)
    
    # Work out what day the 1st fell on
    # and subtract that from the requested day 
    # i.e. if the 1st was a tues and we requested 
    # Weds we'll subtract 1 from 2
    off = dow - d1.weekday()
    
    # Check if the offset went negative
    if off < 0:
        # It did - so the first day of the 
        # month occurred later in the week than 
        # the requested day
        # bump forward a week
        off += 7
        
    # Add the offset to the start of the month
    d2 = d1 + timedelta(off)
    return d2


GITLAB_SERVER = os.getenv("GITLAB_SERVER", "https://gitlab.com")
TOKEN = os.getenv("GITLAB_TOKEN", False)
CONFIG_FILE = os.getenv("CONFIG_FILE", "/config.yml")
DRY_RUN = (os.getenv("DRY_RUN", "false").lower() == "true")
CFG = loadConfig(CONFIG_FILE)
WEEK = ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]

if DRY_RUN:
    print("\n".join(["Dry Run Mode","==============",""]))

if "gitlab" in CFG:
    if "url" in CFG["gitlab"]:
        GITLAB_SERVER = CFG["gitlab"]["url"]
    if "token" in CFG["gitlab"]:
        TOKEN_SERVER = CFG["gitlab"]["token"]

if TOKEN:
    gl = gitlab.Gitlab(url=GITLAB_SERVER, private_token=TOKEN)
    try:
        gl.auth()
    except Exception as e:
        print(f"Error, authentication failed: {e}")
        sys.exit(1)
else:
    gl = gitlab.Gitlab(url=GITLAB_SERVER)
    
    

if "tickets" not in CFG:
    print("Error, no ticket templates provided")
    sys.exit(1)
    


# Build time constraints for this run
now = dt.now()


date_matches = {
    "datestr" : now.strftime("%Y-%m-%d"),
    "Y" : now.strftime("%Y"),
    "M" : now.strftime("%m"),
    "DoW" : now.strftime("%a").lower(),
    "DoWd" : WEEK.index(now.strftime("%a").lower()), # 0 mon - 6 sun
    "DoM" : now.strftime("%-d"),
    "dayw_list" : [
        now.strftime("%a").lower(),
        WEEK.index(now.strftime("%a").lower())
        ],
    "month_list" : [
        now.strftime("%-m"), 
        now.strftime("%b").lower(),
        "*"
        ]
    }

if DRY_RUN:
    print(f"Calculated Dates: {date_matches}\n")

for ticket in CFG["tickets"]:
    if "active" in ticket and not ticket["active"]:
        # It's disabled, skip
        continue
    
    try:
        if shouldRun(ticket, date_matches):
            createTicket(ticket)
        else:
            # Temporary: we won't print routinely
            print(f"Skipping {ticket}")
    except Exception as e:
        print(f"Error creating ticket: {e} ({ticket})")

