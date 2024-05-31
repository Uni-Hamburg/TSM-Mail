"""
Contains defined constants used for parsing TSM data
"""

# Log level strings
LOG_LEVEL_ERROR_STR = "ERROR"
LOG_LEVEL_WARN_STR = "WARN"
LOG_LEVEL_INFO_STR = "INFO"
LOG_LEVEL_DEBUG_STR = "DEBUG"

# Number contants
HISTORY_MAX_ITEMS = 15

# Delimiters
# dsmadmc line delimiter
LINE_DELIM = ","

# Session number delimiter
SESSION_NUM_DELIM = "("

# Query column numbers for .split() Operations
# Activity log
COLUMN_DATE_TIME = 0
COLUMN_SEVERITY = 1
COLUMN_MESSAGE = 2

# Event Queries (QUERY EVENT)
COLUMN_QE_PD_NAME = 0
COLUMN_QE_SCHED_NAME = 1
COLUMN_QE_NODE_NAME = 2
COLUMN_QE_SCHED_START = 3
COLUMN_QE_SCHED_ACT_START = 4
COLUMN_QE_TIME_COMPLETED = 5
COLUMN_QE_STATUS = 6
COLUMN_QE_RESULT = 7
COLUMN_QE_REASON = 8

# Nodes
COLUMN_NODE_NAME = 0
COLUMN_PLATFORM_NAME = 1
COLUMN_PD_NAME = 2
COLUMN_DECOMM_STATE = 3

COLUMN_DOMAIN_CONTACT = 4
COLUMN_NODE_CONTACT = 5

# VM backup constants
COLUMN_VM_SCHED_NAME = 0
COLUMN_VM_NAME = 1
COLUMN_VM_START_TIME = 2
COLUMN_VM_END_TIME = 3
COLUMN_VM_SUCCESS = 4
COLUMN_VM_ACTIVITY = 5
COLUMN_VM_ACT_TYPE = 6
COLUMN_VM_BYTES = 7
COLUMN_VM_ENTITY = 8

# Default strings for nodes
NODE_DECOMM_STATE_YES = "YES"
NODE_DECOMM_STATE_NO = ""

# Default strings for schedules
SCHED_RETURN_CODE_DEFAULT = "None"
SCHED_ACT_START_TIME_DEFAULT = "Not started"
SCHED_END_TIME_DEFAULT = " "

# Status strings
STATUS_COMPLETED_STR = "Completed"
STATUS_MISSED_STR = "Missed"
STATUS_FAILED_STR = "Failed"
STATUS_SEVERED_STR = "Severed"
STATUS_FAILED_NO_RESTART_STR = "Failed - no restart"
STATUS_RESTARTED_STR = "Restarted"
STATUS_STARTED_STR = "Started"
STATUS_IN_PROGRESS_STR = "In Progress"
STATUS_PENDING_STR = "Pending"
STATUS_FUTURE_STR = "Future"

# String definitions for parsing data from server queries.
NODE_NAME_STR = "Node:"

# Find strings for TDP MSSQL in activity logs
TDP_MSSQL_STR = "TDP MSSQL"

# Find strings for activity logs
INSPECTED_STR = "objects inspected:"
BACKED_UP_STR = "objects backed up:"
UPDATED_STR = "objects updated:"
EXPIRED_STR = "objects expired:"
FAILED_STR = "objects failed:"
RETRIES_STR = "retries:"
BYTES_INSPECTED_STR = "bytes inspected:"
BYTES_TRANSFERRED_STR = "bytes transferred:"
AGGREGATE_DATA_RATE_STR = "Aggregate data transfer rate:"
PROCESSING_TIME_STR = "processing time:"

# Find strings for missed / failed schedules
SCHED_NAME_STR = "Schedule "
SCHED_SUCCESS_STR = "completed successfully"
SCHED_MISSED_STR = "has missed its"
SCHED_FAILED_STR = "failed"
SCHED_FAILED_RET_CODE_STR = "return code"
