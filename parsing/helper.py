"""
Globally used helper functions are defind here.
"""

from parsing.policy_domain import PolicyDomain
from parsing.node import Node
from parsing.schedule_status import ScheduleStatusEnum

# Check if node has any non-successful schedules
def check_non_successful_schedules(policy_domain: PolicyDomain, node: Node) -> bool:
    """
    Check if policy domain contains any non-successful backup runs.
    """
    if policy_domain.has_non_successful_schedules:
        return True

    for sched_stat in node.schedules.values():
        if sched_stat.status != ScheduleStatusEnum.SUCCESSFUL:
            return True
    return False
