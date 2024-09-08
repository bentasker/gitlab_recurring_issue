#!/usr/bin/env python3
#
# 


import gitlab
import os
import sys


GITLAB_SERVER = os.getenv("GITLAB_SERVER", "https://gitlab.com")
TOKEN = os.getenv("GITLAB_TOKEN", False)


if TOKEN:
    gl = gitlab.Gitlab(url=GITLAB_SERVER, private_token=TOKEN)
    try:
        gl.auth()
    except Exception as e:
        print(f"Error, authentication failed: ${e}")
        sys.exit(1)
else:
    gl = gitlab.Gitlab(url=GITLAB_SERVER)
    
    

# Get a project by name and namespace
#project_name_with_namespace = "utilities/gitlab_recurring_issue"
project_name_with_namespace = "misc/test_proj"
project = gl.projects.get(project_name_with_namespace)

# Get the issues
project_issues = project.issues.list()

# Get details of the user we want to assign to
user = gl.users.list(username='btasker')[0]

print(user)

issue = project.issues.create({'title': 'I have a bug',
                               'description': 'Something useful here'
                                   })

print(issue)
issue.labels = ["Bug"]
issue.assignee_ids = [user.id]

issue.save()
print(issue)
