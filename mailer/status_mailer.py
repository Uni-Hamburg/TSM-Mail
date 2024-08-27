"""
status_mailer.py generates status mails from node and policy domain data
"""

import logging
import smtplib
import os
from email.message  import EmailMessage
from jinja2 import Environment, FileSystemLoader

from parsing.policy_domain import PolicyDomain
from parsing.schedule_status import ScheduleStatusEnum

logger = logging.getLogger("main")

class StatusMailer:
    """
    StatusMailer sends mails containing status information to registered nodes.

    Args:
        smtp_host:      The mailer host to connect to
        smtp_port:      Mailer host port
        template_path:  Path to jinja2 template for mail body
    """

    def __init__(self, smtp_host: str, smtp_port: int, template_path: str):
        self.__smtp_host = smtp_host
        self.__smtp_port = smtp_port

        # Load jinja2 mail HTML template
        self.__template_file_loader = FileSystemLoader(os.path.dirname(template_path))
        self.__template_env = Environment(loader=self.__template_file_loader,
                                          extensions=['jinja2.ext.do'])

        self.__template = self.__template_env.get_template(os.path.basename(template_path))
        self.__template.globals["ScheduleStatusEnum"] = ScheduleStatusEnum

        logger.debug("Connecting to %s at port %s...", self.__smtp_host, self.__smtp_port)
        # Establish connection to the SMTP server
        self.__smtp_conn = smtplib.SMTP(self.__smtp_host, self.__smtp_port)
        self.__smtp_conn.starttls()

    def send_to(self, policy_domain: PolicyDomain, sender_addr: str, receiver_addr: str,
                subject: str, replyto_addr: str, bcc_addr: str):
        """
        Renders the mail template and sends it using the smtp library.
        """
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender_addr
        message["To"] = receiver_addr

        if replyto_addr:
            message["Reply-to"] = replyto_addr
        else:
            logger.info("No Reply-to configured. Skipping.")

        if bcc_addr:
            message["Bcc"] = bcc_addr
        else:
            logger.info("No Bcc configured. Skipping.")

        # Render HTML template of message containing node data from TSM nodes
        message_html = self.__template.render(pd=policy_domain)

        message.add_header('Content-Type', 'text/html')
        message.add_header('X-Auto-Response-Suppress', 'All')
        message.set_payload(message_html)

        logger.info("Sending report for %s to %s.", policy_domain.name, receiver_addr)
        self.__smtp_conn.send_message(message)
