"""
Contains PolicyDomain class which contains all relevant information to a TSM policy domain.
"""

from functools import reduce

from parsing.node import Node
from parsing.client_backup_result import ClientBackupResult
from parsing.vmresult import VMResult


class PolicyDomain:
    """
    PolicyDomain class contains all associated nodes and a flag
    to determine if there have been failed schedules in the last 24 hours.

    Args:
        nodes:      list of nodes associated with PolicyDomain
        name:       Name of policy domain
        contact:    Contact mail for PolicyDomain
    """

    def __init__(
        self, nodes: list[Node] | None = None, name: str = "", contact: str = ""
    ):
        self.contact = contact
        self.name = name
        self.client_backup_summary = ClientBackupResult()
        self.vm_backup_summary = VMResult()

        if nodes:
            self.nodes = nodes
            self.calculate_backup_summaries()
        else:
            self.nodes = []

    def calculate_backup_summaries(self):
        """
        Calculates all backup summaries for policy domain.
        """
        if self.nodes:
            backupresults = [node.backupresult for node in self.nodes]
            self.client_backup_summary = reduce(lambda s1, s2: s1 + s2, backupresults)

            vm_backup_results = []
            for node in self.nodes:
                vm_backup_results.extend(node.vm_results)

            if vm_backup_results:
                self.vm_backup_summary = reduce(
                    lambda s1, s2: s1 + s2, vm_backup_results
                )

            # Reset node name in client_backup_summary
            # (summary doesn't have a node_name)
            self.client_backup_summary.node_name = ""

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

    def __eq__(self, other) -> bool:
        return (
            self.contact == other.contact
            and self.name == other.name
            and self.client_backup_summary == other.client_backup_summary
            and self.vm_backup_summary == other.vm_backup_summary
            and self.nodes == other.nodes
        )
