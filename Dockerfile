FROM registry.gitlab.com/python-gitlab/python-gitlab:alpine

COPY app /app


# TODO: change
ENTRYPOINT []
CMD ["/app/create_issues.py"]
