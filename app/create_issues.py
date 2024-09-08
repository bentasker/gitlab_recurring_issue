#!/usr/bin/env python3
#
# 


import gitlab
import os
import sys
import yaml


def loadConfig(cfg_file):
    with open(cfg_file, 'r') as f:
        cfg = yaml.safe_load(f)

    # TODO: populate defaults
    return cfg


def createTicket(ticket):
    ''' Create a Gitlab ticket based on a provided dict
    '''
    
    # Get a project by name and namespace
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
    print(issue)
    

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
    
    
for ticket in CFG["tickets"]:
    if "active" in ticket and not ticket["active"]:
        # It's disabled, skip
        continue
    
    try:
        createTicket(ticket)
    except Exception as e:
        print(f"Error creating ticket: {e}")

