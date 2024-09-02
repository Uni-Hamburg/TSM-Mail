"""
Contains the VMResult class which holds all relevant information for a
VMWare backup result from the TSM environment.
"""

from datetime import datetime, timedelta

class VMResult:
    """
    VMResult represents the data collected for a schedule being run for a virtual machine
    in TSM.

    Args:
        schedule_name:          Name of the VM schedule
        vm_name:                Name of the virtual machine
        start_time:             Start time of VM schedule
        end_time:               End time of VM schedule
        successful:             Status of schedule (true / false)
        activity:               Activity of associated schedule (e.g. BACKUP for backup)
        activity_type:          Type of schedules activity (e.g. Incremental Forever - Full)
        backed_up_bytes:        Amount of bytes being backed up in schedule
        entity:                 Name of VMWare TDP entity
    """

    def __calculate_elapsed_time(self) -> timedelta:
        # Caclulate the elapsed time in the format MM:SS
        start_time_d = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end_time_d = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")

        time_diff = end_time_d - start_time_d

        return time_diff

    def __init__(self, schedule_name: str = "", vm_name: str = "", start_time: str = "",
                 end_time: str = "", successful: bool = False, activity: str = "",
                 activity_type: str = "", backed_up_bytes: int = 0, entity: str = ""):
        self.schedule_name = schedule_name
        self.vm_name = vm_name
        self.start_time = start_time.split('.')[0].strip() # Remove millisecs
        self.end_time = end_time.split('.')[0].strip()   # Remove millisecs
        self.successful = successful
        self.activity = activity
        self.activity_type = activity_type
        self.backed_up_bytes = backed_up_bytes
        self.backed_up_bytes_unit = "GB"
        self.entity = entity

        if start_time:
            self.elapsed_time = self.__calculate_elapsed_time()
        else:
            self.elapsed_time = timedelta()

    def __convert_notation(self, num_string: str) -> str:
        # Convert from US notation to EU notation.
        return num_string.replace('.', 'x').replace(',', '.').replace('x', ',')

    def __format_backed_up_bytes(self, precision: int = 2) -> str:
        # Format and return backed up bytes as string.
        units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}
        size = format(self.backed_up_bytes / units[self.backed_up_bytes_unit], f",.{precision}f")

        return self.__convert_notation(size)

    def __format_elapsed_time(self) -> str:
        # Format elapsed time for node and return as string.
        minutes, seconds = divmod(int(self.elapsed_time.total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def backed_up_bytes_str(self) -> str:
        """
        Returns a formatted string for "backed_up_bytes".
        """
        return self.__format_backed_up_bytes()

    def elapsed_time_str(self):
        """
        Returns a formatted string for "elapsed_time".
        """
        return self.__format_elapsed_time()

    def __add__(self, other: 'VMResult') -> 'VMResult':
        res = VMResult()

        res.backed_up_bytes = self.backed_up_bytes + other.backed_up_bytes
        res.elapsed_time = self.elapsed_time + other.elapsed_time

        return res

    def __eq__(self, other: 'VMResult') -> bool:
        return self.schedule_name == other.schedule_name and \
               self.vm_name == other.vm_name and \
               self.start_time == other.start_time and \
               self.end_time == other.end_time and \
               self.successful == other.successful and \
               self.activity == other.activity and \
               self.activity_type == other.activity_type and \
               self.backed_up_bytes == other.backed_up_bytes and \
               self.backed_up_bytes_unit == other.backed_up_bytes_unit and \
               self.entity == other.entity and \
               self.elapsed_time == other.elapsed_time
