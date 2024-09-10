FROM registry.gitlab.com/python-gitlab/python-gitlab:alpine

LABEL "org.opencontainers.image.source" "https://github.com/bentasker/gitlab_recurring_issue"

RUN mkdir /templates
COPY app /app


# TODO: change
ENTRYPOINT []
CMD ["/app/create_issues.py"]
