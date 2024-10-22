"""
Contains the ClientBackupResult class which contains the data of a
TSM client backup (e.g. bytes inspected, bytes transferred, processing time, etc.).
"""

import logging
from datetime import datetime
from typing import List

import tabulate

from parsing.constants import SESSION_NUM_DELIM, TDP_MSSQL_STR, \
    INSPECTED_STR, BACKED_UP_STR, UPDATED_STR, EXPIRED_STR, FAILED_STR, RETRIES_STR, \
    BYTES_INSPECTED_STR, BYTES_TRANSFERRED_STR, AGGREGATE_DATA_RATE_STR, PROCESSING_TIME_STR

logger = logging.getLogger("main")

class ClientBackupResult:
    """
    ClientBackupResult parses backup results from activity log and holds
    the parsed data.
    """
    def __init__(self, node_name: str=""):
        self.inspected = 0
        self.backed_up = 0
        self.updated = 0
        self.expired = 0
        self.failed = 0
        self.retries = 0

        self.bytes_inspected = 0
        self.bytes_inspected_unit = "GB"

        self.bytes_transferred = 0
        self.bytes_transferred_unit = "GB"

        self.aggregate_data_rate = 0
        self.aggregate_data_rate_unit = "MB"

        self.processing_time = 0

        self.node_name = node_name

    def __parse_size(self, size: str) -> float:
        # Parse memory sizes to bytes as int
        units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}

        number, unit = [string.strip() for string in size.split()]
        return float(number) * units[unit]

    def __parse_elapsed_time(self, line: str) -> int:
        # Parse the elapsed time of backup schedule
        # (format is 00:00:00 instead of elapsed seconds total)
        # into seconds as int
        line_strip = line.strip()
        line_split = line_strip.split(":")
        line_hours = int(line_split[0])
        line_excess_hours = 0
        time = None

        # If elapsed hours > 23h, save excess hours and readd later.
        # Parsing past 24h (e.g. 26:00:00) is not possible using strptime.
        if line_hours > 23:
            line_excess_hours = line_hours - 23
            time = datetime.strptime(f"23:{line_split[1]}:{line_split[2]}", "%H:%M:%S")
        else:
            time = datetime.strptime(line_strip, "%H:%M:%S")

        # Parse elapsed time
        return (time.hour + line_excess_hours) * 3600 + time.minute * 60 + time.second

    def __format_elapsed_time(self, time: int) -> str:
        minutes, seconds = divmod(time, 60)
        hours, minutes = divmod(minutes, 60)

        # Return timestamp with two digit numbers
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def __parse_line(self, line: str, search_str: str) -> float:
        # Parse data from supplied log line

        # Search for search string and return value after search string
        line_split = line.split(search_str, 1)[1]

        return self.__parse_item_float(line_split)

    def __parse_item_float(self, line: str) -> float:
        # Remove all whitespace
        line_strip = line.strip()

        # Split to remove session number and remove dots from number
        line_num = line_strip.split(SESSION_NUM_DELIM)[0].replace(".", "")

        # Convert from US to EU notation
        line_num = line_num.replace(',', '.')

        # Default value for line
        num = 0.0

        # Check if current line contains a size (B, KB, MB, GB, TB)
        if "B" in line_num:
            # Replace "," with "." (german notation)
            # and remove "/sec" if data rate is provided
            line_num = line_num.replace(",", ".").strip().removesuffix("/sec")
            num = self.__parse_size(line_num)
        # Check if line contains timestamp
        elif ":" in line_num:
            num = self.__parse_elapsed_time(line_num)
        # Else output integer directly
        else:
            num = line_num

        # Return parsed number
        return float(num)

    def __convert_notation(self, num_string: str) -> str:
        # Convert from US notation to EU notation
        return num_string.replace('.', 'x').replace(',', '.').replace('x', ',')

    def __format_num_str(self, num: float, precision: int = 2) -> str:
        if precision == 0:
            num_format = format(int(num), ",d")
        else:
            num_format = format(num, f",.{precision}f")
        return self.__convert_notation(num_format)

    def __parse_size_string(self, size_bytes: float, size_suffix: str, data_rate: bool = False,
                            remove_suffix: bool = False, precision: int = 2) -> str:
        # Parses bytes as float to a size string, e.g. "300 MB/sec".
        units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}

        size = format(size_bytes / units[size_suffix], f",.{precision}f")
        size = self.__convert_notation(size)

        if remove_suffix:
            return size

        return f"{size} {size_suffix}{'/sec' if data_rate else ''}"

    def parse(self, client_log: List[str]):
        """
        Parse data from the client backup log.
        """

        # Check if client log is empty
        if not client_log:
            logger.info("Provided client is log empty.")
            return

        for item in client_log:
            # TODO: Implement TDP MSSQL parsing for client results.
            if TDP_MSSQL_STR in item:
                continue

            if INSPECTED_STR in item:
                self.inspected = self.__parse_line(item, INSPECTED_STR)
            if BACKED_UP_STR in item:
                self.backed_up = self.__parse_line(item, BACKED_UP_STR)
            if UPDATED_STR in item:
                self.updated = self.__parse_line(item, UPDATED_STR)
            if EXPIRED_STR in item:
                self.expired = self.__parse_line(item, EXPIRED_STR)
            if FAILED_STR in item:
                self.failed = self.__parse_line(item, FAILED_STR)
            if RETRIES_STR in item:
                self.retries = self.__parse_line(item, RETRIES_STR)
            if BYTES_INSPECTED_STR in item:
                self.bytes_inspected = self.__parse_line(item, BYTES_INSPECTED_STR)
            if BYTES_TRANSFERRED_STR in item:
                self.bytes_transferred = self.__parse_line(item, BYTES_TRANSFERRED_STR)
            if AGGREGATE_DATA_RATE_STR in item:
                self.aggregate_data_rate = self.__parse_line(item, AGGREGATE_DATA_RATE_STR)
            if PROCESSING_TIME_STR in item:
                self.processing_time = self.__parse_line(item, PROCESSING_TIME_STR)

    def inspected_str(self):
        """
        Returns a formatted string for "inspected".
        """
        return self.__format_num_str(self.inspected, precision=0)

    def backed_up_str(self):
        """
        Returns a formatted string for "backed_up".
        """
        return self.__format_num_str(self.backed_up, precision=0)

    def updated_str(self):
        """
        Returns a formatted string for "updated".
        """
        return self.__format_num_str(self.updated, precision=0)

    def expired_str(self):
        """
        Returns a formatted string for "expired".
        """
        return self.__format_num_str(self.expired, precision=0)

    def failed_str(self):
        """
        Returns a formatted string for "failed".
        """
        return self.__format_num_str(self.failed, precision=0)

    def retries_str(self):
        """
        Returns a formatted string for "retries".
        """
        return self.__format_num_str(self.retries, precision=0)

    def bytes_inspected_str(self):
        """
        Returns a formatted string for "bytes_inspected".
        """
        return self.__parse_size_string(
            self.bytes_inspected, self.bytes_inspected_unit, remove_suffix=True)

    def bytes_transferred_str(self):
        """
        Returns a formatted string for "bytes_transferred".
        """
        return self.__parse_size_string(
            self.bytes_transferred, self.bytes_transferred_unit, remove_suffix=True)

    def aggregate_data_rate_str(self):
        """
        Returns a formatted string for "aggregate_data_rate".
        """
        return self.__parse_size_string(
            self.aggregate_data_rate, self.aggregate_data_rate_unit,
            remove_suffix=True, data_rate=True)

    def processing_time_str(self):
        """
        Returns a formatted string for "processing_time".
        """
        return self.__format_elapsed_time(int(self.processing_time))

    def __add__(self, other) -> 'ClientBackupResult':
        cl_res = ClientBackupResult(self.node_name)

        cl_res.inspected = self.inspected + other.inspected
        cl_res.backed_up = self.backed_up + other.backed_up
        cl_res.updated = self.updated + other.updated
        cl_res.expired = self.expired + other.expired
        cl_res.failed = self.failed + other.failed
        cl_res.retries = self.retries + other.retries
        cl_res.bytes_inspected = self.bytes_inspected + other.bytes_inspected
        cl_res.bytes_transferred = self.bytes_transferred + other.bytes_transferred
        cl_res.aggregate_data_rate = self.aggregate_data_rate + other.aggregate_data_rate
        # Instead of adding up the processing time, show processing time of longest backup
        # in summary
        cl_res.processing_time = max(self.processing_time, other.processing_time)

        return cl_res

    def __str__(self):
        table = tabulate.tabulate([
            ["Inspected:", self.inspected],
            ["Backed up:", self.backed_up],
            ["Updated:", self.updated],
            ["Expired:", self.expired],
            ["Failed:", self.failed],
            ["Retries:", self.retries],
            ["Bytes inspected:", self.bytes_inspected],
            ["Bytes transferred:", self.bytes_transferred],
            ["Aggregate data rate:", self.aggregate_data_rate],
            ["Processing time:", self.processing_time],
        ])

        return f"Data of node: {self.node_name}\n{table}"

    def __eq__(self, other) -> bool:
        return self.inspected == other.inspected and \
               self.backed_up == other.backed_up and \
               self.updated == other.updated and \
               self.expired == other.expired and \
               self.failed == other.failed and \
               self.retries == other.retries and \
               self.bytes_inspected == other.bytes_inspected and \
               self.bytes_inspected_unit == other.bytes_inspected_unit and \
               self.bytes_transferred == other.bytes_transferred and \
               self.bytes_transferred_unit == other.bytes_transferred_unit and \
               self.aggregate_data_rate == other.aggregate_data_rate and \
               self.aggregate_data_rate_unit == other.aggregate_data_rate_unit and \
               self.processing_time == other.processing_time and \
               self.node_name == other.node_name
