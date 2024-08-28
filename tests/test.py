#!/usr/bin/env python

"""
Contains various tests for the tsm_mail application.
"""
import sys
import unittest
from datetime import datetime, timedelta

# TODO: Find better solution to this workaround
sys.path.append('.')
from parsing.policy_domain import PolicyDomain
from parsing.node import Node
from parsing.schedule_status import SchedulesParser
from parsing.constants import NODE_DECOMM_STATE_NO

class TestPolicyDomains(unittest.TestCase):
    """
    Tests surrounding policy domains.
    """
    def test_policy_domain_schedules(self):
        """
        Tests schedule parsing from server logs and "has_client_schedules" and
        "has_non_successful_schedules" methods.
        """

        # Generates a formatted time string for test server logs, so the
        # schedule parsed from the server logs is not dropped.
        def format_time(offset_days = 0) -> str:
            time = datetime.now() + timedelta(days=offset_days)
            return time.strftime('%Y-%m-%d %H:%M:%S')

        # Normal server schedule log with successful schedules
        server_log_successful = [
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-3)},,,Uncertain,,',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-2)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-1)},2024-08-23 21:11:07,2024-08-24 05:16:46,Completed,4,"The operation completed successfully, but some files were not processed."',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Completed,0,All operations completed successfully.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(1)},,,Future,,'
        ]

        # Normal server schedule log with failed schedules
        server_log_with_failed = [
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-2)},,,Uncertain,,',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Failed,12,Backup failed with RC = 12.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(1)},,,Future,,'
        ]

        # Normal server schedule log with missed schedules
        server_log_with_missed = [
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-2)},,,Uncertain,,',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time()},2024-08-26 21:10:03,2024-08-26 22:37:12,Missed,0,Client missed schedule TEST_SCHEDULE.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(1)},,,Future,,'
        ]

        # Testing data for edge cases and erroneous server logs
        server_log_with_errors = [
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-30)},2024-07-01 00:00:00,2024-07-01 01:00:00,Completed,0,All operations completed successfully.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-15)},,2024-09-30 00:00:00,,Missed,0,Client missed schedule TEST_SCHEDULE.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(15)},,2024-09-30 00:00:00,,Completed,0,All operations completed successfully.',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(30)},,2024-09-30 00:00:00,,Future,,',
            f'TEST_DOMAIN,TEST_SCHEDULE,NODE,{format_time(-1)},2024-08-25 21:10:15,2024-08-25 22:05:53,Incomplete,3,"The operation completed but not all tasks finished."',
        ]

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

if __name__ == '__main__':
    unittest.main()
