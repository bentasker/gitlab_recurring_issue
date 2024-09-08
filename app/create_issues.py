#!/usr/bin/env python3
#
# 

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

    # Create the ticket
    issue = project.issues.create({
            'title': ticket['title'],
            'description': ticket['description']
        })

    issue.labels = ticket['labels'] if "labels" in ticket else []

    if "assignee" in ticket and len(ticket['assignee']) > 0:
        # Get details of the user we want to assign to
        user = gl.users.list(username=ticket['assignee'])[0]
        if user:
            issue.assignee_ids = [user.id]            

    # Save any changes
    issue.save()
    print(f"Created issue {issue.iid} in project {ticket['project']}: {ticket['title']}")
    
    
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
    ''' Derived from a Stackoverflow answer: https://stackoverflow.com/a/71688384
    Credit@ Molomy
    '''
    day = ((8 + dow) - date(year, month, 1).weekday()) % 7
    return date(year, month, day)



GITLAB_SERVER = os.getenv("GITLAB_SERVER", "https://gitlab.com")
TOKEN = os.getenv("GITLAB_TOKEN", False)
CONFIG_FILE = os.getenv("CONFIG_FILE", "/config.yml")
CFG = loadConfig(CONFIG_FILE)
WEEK = ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]

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
    
if "gitlab" in CFG:
    if "url" in CFG["gitlab"]:
        GITLAB_SERVER = CFG["gitlab"]["url"]
    if "token" in CFG["gitlab"]:
        TOKEN_SERVER = CFG["gitlab"]["token"]
    
        


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
        print(f"Error creating ticket: {e}")

