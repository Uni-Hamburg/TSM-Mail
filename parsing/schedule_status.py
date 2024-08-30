"""
Contains ScheduleStatus class which contains all relevant information for
a TSM client schedule. The status itself is coded in the ScheduleStatusEnum,
also defined here.
The schedule status data is parsed using the ScheduleStatusParser,
which is defined here aswell.
"""

import logging
from datetime import datetime
from enum import Enum, auto
from typing import List, Dict

from parsing.constants import SCHED_RETURN_CODE_DEFAULT, SCHED_ACT_START_TIME_DEFAULT, \
    SCHED_END_TIME_DEFAULT, HISTORY_MAX_ITEMS, STATUS_COMPLETED_STR, STATUS_MISSED_STR, \
    STATUS_FAILED_STR, STATUS_FAILED_NO_RESTART_STR, STATUS_SEVERED_STR, STATUS_IN_PROGRESS_STR, \
    STATUS_FUTURE_STR, STATUS_RESTARTED_STR, STATUS_PENDING_STR, STATUS_STARTED_STR, LINE_DELIM, \
    COLUMN_QE_SCHED_NAME, COLUMN_QE_STATUS, COLUMN_QE_RESULT, COLUMN_QE_SCHED_START, \
    COLUMN_QE_SCHED_ACT_START, COLUMN_QE_TIME_COMPLETED

logger = logging.getLogger("main")

class ScheduleStatusEnum(Enum):
    """
    ScheduleStatusEnum describes the three stats of a schedule
    """
    SUCCESSFUL = auto()
    MISSED = auto()
    FAILED = auto()
    SEVERED = auto()
    FAILED_NO_RESTART = auto()
    RESTARTED = auto()
    STARTED = auto()
    IN_PROGRESS = auto()
    PENDING = auto()
    UNKNOWN = auto()

class ScheduleStatus:
    """
    ScheduleStatus contains information about a client schedule.

    Args:
        status:             The status of the schedule.
        schedule_name:      Name of the schedule.
        return_code:        Return code of the most recent result of schedule.
        actual_start_time:  The actual start time of the schedule.
        end_time:           The end time of the schedule.
    """
    def __init__(self, status: ScheduleStatusEnum = ScheduleStatusEnum.UNKNOWN,
                 schedule_name: str = "", return_code: str = SCHED_RETURN_CODE_DEFAULT,
                 start_time: str = "",
                 actual_start_time: str = SCHED_ACT_START_TIME_DEFAULT,
                 end_time: str = SCHED_END_TIME_DEFAULT):
        self.status: ScheduleStatusEnum = status
        self.schedule_name = schedule_name
        self.return_code = return_code
        self.start_time = start_time
        self.actual_start_time = actual_start_time
        self.end_time = end_time

        # Initialize history with "UNKNOWN" status
        self.history: List[ScheduleStatusEnum] = \
            [ScheduleStatusEnum.UNKNOWN for _ in range(HISTORY_MAX_ITEMS)]

    def __eq__(self, other: 'ScheduleStatus') -> bool:
        return self.status == other.status and \
               self.schedule_name == other.schedule_name and \
               self.return_code == other.return_code and \
               self.start_time == other.start_time and \
               self.actual_start_time == other.actual_start_time and \
               self.end_time == other.end_time

class SchedulesParser:
    """
    SchedulesParser parses and collects schedule data from all schedules provided in logs.
    """

    def __init__(self):

        # Mapping of the schedule status string returned from TSM
        # to the enum type ScheduleStatusEnum
        self.__schedule_status = {
            STATUS_COMPLETED_STR: ScheduleStatusEnum.SUCCESSFUL,
            STATUS_MISSED_STR: ScheduleStatusEnum.MISSED,
            STATUS_FAILED_STR: ScheduleStatusEnum.FAILED,
            STATUS_SEVERED_STR: ScheduleStatusEnum.SEVERED,
            STATUS_FAILED_NO_RESTART_STR: ScheduleStatusEnum.FAILED_NO_RESTART,
            STATUS_RESTARTED_STR: ScheduleStatusEnum.RESTARTED,
            STATUS_STARTED_STR: ScheduleStatusEnum.STARTED,
            STATUS_IN_PROGRESS_STR: ScheduleStatusEnum.IN_PROGRESS,
            STATUS_PENDING_STR: ScheduleStatusEnum.PENDING
        }

    # Remove schedules which are older than 24 hours
    def __remove_old_schedules(self, scheds: Dict[str, ScheduleStatus]) -> Dict[str, ScheduleStatusEnum]:
        new_scheds: Dict[str, ScheduleStatus] = {}

        for sched_name, schedule in scheds.items():
            current_date = datetime.now()
            sched_date = datetime.strptime(schedule.start_time, '%Y-%m-%d %H:%M:%S')
            date_diff = current_date - sched_date

            if (date_diff.total_seconds() / 3600) < 24:
                new_scheds[sched_name] = schedule

        return new_scheds

    def __get_line_status_str(self, line: str):
        return line.split(LINE_DELIM)[COLUMN_QE_STATUS].strip()

    def parse(self, server_log: List[str]) -> Dict[str, ScheduleStatus]:
        """
        Parse client schedules from the server logs.
        """
        scheds: Dict[str, ScheduleStatus] = {}

        # Remove "Future" schedule from list as it is
        # not relevant for this usecase
        server_log = list(filter(lambda line: self.__get_line_status_str(line) != STATUS_FUTURE_STR, server_log))

        for _, line in enumerate(server_log):
            line_split = line.split(LINE_DELIM)

            # Create empty Schedule Status Data object if not created already
            if line_split[COLUMN_QE_SCHED_NAME] not in scheds:
                scheds[line_split[COLUMN_QE_SCHED_NAME]] = ScheduleStatus()

            sched_stat = scheds[line_split[COLUMN_QE_SCHED_NAME]]
            if line_split[COLUMN_QE_STATUS] in self.__schedule_status:
                sched_stat.status = self.__schedule_status[line_split[COLUMN_QE_STATUS]]
            else:
                sched_stat.status = ScheduleStatusEnum.UNKNOWN

            if len(line_split[COLUMN_QE_SCHED_NAME]) > 0:
                sched_stat.schedule_name = line_split[COLUMN_QE_SCHED_NAME]

            if len(line_split[COLUMN_QE_RESULT]) > 0:
                sched_stat.return_code = line_split[COLUMN_QE_RESULT]
            else:
                sched_stat.return_code = SCHED_RETURN_CODE_DEFAULT

            if len(line_split[COLUMN_QE_SCHED_START]) > 0:
                sched_stat.start_time = line_split[COLUMN_QE_SCHED_START]

            if len(line_split[COLUMN_QE_SCHED_ACT_START]) > 0:
                sched_stat.actual_start_time = line_split[COLUMN_QE_SCHED_ACT_START]
            else:
                sched_stat.actual_start_time = SCHED_ACT_START_TIME_DEFAULT

            if len(line_split[COLUMN_QE_TIME_COMPLETED]) > 0:
                sched_stat.end_time = line_split[COLUMN_QE_TIME_COMPLETED]
            else:
                sched_stat.end_time = SCHED_END_TIME_DEFAULT

            # Check if schedule exists in dict and add schedule line to history
            if sched_stat.schedule_name in scheds:
                if sched_stat.start_time:
                    sched_start_date = datetime.strptime(sched_stat.start_time, '%Y-%m-%d %H:%M:%S')
                    current_date = datetime.now()

                    # Calculate position in 15 day history list
                    date_diff = current_date - sched_start_date

                    # Check if date_diff is within 15 days of current_date.
                    # History is set to be maximum 15 days.
                    if date_diff.days <= 15 and date_diff.days > 0:
                        scheds[sched_stat.schedule_name].history[
                            HISTORY_MAX_ITEMS - date_diff.days] = sched_stat.status

        return self.__remove_old_schedules(scheds)
