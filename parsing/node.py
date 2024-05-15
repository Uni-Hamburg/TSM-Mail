from typing import Dict
from dataclasses import dataclass

from parsing.client_backup_result import ClientBackupResult
from parsing.constants import NODE_DECOMM_STATE_YES
from parsing.schedule_status import ScheduleStatus

@dataclass
class Node:
    """
    Node class represents all data collected from TSM regarding nodes, such as
    the associated policy domain of the now, the platform, the schedule status
    and the most recent backup results.

    Args:
        name:               Name of the node
        platform:           Platform name of the node (e.g. WinNT, Linux, etc.)
        policy_domain_name: Name of the associated policy domain of node
        decomm_state:       Decomissioning state of node ("YES" or "")
        contact:            E-Mail address of contact person of said node (if none is supplied
                            the mail contact of the policy domain is used).
        schedules:          The status of the last schedules from within 24 hours
                            and a 15 day history of schedule stats.
        backupresult:       A ClientBackupResult item containing results from the most recent
                            backup.
        vm_results:         VM backup schedule results associated with this node
    """
    def __init__(self, name: str, platform: str, policy_domain_name: str, decomm_state: str,
                 contact: str = "", schedules: Dict[str, ScheduleStatus] = None,
                 backupresult: 'ClientBackupResult' = None, vm_results: 'VMResult' = None):
        self.name = name
        self.policy_domain_name = policy_domain_name
        self.platform = platform

        if backupresult is not None:
            self.backupresult = backupresult
        else:
            self.backupresult = ClientBackupResult()

        if decomm_state.strip() == NODE_DECOMM_STATE_YES:
            self.decomm_state = True
        else:
            self.decomm_state = False

        if vm_results is not None:
            self.vm_results = vm_results
        else:
            self.vm_results = []

        self.contact = contact
        self.schedules = schedules
