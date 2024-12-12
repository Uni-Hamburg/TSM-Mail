"""
Contains functions to interface with the TSM environment through the admin console (dsmadmc).
"""

import subprocess
import logging
import multiprocessing as mp
from typing import Any, cast
from datetime import datetime, timedelta
from dataclasses import dataclass

from parsing.constants import LINE_DELIM, COLUMN_NODE_NAME

logger = logging.getLogger("main")


@dataclass
class CollectorConfig:
    """
    CollectorConfig contains necessary information to fetch data from the ISP / TSM environment.
    Args:
        config: Software configuration (config file)
        inst: The ISP server / instance to fetch data from
        pwd: The password for the user to fetch the data with
    """

    app_config: dict[str, Any]
    inst: str
    pwd: str


def __issue_cmd(config: CollectorConfig, cmd: str) -> bytes:
    # Sends a command to the TSM server using the admin console 'dsmadmc'.
    try:
        cmd_result = subprocess.check_output(
            [
                "dsmadmc",
                f"-se={config.inst}",
                f"-id={config.app_config['tsm_user']}",
                f"-password={config.pwd.rstrip()}",
                "-dataonly=yes",
                "-comma",
                "-out",
                cmd,
            ]
        )
        return cmd_result
    except subprocess.CalledProcessError as exception:
        if "ANR2034E" in str(exception.output):
            logger.info(
                'Query "%s" \nreturned error: "%s", returning empty string.',
                cmd,
                exception.output,
            )
            return bytes()

        logger.error("Error calling dsmadmc: %s", exception.output)
        raise exception


def __collect_schedule_for_node(
    config: CollectorConfig, sched_logs: dict[str, list[str]], node_name: str
):
    # Queries all schedules for a node with node_name.
    logger.info("Collecting schedule status for %s on %s...", node_name, config.inst)

    sched_stat_r = __issue_cmd(
        config,
        f"QUERY EVENT * * node={node_name} " "f=d begint=now endd=today begind=-15",
    )
    sched_stat_str = sched_stat_r.decode("utf-8", "replace")
    sched_stat_list = sched_stat_str.splitlines()

    # Don't add empty logs
    if sched_stat_list:
        sched_logs[node_name] = sched_stat_list


def __collect_client_backup_result(
    config: CollectorConfig, cl_logs: dict[str, list[str]], node_name: str
):
    # Queries client backup results for the last 24 hours for node with node_name.
    logger.info(
        "Collecting client backup result for %s on %s...", node_name, config.inst
    )

    cl_stat_r = __issue_cmd(
        config,
        "SELECT nodename, message FROM actlog "
        "WHERE originator = 'CLIENT' "
        "AND date_time>current_timestamp - 24 hours "
        f"AND nodename = '{node_name}'",
    )
    cl_stat_list = cl_stat_r.decode("utf-8", "replace").splitlines()

    # Don't add empty logs
    if cl_stat_list:
        cl_logs[node_name] = cl_stat_list


def collect_nodes_and_domains(config: CollectorConfig) -> list[str]:
    """
    Runs SQL query to get all nodes and policy domains.
    """
    nodes_r = __issue_cmd(
        config,
        "SELECT n.node_name, n.platform_name, n.domain_name, "
        "n.decomm_state, d.description, n.contact FROM nodes n, domains d "
        "WHERE d.domain_name = n.domain_name AND n.decomm_state IS NULL",
    )
    nodes_str = nodes_r.decode("utf-8", "replace")
    nodes_and_domains_logs = nodes_str.splitlines()

    return nodes_and_domains_logs


def collect_vm_schedules(config: CollectorConfig) -> list[str]:
    """
    Gets all status logs for the VMWare backup schedules.
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    today_str = today.strftime("%Y-%m-%d %H:%M:%S")
    yesterday_str = yesterday.strftime("%Y-%m-%d %H:%M:%S")

    logger.info("Collecting VMWare schedules on %s...", config.inst)

    vm_results_r = __issue_cmd(
        config,
        "SELECT schedule_name, sub_entity, start_time, end_time, "
        "successful, activity, activity_type, bytes, entity "
        f"FROM summary_extended WHERE (activity_details='VMware' "
        "OR activity_details LIKE '%Hyper%') AND start_time "
        f"BETWEEN '{yesterday_str}' AND '{today_str}'",
    )

    vm_results_str = vm_results_r.decode("utf-8", "replace")
    vm_results_list = vm_results_str.splitlines()

    logger.info("Collected VMWare schedule data for %d VMs.", len(vm_results_list))

    return vm_results_list


def collect_schedule_logs(
    config: CollectorConfig, log: list[str]
) -> dict[str, list[str]]:
    """
    Reads and returns schedule logs for a node.
    """
    sched_logs_manager = mp.Manager()
    sched_logs = cast(dict[str, list[str]], sched_logs_manager.dict())

    nodes: list[str] = []

    for line in log:
        nodes.append(line.split(LINE_DELIM)[COLUMN_NODE_NAME])

    with mp.Pool() as pool:
        pool.starmap(
            __collect_schedule_for_node,
            [(config, sched_logs, node_name) for node_name in nodes],
        )

    return sched_logs


def collect_client_backup_results(
    config: CollectorConfig, log: list[str]
) -> dict[str, list[str]]:
    """
    Gets all client backup results for the last 24 hours from a node.
    """
    cl_logs_manager = mp.Manager()
    cl_logs = cast(dict[str, list[str]], cl_logs_manager.dict())

    nodes: list[str] = []

    for line in log:
        nodes.append(line.split(LINE_DELIM)[COLUMN_NODE_NAME])

    with mp.Pool() as pool:
        pool.starmap(
            __collect_client_backup_result,
            [(config, cl_logs, node_name) for node_name in nodes],
        )

    return cl_logs
