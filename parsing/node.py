"""
Contains the Node class which holds all relevant information for a TSM node.
"""

from typing import Dict, List

from parsing.client_backup_result import ClientBackupResult
from parsing.constants import NODE_DECOMM_STATE_YES
from parsing.schedule_status import ScheduleStatus, ScheduleStatusEnum

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
                 backupresult: 'ClientBackupResult' = None, vm_results: List['VMResult'] = None):
        self.name = name
        self.policy_domain_name = policy_domain_name
        self.platform = platform

        if backupresult is not None:
            self.backupresult = backupresult
        else:
            self.backupresult = ClientBackupResult(name)

        if decomm_state.strip() == NODE_DECOMM_STATE_YES:
            self.decomm_state = True
        else:
            self.decomm_state = False

        if vm_results is not None:
            self.vm_results = vm_results
        else:
            self.vm_results = []

        self.contact = contact

        if schedules:
            self.schedules = schedules
        else:
            self.schedules = {}

    def has_client_schedules(self) -> bool:
        """
        Checks if node has any attempted / completed schedules.
        """
        if not self.schedules:
            return False

        if any(sched_stat.status != ScheduleStatusEnum.UNKNOWN \
           for sched_stat in self.schedules.values()):
            return True
        return False

    def has_non_successful_schedules(self) -> bool:
        """
        Checks if node has any non successful schedules.
        """
        if not self.schedules:
            return False

        if any(sched_stat.status != ScheduleStatusEnum.SUCCESSFUL \
           for sched_stat in self.schedules.values()):
            return True
        return False

    def has_vm_backups(self) -> bool:
        """
        Checks if node has any VMWare backup results.
        """
        if len(self.vm_results) > 0:
            return True
        return False

    def __eq__(self, other: 'Node') -> bool:
        return self.name == other.name and \
               self.policy_domain_name == other.policy_domain_name and \
               self.platform == other.platform and \
               self.backupresult == other.backupresult and \
               self.decomm_state == other.decomm_state and \
               self.vm_results == other.vm_results and \
               self.contact == other.contact and \
               self.schedules == other.schedules
