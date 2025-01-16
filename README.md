# TSM Mail

This repository contains the code of the TSM / ISP data parser and mail client for sending generated HTML
reports of TSM / ISP client activity.
tsm_mail.py is the main entrypoint.

## Usage

```
usage: tsm_mail.py [-h] -c PATH [-p PATH] [-e] [--disable-mail-send]

TSM Mail generates and distributes HTML reports of an IBM TSM / ISP environment.

optional arguments:
  -h, --help            show this help message and exit
  -c PATH, --config PATH
                        path to config file
  -p PATH, --pickle PATH
                        the pickle argument determines if the fetched TSM reports should be saved to file for quicker loading times while debugging.
                        NOTE: To fetch a new report, delete the pickle file or supply a different path to the argument
  -e, --export          create HTML files of generated reports
  --disable-mail-send   disable actually sending the mails for debugging purposes
```

### Node & Policy Domain EMail configuration
The email addresses used for sending out the reports can be configured in two ways:
* Inside a policy domain description field (separated by ';')
* Inside a node contact field (separated by ';')

The script determines which field to use by first checking if there are any contacts defined in the policy domain,
otherwise it will look for email addresses in the node contact fields.
So if a node is in a policy domain which has a contact defined and the node itself also has a contact defined,
the nodes contact will be omitted and the policy domains contact will be used instead.

## Config 

The mail generator is configured through a config yaml file.
Below an explanation for every config entry.

`tsm_user`: Username used to connect to TSM. (`str`) \
`tsm_password_file`: File containing the password for the TSM user. (`str`)

`mail_server_host`: SMTP host address. (`str`) \
`mail_server_port`: SMTP host port. (`int`) \
`mail_server_username`: SMTP username. A connection without authentication will be attempted if no credentials are provided.  (`str`) \
`mail_server_password`: SMTP password. (`str`)

`mail_subject_template`: String containing the mail template. Valid placeholders currently are:
 * `$status` &rarr; Status of policy domain ("OKAY" = all clients successfully completed their backups, "WARN" = there were some errors / not finished schedules)
 * `$tsm_inst` &rarr; TSM server instance of current mail report.
 * `$time` &rarr; Timestamp at time of sending mail report.
 * `$pd_name` &rarr; Name of the currently sent policy domain.

`mail_from_addr`: The sender address of mail. (`str`) \
`mail_bcc_addr`: BCC address. This attribute is optional. (`str`) \
`mail_replyto_addr`: Reply-to address. This attribute is also optional. (`str`) \
`mail_template_path`: Path to the jinja2 template used in the mails body. (`path, str`)

`log_level`: Log level as string used for logging: Valid log levels are:
 * `"DEBUG"`
 * `"ERROR"`
 * `"WARN"`
 * `"INFO"`

`log_path`: Path to log file (`path, str`) \
`log_rotate`: Flag to enable log rotation (every week) (`bool`)

`tsm_instances`: A list of strings containing configured TSM server instances to get client information from. (`List[str]`)

### Config template

```yaml
tsm_user: "MAILER"
tsm_password_file: "./pwd.txt"

mail_server_host: "mail-serv.com"
mail_server_port: 25
mail_server_username: "mailer"
mail_server_password: "password"

mail_subject_template: "ISP: $status for $tsm_inst at $time for $pd_name"
mail_from_addr: "backup@company.org"
mail_bcc_addr: "backup.rrz@uni-hamburg.de"
mail_replyto_addr: "rrz-serviceline@uni-hamburg.de"

mail_template_path: "./templates/statusmail.j2"

log_level: "ERROR"
log_path: "./tsm_mail.log"
log_rotate: true

tsm_instances:
  - "tsmsrv1"
  - "tsmsrv2"
  - "tsmsrv3"
```
