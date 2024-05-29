"""
Contains the Collector class which is the interface to the TSM environment.
The collector issues SQL queries and other TSM commands to the TSM server.
"""

import subprocess
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

from parsing.constants import LINE_DELIM, COLUMN_NODE_NAME

logger = logging.getLogger("main")

class Collector():
    """
    Collector class contains multiple functions to fetch data from the ISP / TSM environment.
    Args:
        config: Software configuration (config.json)
        inst: The ISP server / instance to fetch data from
        pwd: The password for the user to fetch the data with
    """
    def __init__(self, config: Dict[str, Any], inst: str, pwd: str):
        self.config = config
        self.inst = inst
        self.pwd = pwd

    def __issue_cmd(self, cmd) -> bytearray:
        # Sends a command to the TSM server using the admin console 'dsmadmc'.
        try:
            cmd_result = subprocess.check_output(
                ["sudo", "dsmadmc", f"-se={self.inst}",
                 f"-id={self.config['tsm_user']}", f"-password={self.pwd}",
                 "-dataonly=yes", "-comma", "-out", cmd])
            return cmd_result
        except subprocess.CalledProcessError as exception:
            if "ANR2034E" in str(exception.output):
                logger.info(f'Query "{cmd}" \nreturned error: " \
                            {exception.output}", returning empty string.')
                return bytearray()

            logger.error(f"Error calling dsmadmc: {exception.output}")
            return exception

    def __collect_schedule_for_node(self, node_name: str) -> List[str]:
        # Queries all schedules for a node with node_name.
        logger.info(f"Collecting schedule status for {node_name} on {self.inst}...")

        sched_stat_r = self.__issue_cmd(
            f"QUERY EVENT * * node={node_name} f=d begint=now endd=today begind=-15")
        sched_stat_str = sched_stat_r.decode("utf-8", "replace")
        sched_stat_list = sched_stat_str.splitlines()

        return sched_stat_list

    def __collect_client_backup_result(self, node_name: str) -> List[str]:
        # Queries client backup results for the last 24 hours for node with node_name.
        logger.info(f"Collecting client backup result for {node_name} on {self.inst}...")

        cl_stat_r = self.__issue_cmd("SELECT nodename, message FROM actlog " \
                                    "WHERE originator = 'CLIENT' " \
                                    f"AND date_time>current_timestamp - 24 hours \
                                    AND nodename = '{node_name}'")
        cl_stat_list = cl_stat_r.decode("utf-8", "replace").splitlines()

        return cl_stat_list

    def collect_nodes_and_domains(self) -> List[str]:
        """
        Runs SQL query to get all nodes and policy domains.
        """
        nodes_r = self.__issue_cmd("SELECT n.node_name, n.platform_name, n.domain_name, " \
                                    "n.decomm_state, d.description, n.contact FROM nodes n, domains d " \
                                    "WHERE d.domain_name = n.domain_name AND n.decomm_state IS NULL")
        nodes_str = nodes_r.decode("utf-8", "replace")
        nodes_and_domains_logs = nodes_str.splitlines()

        return nodes_and_domains_logs

    def collect_vm_schedules(self) -> List[str]:
        """
        Gets all status logs for the VMWare backup schedules.
        """
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        today_str = today.strftime("%Y-%m-%d %H:%M:%S")
        yesterday_str = yesterday.strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Collecting VM schedules on {self.inst}...")

        vm_results_r = self.__issue_cmd("SELECT schedule_name, sub_entity, start_time, end_time, " \
                                "successful, activity, activity_type, bytes, entity " \
                                f"FROM summary_extended WHERE (activity_details='VMware' \
                                OR activity_details LIKE '%Hyper%') AND start_time \
                                BETWEEN '{yesterday_str}' AND '{today_str}'")

        vm_results_str = vm_results_r.decode("utf-8", "replace")
        vm_results_list = vm_results_str.splitlines()

        logger.info(f"Collected VM schedule data for {len(vm_results_list)} VMs.")

        return vm_results_list

    def collect_schedule_logs(self, log: List[str]) -> Dict[str, List[str]]:
        """
        Reads and returns schedule logs for a node.
        """
        sched_logs: Dict[str, List[str]] = {}

        for line in log:
            node = line.split(LINE_DELIM)[COLUMN_NODE_NAME]

            sched_log = self.__collect_schedule_for_node(node)

            # Don't add empty logs
            if len(sched_log) > 0:
                sched_logs[node] = sched_log

        return sched_logs

    def collect_client_backup_results(self, log: List[str]) -> Dict[str, List[str]]:
        """
        Gets all client backup results for the last 24 hours from a node.
        """
        cl_logs: Dict[str, List[str]] = {}

        for line in log:
            node = line.split(LINE_DELIM)[COLUMN_NODE_NAME]

            cl_log = self.__collect_client_backup_result(node)

            # Don't add empty logs
            if len(cl_log) > 0:
                cl_logs[node] = cl_log

        return cl_logs
