from typing import List
from dataclasses import dataclass

from parsing.node import Node
from parsing.client_backup_result import ClientBackupResult
from parsing.vmresult import VMResult

@dataclass
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
        # Flag to determine if said policy domain has any failed schedules
        self.has_non_successful_schedules = False

        # Flags to determine if policy domain has backups of each type
        self.has_vm_backups = False
        self.has_client_backups = False

        self.contact = contact
        self.name = name
        self.client_backup_summary = ClientBackupResult()
        self.vm_backup_summary = VMResult()

        if nodes is not None:
            self.nodes = nodes
        else:
            self.nodes = []
