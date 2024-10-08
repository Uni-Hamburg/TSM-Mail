"""
status_mailer.py generates status mails from node and policy domain data
"""

import logging
import smtplib
from smtplib import SMTPException
from email.message import EmailMessage

from parsing.policy_domain import PolicyDomain
from parsing.report_template import ReportTemplate

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
        self.__smtp_conn = None

        # Load jinja2 mail HTML template
        self.__template = ReportTemplate(template_path)

    def __smtp_connected(self) -> bool:
        """
        Checks if the smtp connection is still connected or not.
        """
        if not self.__smtp_conn:
            return False

        try:
            status = self.__smtp_conn.noop()[0]
        except SMTPException:
            status = -1
        return status == 250

    def send_to(self, policy_domain: PolicyDomain, sender_addr: str, receiver_addr: str,
                subject: str, replyto_addr: str, bcc_addr: str):
        """
        Renders the mail template and sends it using the smtp library.
        """
        # Establish connection to the SMTP server if it is not established / timed out
        if not self.__smtp_conn or not self.__smtp_connected():
            logger.info("Connecting to %s at port %s...", self.__smtp_host, self.__smtp_port)
            self.__smtp_conn = smtplib.SMTP(self.__smtp_host, self.__smtp_port)
            self.__smtp_conn.starttls()

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
        message_html = self.__template.render(policy_domain)

        message.add_header('Content-Type', 'text/html')
        message.add_header('X-Auto-Response-Suppress', 'All')
        message.set_payload(message_html)

        logger.info("Sending report for %s to %s.", policy_domain.name, receiver_addr)
        self.__smtp_conn.send_message(message)
