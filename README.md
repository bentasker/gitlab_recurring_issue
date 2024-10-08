# Gitlab Recurring Issue Creation

A small cronjob to periodically raise pre-defined Gitlab tickets.

The aim of this script is to fill [a gap](https://gitlab.com/gitlab-org/gitlab/-/issues/15981) in Gitlab's capabilities, by periodically raising tickets for recurring tasks.

Project management can be found [in my Gitlab mirror](https://projects.bentasker.co.uk/gils_projects/project/utilities/gitlab_recurring_issue.html).

---

### Pre-Requisites

You will need to create a [Personal Access Token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html) for the script to use when creating issues.

The user associated with the token should be added to relevant projects with `Developer` privileges (without this, it'll be able to create issues but won't be able to add labels or assign the issue).


---

### Auth Configuration

You will need to provide your Gitlab URL (if not `gitlab.com`) and personal access token. This can be done in the YAML config file or via environment variable (if you're running on Kubernetes, the latter is preferred as it allows the token to be stored in a secret).

```sh
GITLAB_SERVER="https://gitlab.example.com"
GITLAB_TOKEN="<my token>"
```

If you wish to provide via YAML instead, add the following to your config file
```yaml
gitlab:
  url: "https://gitlab.example.com" 
  token: "<my token>"
```

---

## Tickets Configuration

Ticket templates consist of a few items

* Title to use (mandatory)
* Description to use (mandatory)
* Project and namespace to create within (mandatory)
* Schedule (mandatory, see below)
* Labels to apply (optional)
* Issue assignee (optional)

They should be placed under the `tickets` attribute in the config file


### Schedule

Tickets are created when a run aligns with the constraints provided within the `schedule` attribute.

There are a number of supported scheduling methodologies, but scheduling is currently entirely stateless, so it's not possible to specify "every n days"

---

#### Day & Month

It's possible to schedule a ticket to be created on a specific day of a month (using a short name or a month number):
```yaml
schedule:
  day: 4
  month: Sep
```

It's also possible to provide multiple days and/or months by seperating values with a forward slash
```yaml
schedule:
  day: 4/9/15/22
  month: Sep
```

or to run on the 2nd of February, March and September:
```yaml
schedule:
  day: 4
  month: 2/mar/Sep
```

---

#### Every scheduling

An `every` schedule can be used to simply provide a weekday
```yaml
schedule:
  every: Sat
```

Note: you can also provide an integer, where 0 is Monday and 6 is Sunday.

The `every` attribute also accepts the value `run` - if this is present, the ticket will be raised every time the script is invoked.

---

#### `n`th Day Scheduling

The script support `n`th day scheduling.

For example, to specify that a ticket should be raised on the 2nd Sunday of each month:
```yaml
schedule:
  nth:
    n: 2
    weekday: Sun
```

---

### Configuration Example

An example configuration might look like this
```yaml
gitlab:
  url: https://gitlab.example.com
tickets:
   - title: "Cook Roast Dinner"
     active: true
     project: home/HOME
     schedule:
       nth:
        n: 2
        weekday: Sun
     description: "It's roast dinner sunday"
     assignee: btasker
     labels: ["task", "food"]
   - title: "File Tax Return"
     active: true
     due_in_days: 30
     project: home/finances
     schedule:
       day: 1
       month: Sep
     description: "File return for the last financial year"
     assignee: btasker
     labels: ["task", "finances"]
   - title: "Check tyre pressures"
     active: true
     project: home/vehicles
     schedule:
       every: Sunday
     description: "Check car type pressures"
     assignee: btasker
     labels: ["task", "car"]
```

The `due_in_days` attribute is optional, but when present is used to calculate the issue due date. The value is the number of days from the date the ticket is raised.

---

### Description Files

Although ticket descriptions can be set in YAML (via `description`), it may sometimes be desirable to provide descriptions that don't fit well into YAML.

The system is able to read descriptions from a file defined in `description_file` (if set, this will override `description`). 

Files should be stored in the template directory (the location of this is set in env var `TEMPLATE_DIR`, which defaults to `/templates`) and **must** have the suffix `.template`.

For example to use `/templates/test.template` to populate a ticket description:

```yaml
   - title: "Check tyre pressures"
     active: true
     project: home/vehicles
     schedule:
       every: Sunday
     description_file: test.template
     assignee: btasker
     labels: ["task", "car"]
```


---

### Invocation

The script is intended to be run from within a container:
```
docker run --rm \
-e GITLAB_TOKEN="<my token>" \
-e GITLAB_SERVER="https://gitlab.example.com" \
-v $PWD/examples/example_config.yml:/config.yml \
ghcr.io/bentasker/gitlab_recurring_issue:0.1
```

Note: if the config needs to be mounted elsewhere, the location can be provided in env var `CONFIG_FILE`

The environment variable `DRY_RUN` can be used to run without writing into Gitlab - this will simply print details for tickets who's schedule matches the run time.

The environment variable `FORCE` can be used to ignore schedule information: when set to `true` all configured tickets will be raised (or, output if `DRY_RUN` is also active).

---

### Run Scheduling

The script doesn't provide a means for running itself - you'll need to use `cron` or `CronJob` to invoke it once a day.

Within this repo, there's an [example Kubernetes CronJob definition](examples/kubernetes.yml).


Because the script is stateless, it doesn't know when you last ran it, so if you run it more than once a day you'll likely get duplicate tickets.


---

## License

Copyright (c) 2024 B Tasker
Released under [MIT License](https://www.bentasker.co.uk/pages/licenses/mit-license.html)





