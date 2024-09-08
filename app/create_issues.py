#!/usr/bin/env python3
#
# 

import gitlab
import os
import sys
import yaml

from datetime import datetime as dt

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
        # Check whether we match an every rule
        if every == "run":
            return True
        # Day of week
        elif every in [date_matches["DoW"], date_matches["DoWd"]]:
            return True
    
    # We didn't match an every, so check for explicit date matches
    if "day" in sched:
        day = str(sched["day"]).lower()
        month = str(sched["month"]).lower() if "month" in sched else "*"
        
        # Check whether multiple months have been provided
        month_list = [month]
        if "/" in month:
            # Multiple months have been provided
            month_list = month.split("/")
            
        for m in month_list:        
            if day == date_matches["DoM"] and m in date_matches["month_list"]:
                    return True
    
    # We didn't match anything
    return False
        

GITLAB_SERVER = os.getenv("GITLAB_SERVER", "https://gitlab.com")
TOKEN = os.getenv("GITLAB_TOKEN", False)
CONFIG_FILE = os.getenv("CONFIG_FILE", "/config.yml")
CFG = loadConfig(CONFIG_FILE)


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
    "DoW" : now.strftime("%a").lower(),
    "DoWd" : now.strftime("%w"), # 0 Sun - 6 Sat
    "DoM" : now.strftime("%-d"),
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

