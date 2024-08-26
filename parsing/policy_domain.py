"""
Contains PolicyDomain class which contains all relevant information to a TSM policy domain.
"""

from typing import List

from parsing.node import Node
from parsing.client_backup_result import ClientBackupResult
from parsing.vmresult import VMResult

class PolicyDomain:
    """
    PolicyDomain class contains all associated nodes and a flag
    to determine if there have been failed schedules in the last 24 hours.

    Args:
        nodes:      List of nodes associated with PolicyDomain
        name:       Name of policy domain
        contact:    Contact mail for PolicyDomain
    """
    def __init__(self, nodes: List[Node] = None, name: str = "", contact: str = ""):
        self.contact = contact
        self.name = name
        self.client_backup_summary = ClientBackupResult()
        self.vm_backup_summary = VMResult()

        if nodes is not None:
            self.nodes = nodes
        else:
            self.nodes = []

    def has_client_schedules(self) -> bool:
        """
        Checks if any node in this PolicyDomain has any attempted / completed backup
        schedules.
        """
        return any(node.has_client_schedules() for node in self.nodes)

    def has_non_successful_schedules(self) -> bool:
        """
        Checks if any node in this PolicyDomain has any non successful backup schedules.
        """
        return any(node.has_non_successful_schedules() for node in self.nodes)

    def has_vm_backups(self) -> bool:
        """
        Checks if any node has any VMWare backup results.
        """
        return any(node.has_vm_backups() for node in self.nodes)
