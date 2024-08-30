"""
Contains several functions to mock data from the TSM environment.
"""

from typing import List, Dict
from datetime import datetime, timedelta
from functools import reduce

from parsing.node import Node
from parsing.policy_domain import PolicyDomain
from parsing.client_backup_result import ClientBackupResult
from parsing.schedule_status import ScheduleStatus, ScheduleStatusEnum
from parsing.constants import NODE_DECOMM_STATE_NO, HISTORY_MAX_ITEMS, STATUS_COMPLETED_STR, \
    STATUS_FAILED_NO_RESTART_STR, STATUS_FAILED_STR, STATUS_FUTURE_STR, STATUS_IN_PROGRESS_STR, \
    STATUS_MISSED_STR, STATUS_PENDING_STR, STATUS_RESTARTED_STR, STATUS_SEVERED_STR, \
    STATUS_STARTED_STR, SCHED_ACT_START_TIME_DEFAULT

def format_time(offset_days = 0) -> str:
    """
    Generates a formatted time string for test server logs starting from datetime.now().
    """
    time = datetime.now() + timedelta(days=offset_days)
    return time.strftime('%Y-%m-%d %H:%M:%S')

def mock_schedule_logs_successful(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    """
    Returns schedule logs with successful schedules only.
    """
    return [
        f'{domain},{schedule},{node_name},{format_time(-3)},,,Uncertain,,',
        f'{domain},{schedule},{node_name},{format_time(-2)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-23 21:11:07,2024-08-24 05:16:46,Completed,4,The operation completed successfully, but some files were not processed.',
        f'{domain},{schedule},{node_name},{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(1)},,,{STATUS_FUTURE_STR},,'
    ]

def mock_schedule_logs_failed(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    """
    Returns schedule logs with failed schedules.
    """
    return [
        f'{domain},{schedule},{node_name},{format_time(-2)},,,Uncertain,,',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Failed,12,Backup failed with RC : str= 12.',
        f'{domain},{schedule},{node_name},{format_time(1)},,,{STATUS_FUTURE_STR},,'
    ]

def get_schedule_logs_missed(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    """
    Returns schedule logs with missed schedules.
    """
    return [
        f'{domain},{schedule},{node_name},{format_time(-2)},,,Uncertain,,',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Missed,0,Client missed schedule TEST_SCHEDULE.',
        f'{domain},{schedule},{node_name},{format_time(1)},,,{STATUS_FUTURE_STR},,'
    ]

def mock_schedule_logs_edge_cases(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    """
    Returns schedule logs with edge cases and erroneous values.
    """
    return [
        f'{domain},{schedule},{node_name},{format_time(-30)},2024-07-01 00:00:00,2024-07-01 01:00:00,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(-15)},,2024-09-30 00:00:00,,Missed,0,Client missed schedule TEST_SCHEDULE.',
        f'{domain},{schedule},{node_name},{format_time(15)},,2024-09-30 00:00:00,,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(30)},,2024-09-30 00:00:00,,{STATUS_FUTURE_STR},,',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Incomplete,3,"The operation completed but not all tasks finished."',
    ]

def mock_schedule_logs(policy_domain_name: str='DOMAIN',
                       node_name: str='NODE', schedule_name: str='SCHEDULE',
                       schedule_status: ScheduleStatusEnum=ScheduleStatusEnum.UNKNOWN) -> List[str]:
    """
    Generates mocked schedule logs with all possible schedule 
    results (see ScheduleStatusEnum for reference).
    """
    # Fill schedule log with UNKNOWN and maximum time difference
    logs: List[str] = [f'{policy_domain_name},{schedule_name},{node_name},' \
                       f'{format_time(-15)},,,Uncertain,,' for _ in range(HISTORY_MAX_ITEMS)]

    status_messages = {
        ScheduleStatusEnum.SUCCESSFUL: "All operations completed successfully.",
        ScheduleStatusEnum.MISSED: "The schedule was missed.",
        ScheduleStatusEnum.FAILED: "The schedule failed due to an internal error.",
        ScheduleStatusEnum.SEVERED: "The schedule was severed.",
        ScheduleStatusEnum.FAILED_NO_RESTART: "The schedule failed and cannot be restarted.",
        ScheduleStatusEnum.RESTARTED: "The schedule was restarted after a failure.",
        ScheduleStatusEnum.STARTED: "The schedule has started.",
        ScheduleStatusEnum.IN_PROGRESS: "The schedule is currently in progress.",
        ScheduleStatusEnum.PENDING: "The schedule is pending execution.",
        ScheduleStatusEnum.UNKNOWN: "The status of the schedule is unknown."
    }

    status_to_string = {
        ScheduleStatusEnum.SUCCESSFUL: STATUS_COMPLETED_STR,
        ScheduleStatusEnum.MISSED: STATUS_MISSED_STR,
        ScheduleStatusEnum.FAILED: STATUS_FAILED_STR,
        ScheduleStatusEnum.SEVERED: STATUS_SEVERED_STR,
        ScheduleStatusEnum.FAILED_NO_RESTART: STATUS_FAILED_NO_RESTART_STR,
        ScheduleStatusEnum.RESTARTED: STATUS_RESTARTED_STR,
        ScheduleStatusEnum.STARTED: STATUS_STARTED_STR,
        ScheduleStatusEnum.IN_PROGRESS: STATUS_IN_PROGRESS_STR,
        ScheduleStatusEnum.PENDING: STATUS_PENDING_STR,
        ScheduleStatusEnum.UNKNOWN: 'Uncertain'
    }

    # Add all possible schedule status to the schedule logs to test
    # history parsing with all schedule status.
    i = 1
    for status, message in status_messages.items():
        start_time = format_time(-i)
        end_time = '1970-01-01 00:00:00'

        log_entry = f'{policy_domain_name},' \
                    f'{schedule_name},{node_name},{start_time},,' \
                    f'{end_time},{status_to_string[status]},{0},' \
                    f'{message}'

        # Add log entries before the current and future schedules
        logs[HISTORY_MAX_ITEMS - (2 + i)] = log_entry
        i = i + 1

    # Add schedule status to be parsed as most recent (passed to this function).
    logs[HISTORY_MAX_ITEMS - 2] = f'{policy_domain_name},{schedule_name},' \
                                  f'{node_name},{format_time()},,1970-01-01 00:00:00,' \
                                  f'{status_to_string[schedule_status]},0,' \
                                  f'{status_messages[schedule_status]}'

    # Add future log.
    logs[HISTORY_MAX_ITEMS - 1] = f'{policy_domain_name},{schedule_name},{node_name},' \
                                  f'{format_time(1)},,,{STATUS_FUTURE_STR},,'

    return logs

def mock_backup_result_log(node_name: str) -> List[str]:
    """
    Returns backup result logs of a random backup result.
    """

    # TODO: Change notation (make notation configurable)
    return [
        f'{node_name},ANE4952I Total number of objects inspected:   11.765.672  (SESSION: 691911)',
        f'{node_name},ANE4954I Total number of objects backed up:        8.553  (SESSION: 691911)',
        f'{node_name},ANE4958I Total number of objects updated:          4.938  (SESSION: 691911)',
        f'{node_name},ANE4960I Total number of objects rebound:              0  (SESSION: 691911)',
        f'{node_name},ANE4957I Total number of objects deleted:              0  (SESSION: 691911)',
        f'{node_name},ANE4970I Total number of objects expired:            327  (SESSION: 691911)',
        f'{node_name},ANE4959I Total number of objects failed:               0  (SESSION: 691911)',
        f'{node_name},ANE4197I Total number of objects encrypted:            0  (SESSION: 691911)',
        f'{node_name},ANE4914I Total number of objects grew:                 0  (SESSION: 691911)',
        f'{node_name},ANE4916I Total number of retries:                     10  (SESSION: 691911)',
        f'{node_name},"ANE4977I Total number of bytes inspected:          67,87 TB  (SESSION: 691911)"',
        f'{node_name},"ANE4961I Total number of bytes transferred:       216,50 GB  (SESSION: 691911)"',
        f'{node_name},"ANE4963I Data transfer time:                    1.544,64 sec  (SESSION: 691911)"',
        f'{node_name},"ANE4966I Network data transfer rate:          146.968,08 KB/sec  (SESSION: 691911)"',
        f'{node_name},"ANE4967I Aggregate data transfer rate:         43.416,17 KB/sec  (SESSION: 691911)"',
        f'{node_name},ANE4968I Objects compressed by:                        0%   (SESSION: 691911)',
        f'{node_name},"ANE4976I Total data reduction ratio:               99,69%   (SESSION: 691911)"',
        f'{node_name},ANE4964I Elapsed processing time:               01:27:08  (SESSION: 691911)',
    ]

def mock_node_log(node_name: str="NODE", platform_name: str="Unknown Platform",
                  domain_name: str="DOMAIN", policy_domain_contact: str="",
                  node_contact: str="") -> str:
    """
    Returns a server log for provided data.
    """
    return f'{node_name},{platform_name},{domain_name},,{policy_domain_contact},{node_contact}'

def mock_schedules(schedule_names_and_status: Dict[str, ScheduleStatusEnum]) -> Dict[str, ScheduleStatus]:
    """
    Generates test schedules using the provided dictionary with name and status.
    """
    return {name: mock_schedule(name, status) for name, status in schedule_names_and_status.items()}

def mock_schedule(schedule_name: str='SCHEDULE',
                  schedule_status: ScheduleStatusEnum=ScheduleStatusEnum.UNKNOWN) -> ScheduleStatus:
    """
    Generates a test schedule including the schedules status and history.
    """
    def generate_history(schedule_status: ScheduleStatusEnum) -> List[ScheduleStatusEnum]:
        history = [ScheduleStatusEnum.UNKNOWN for _ in range(HISTORY_MAX_ITEMS)]
        schedule_history_top = HISTORY_MAX_ITEMS - 1

        # Add all schedules to schedule history to test HTML parsing of schedule history.
        i = schedule_history_top # Start from the schedule_top, offset by one
        for status in ScheduleStatusEnum:
            history[i] = status
            i = i - 1

        return history

    return_status = ScheduleStatus(
        schedule_status,
        schedule_name,
        start_time=format_time(),
        actual_start_time=SCHED_ACT_START_TIME_DEFAULT,
        end_time='1970-01-01 00:00:00',
        return_code='0'
    )

    return_status.history = generate_history(schedule_status)
    return return_status

def mock_backup_result(node_name: str='NODE') -> ClientBackupResult:
    """
    Generates a random client backup result.
    """
    cl_backup_result = ClientBackupResult(node_name)
    cl_backup_result.parse(mock_backup_result_log(node_name))
    return cl_backup_result

def mock_node_with_schedules(node_name: str='NODE', platform_name: str='Unknown Platform',
                             domain_name: str='DOMAIN', schedules: Dict[str, ScheduleStatusEnum]=None) -> Node:
    """
    Generates a node with schedules and backup results.
    """
    return Node(node_name, platform_name, domain_name, NODE_DECOMM_STATE_NO,
                backupresult=mock_backup_result(node_name),
                schedules=mock_schedules(schedules) if schedules else {})

def mock_policy_domain(domain_name: str, domain_contact: str, nodes: List[Node]) -> PolicyDomain:
    """
    Creates a mocked policy domain. 
    """
    policy_domain = PolicyDomain(nodes, domain_name, domain_contact)
    # policy_domain.client_backup_summary = sum([node.backupresult for node in policy_domain.nodes])

    backupresults = [node.backupresult for node in policy_domain.nodes]
    policy_domain.client_backup_summary += reduce(lambda s1, s2: s1 + s2, backupresults)
    return policy_domain
