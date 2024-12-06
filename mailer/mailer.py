"""
Mailer defines the interface a mailing client has to implement.
"""

from typing import Protocol
from parsing.policy_domain import PolicyDomain


class Mailer(Protocol):
    def send_to(
        self,
        policy_domain: PolicyDomain,
        sender_addr: str,
        receiver_addr: str,
        subject: str,
        replyto_addr: str,
        bcc_addr: str,
    ): ...
