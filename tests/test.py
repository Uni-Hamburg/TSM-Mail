#!/usr/bin/env python

"""
Contains various tests for the tsm_mail application.
"""
import sys
import unittest
import random
from typing import List
from datetime import datetime, timedelta

# TODO: Find better solution to this workaround
sys.path.append('.')
from parsing.policy_domain import PolicyDomain
from parsing.node import Node
from parsing.schedule_status import SchedulesParser
from parsing.constants import NODE_DECOMM_STATE_NO
from parsing.tsm_data import TSMData

# Generates a formatted time string for test server logs, so the
# schedule parsed from the server logs is not dropped.
def format_time(offset_days = 0) -> str:
    time = datetime.now() + timedelta(days=offset_days)
    return time.strftime('%Y-%m-%d %H:%M:%S')

def get_schedule_logs_successful(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    return [
        f'{domain},{schedule},{node_name},{format_time(-3)},,,Uncertain,,',
        f'{domain},{schedule},{node_name},{format_time(-2)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-23 21:11:07,2024-08-24 05:16:46,Completed,4,The operation completed successfully, but some files were not processed.',
        f'{domain},{schedule},{node_name},{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(1)},,,Future,,'
    ]

def get_schedule_logs_failed(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    return [
        f'{domain},{schedule},{node_name},{format_time(-2)},,,Uncertain,,',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Failed,12,Backup failed with RC : str= 12.',
        f'{domain},{schedule},{node_name},{format_time(1)},,,Future,,'
    ]

def get_schedule_logs_missed(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    return [
        f'{domain},{schedule},{node_name},{format_time(-2)},,,Uncertain,,',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Missed,0,Client missed schedule TEST_SCHEDULE.',
        f'{domain},{schedule},{node_name},{format_time(1)},,,Future,,'
    ]

def get_schedule_logs_edge_cases(domain: str='DOMAIN', schedule: str='SCHEDULE', node_name: str='NODE') -> List[str]:
    return [
        f'{domain},{schedule},{node_name},{format_time(-30)},2024-07-01 00:00:00,2024-07-01 01:00:00,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(-15)},,2024-09-30 00:00:00,,Missed,0,Client missed schedule TEST_SCHEDULE.',
        f'{domain},{schedule},{node_name},{format_time(15)},,2024-09-30 00:00:00,,Completed,0,All operations completed successfully.',
        f'{domain},{schedule},{node_name},{format_time(30)},,2024-09-30 00:00:00,,Future,,',
        f'{domain},{schedule},{node_name},{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Incomplete,3,"The operation completed but not all tasks finished."',
    ]

def generate_random_backup_results(node_name: str) -> List[str]:
    inspected_objects = random.randint(10_000_000, 15_000_000)
    backed_up_objects = random.randint(0, 10_000)
    updated_objects = random.randint(0, 5_000)
    rebound_objects = random.randint(0, 100)
    deleted_objects = random.randint(0, 100)
    expired_objects = random.randint(0, 500)
    failed_objects = random.randint(0, 10)
    encrypted_objects = random.randint(0, 10)
    grew_objects = random.randint(0, 10)
    retries = random.randint(0, 20)
    inspected_bytes = round(random.uniform(60, 70), 2)  # In TB
    transferred_bytes = round(random.uniform(200, 250), 2)  # In GB
    data_transfer_time = round(random.uniform(1500, 2000), 2)  # In seconds
    network_rate = round(random.uniform(100000, 200000), 2)  # In KB/sec
    aggregate_rate = round(random.uniform(40000, 60000), 2)  # In KB/sec
    compression_rate = random.randint(0, 100)
    data_reduction_ratio = round(random.uniform(90, 99), 2)  # In %
    elapsed_time = f"{random.randint(0, 4):02}:{random.randint(0, 59):02}:{random.randint(0, 59):02}"  # In HH:MM:SS

    # TODO: Change notation (make notation configurable)
    def change_notation(input):
        return format(input, ',').replace(',', '%').replace('.', ',').replace('%', '.')

    return [
        f'{node_name},ANE4952I Total number of objects inspected:   {change_notation(inspected_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4954I Total number of objects backed up:        {change_notation(backed_up_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4958I Total number of objects updated:          {change_notation(updated_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4960I Total number of objects rebound:              {change_notation(rebound_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4957I Total number of objects deleted:              {change_notation(deleted_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4970I Total number of objects expired:            {change_notation(expired_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4959I Total number of objects failed:               {change_notation(failed_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4197I Total number of objects encrypted:            {change_notation(encrypted_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4914I Total number of objects grew:                 {change_notation(grew_objects)}  (SESSION: 999999)',
        f'{node_name},ANE4916I Total number of retries:                     {change_notation(retries)}  (SESSION: 999999)',
        f'{node_name},ANE4977I Total number of bytes inspected:          {change_notation(inspected_bytes)} TB  (SESSION: 999999)',
        f'{node_name},ANE4961I Total number of bytes transferred:       {change_notation(transferred_bytes)} GB  (SESSION: 999999)',
        f'{node_name},ANE4963I Data transfer time:                    {change_notation(data_transfer_time)} sec  (SESSION: 999999)',
        f'{node_name},ANE4966I Network data transfer rate:          {change_notation(network_rate)} KB/sec  (SESSION: 999999)',
        f'{node_name},ANE4967I Aggregate data transfer rate:         {change_notation(aggregate_rate)} KB/sec  (SESSION: 999999)',
        f'{node_name},ANE4968I Objects compressed by:                        {change_notation(compression_rate)}%   (SESSION: 999999)',
        f'{node_name},ANE4976I Total data reduction ratio:               {change_notation(data_reduction_ratio)}%   (SESSION: 999999)',
        f'{node_name},ANE4964I Elapsed processing time:               {elapsed_time}  (SESSION: 999999)'
    ]

def get_test_node_log(node_name: str="NODE", platform_name: str="Unknown Platform", domain_name: str="DOMAIN",
                      policy_domain_contact: str="", node_contact: str="") -> str:
    return f'{node_name},{platform_name},{domain_name},,{policy_domain_contact},{node_contact}'

class TestPolicyDomains(unittest.TestCase):
    """
    Tests surrounding policy domains.
    """
    def test_policy_domain_schedules(self):
        """
        Tests schedule parsing from server logs and "has_client_schedules" and
        "has_non_successful_schedules" methods.
        """

        # Normal server schedule log with successful schedules
        server_log_successful = get_schedule_logs_successful()

        # Normal server schedule log with failed schedules
        server_log_with_failed = get_schedule_logs_failed()

        # Normal server schedule log with missed schedules
        server_log_with_missed = get_schedule_logs_missed()

        # Testing data for edge cases and erroneous server logs
        server_log_with_errors = get_schedule_logs_edge_cases()

        node_successful = Node("NODE_SUCCESSFUL", "Linux", "TEST_DOMAIN", NODE_DECOMM_STATE_NO)
        node_with_failed = Node("NODE_WITH_FAILED", "Linux", "TEST_DOMAIN", NODE_DECOMM_STATE_NO)
        node_with_missed = Node("NODE_WITH_MISSED", "WinNT", "TEST_DOMAIN", NODE_DECOMM_STATE_NO)
        node_with_errors = Node("NODE_WITH_ERRORS", "Unknown Platform", "TEST_DOMAIN", NODE_DECOMM_STATE_NO)

        # Nodes should not have any schedules
        self.assertFalse(node_successful.has_client_schedules())
        self.assertFalse(node_with_failed.has_client_schedules())
        self.assertFalse(node_with_missed.has_client_schedules())
        self.assertFalse(node_with_errors.has_client_schedules())

        schedule_parser = SchedulesParser()
        node_successful.schedules = schedule_parser.parse(server_log_successful)
        node_with_failed.schedules = schedule_parser.parse(server_log_with_failed)
        node_with_missed.schedules = schedule_parser.parse(server_log_with_missed)
        node_with_errors.schedules = schedule_parser.parse(server_log_with_errors)

        self.assertTrue(node_successful.has_client_schedules())
        self.assertFalse(node_successful.has_non_successful_schedules())

        self.assertTrue(node_with_failed.has_client_schedules())
        self.assertTrue(node_with_failed.has_non_successful_schedules())

        self.assertTrue(node_with_missed.has_client_schedules())
        self.assertTrue(node_with_missed.has_non_successful_schedules())

        self.assertFalse(node_with_errors.has_client_schedules())

        # Test policy domain with only successful backup schedules
        policy_domain = PolicyDomain([
            node_successful
        ], "TEST_DOMAIN")

        self.assertTrue(policy_domain.has_client_schedules())
        self.assertFalse(policy_domain.has_non_successful_schedules())

        # Add non successful backup schedules
        policy_domain.nodes.extend([node_with_failed, node_with_missed, node_with_errors])
        self.assertTrue(policy_domain.has_client_schedules())
        self.assertTrue(policy_domain.has_non_successful_schedules())

    def test_node_and_client_backup_parsing(self):
        """
        Tests parsing of nodes and backup results from a server log.
        """
        nodes_log = [
            # TEST_DOMAIN_A
            get_test_node_log('NODE_A', 'Linux x86-64', 'TEST_DOMAIN_A', policy_domain_contact='backup@company-a.de'),
            get_test_node_log('NODE_B', 'Linux x86-64', 'TEST_DOMAIN_A', policy_domain_contact='backup@company-a.de'),
            get_test_node_log('NODE_C', 'Linux x86-64', 'TEST_DOMAIN_A', policy_domain_contact='backup@company-a.de'),
            get_test_node_log('NODE_D', 'Linux x86-64', 'TEST_DOMAIN_A', policy_domain_contact='backup@company-a.de'),
            # TEST_DOMAIN_Z
            get_test_node_log('NODE_X', 'WinNT', 'TEST_DOMAIN_Z', policy_domain_contact='it.center@company-b.com'),
            get_test_node_log('NODE_Y', 'WinNT', 'TEST_DOMAIN_Z', policy_domain_contact='it.center@company-b.com'),
            get_test_node_log('NODE_Z', 'WinNT', 'TEST_DOMAIN_Z', policy_domain_contact='it.center@company-b.com'),
            # Loose nodes without specific domain (have a contact set for each node)
            get_test_node_log('LOOSE_NODE_A', 'Linux x86-64', 'TEST_DOMAIN_LOOSE', node_contact='mr.a@acomp.com'),
            get_test_node_log('LOOSE_NODE_B', 'Linux x86-64', 'TEST_DOMAIN_LOOSE', node_contact='mr.b@bcomp.com'),
        ]

        client_backup_logs = {
            'NODE_A': generate_random_backup_results('NODE_A'),
            'NODE_B': generate_random_backup_results('NODE_B'),
            'NODE_C': generate_random_backup_results('NODE_C'),
            'NODE_D': generate_random_backup_results('NODE_D'),
            'NODE_X': generate_random_backup_results('NODE_X'),
            'NODE_Y': generate_random_backup_results('NODE_Y'),
            'NODE_Z': generate_random_backup_results('NODE_Z'),
            'LOOSE_NODE_A': generate_random_backup_results('LOOSE_NODE_A'),
            'LOOSE_NODE_B': generate_random_backup_results('LOOSE_NODE_B')
        }

        node_schedule_logs = {
            'NODE_A': get_schedule_logs_successful('TEST_DOMAIN_A', 'SCHEDULE_A', 'NODE_A'),
            'NODE_B': get_schedule_logs_successful('TEST_DOMAIN_A', 'SCHEDULE_A', 'NODE_B'),
            'NODE_C': get_schedule_logs_successful('TEST_DOMAIN_A', 'SCHEDULE_A', 'NODE_C'),
            'NODE_D': get_schedule_logs_successful('TEST_DOMAIN_A', 'SCHEDULE_A', 'NODE_D'),
            'NODE_X': get_schedule_logs_successful('TEST_DOMAIN_Z', 'SCHEDULE_Z', 'NODE_X'),
            'NODE_Y': get_schedule_logs_successful('TEST_DOMAIN_Z', 'SCHEDULE_Z', 'NODE_Y'),
            'NODE_Z': get_schedule_logs_successful('TEST_DOMAIN_Z', 'SCHEDULE_Z', 'NODE_Z'),
            'LOOSE_NODE_A': get_schedule_logs_successful('TEST_DOMAIN_LOOSE',
                                                         'SCHEDULE_LOOSE',
                                                         'LOOSE_NODE_A'),
            'LOOSE_NODE_B': get_schedule_logs_successful('TEST_DOMAIN_LOOSE',
                                                         'SCHEDULE_LOOSE',
                                                         'LOOSE_NODE_B')
        }

        data = TSMData()
        data.parse_nodes(nodes_log)
        data.parse_schedules_and_backup_results(node_schedule_logs, client_backup_logs)

        # There should be 3 policy domains and 9 nodes parsed
        self.assertEqual(len(data.domains), 3)
        self.assertEqual(len(data.nodes), 9)

        self.assertTrue(all(node.schedules for node in data.nodes.values()))

if __name__ == '__main__':
    unittest.main()
