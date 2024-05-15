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

    # Caclulate the elapsed time in the format MM:SS
    def __calculate_elapsed_time(self) -> timedelta:
        start_time_d = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
        end_time_d = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")

        time_diff = end_time_d - start_time_d

        return time_diff

    def __init__(self, schedule_name: str = "", vm_name: str = "", start_time: str = "",
                 end_time: str = "", successful: bool = False, activity: str = "", activity_type: str = "",
                 backed_up_bytes: int = 0, entity: str = ""):
        self.schedule_name = schedule_name
        self.vm_name = vm_name
        self.start_time = start_time.split('.')[0] # Remove millisecs
        self.end_time = end_time.split('.')[0]   # Remove millisecs
        self.successful = successful
        self.activity = activity
        self.activity_type = activity_type
        self.backed_up_bytes = backed_up_bytes
        self.backed_up_bytes_unit = "GB"
        self.entity = entity

        if start_time != "":
            self.elapsed_time = self.__calculate_elapsed_time()
        else:
            self.elapsed_time = timedelta()

        self.update_str_representation()

    def __convert_notation(self, num_string: str) -> str:
        # Convert from US notation to EU notation
        return num_string.replace('.', 'x').replace(',', '.').replace('x', ',')

    def __format_backed_up_bytes(self, precision: int = 2) -> str:
        units = {"B": 1, "KB": 10**3, "MB": 10**6, "GB": 10**9, "TB": 10**12}
        size = format(self.backed_up_bytes / units[self.backed_up_bytes_unit], f",.{precision}f")

        return self.__convert_notation(size)

    def __format_elapsed_time(self) -> str:
        minutes, seconds = divmod(int(self.elapsed_time.total_seconds()), 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def update_str_representation(self):
        self.backed_up_bytes_str = self.__format_backed_up_bytes()
        self.elapsed_time_str = self.__format_elapsed_time()

    def __add__(self, other: 'VMResult') -> 'VMResult':
        res = VMResult()

        res.backed_up_bytes = self.backed_up_bytes + other.backed_up_bytes
        res.elapsed_time = self.elapsed_time + other.elapsed_time

        res.update_str_representation()

        return res
