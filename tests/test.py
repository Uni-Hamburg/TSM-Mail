#!/usr/bin/env python

"""
Contains various tests for the tsm_mail application.
"""
import sys
import unittest

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
        Tests "has_client_schedules" and "has_non_successful_schedules" for three nodes 
        with "Completed", "Failed" and "Missed" status in a policy domain.
        """

        schedule_parser = SchedulesParser()

        server_log_without_failed = [
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-23 21:10:00,,,Uncertain,,',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-24 21:10:00,2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-25 21:10:00,2024-08-23 21:11:07,2024-08-24 05:16:46,Completed,4,"The operation completed successfully, but some files were not processed."',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-26 21:10:00,2024-08-26 21:10:03,2024-08-26 22:37:12,Completed,0,All operations completed successfully.',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-27 21:10:00,,,Future,,'
        ]

        server_log_with_failed = [
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-24 21:10:00,,,Uncertain,,',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-25 21:10:00,2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-26 21:10:00,2024-08-26 21:10:03,2024-08-26 22:37:12,Failed,12,Backup failed with RC = 12.',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-27 21:10:00,,,Future,,'
        ]

        server_log_with_missed = [
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-24 21:10:00,,,Uncertain,,',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-25 21:10:00,2024-08-25 21:10:15,2024-08-25 22:05:53,Completed,0,All operations completed successfully.',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-26 21:10:00,2024-08-26 21:10:03,2024-08-26 22:37:12,Missed,0,Client missed schedule TEST_SCHEDULE.',
            'TEST_DOMAIN,TEST_SCHEDULE,NODE,2024-08-27 21:10:00,,,Future,,'
        ]

        node_successful = Node("NODE_SUCCESSFUL", "Linux", "TEST_DOMAIN", NODE_DECOMM_STATE_NO)
        node_with_failed = Node("NODE_WITH_FAILED", "Linux", "TEST_DOMAIN", NODE_DECOMM_STATE_NO)
        node_with_missed = Node("NODE_WITH_MISSED", "WinNT", "TEST_DOMAIN", NODE_DECOMM_STATE_NO)

        # Nodes should not have any schedules
        self.assertFalse(node_successful.has_client_schedules())
        self.assertFalse(node_with_failed.has_client_schedules())
        self.assertFalse(node_with_missed.has_client_schedules())

        node_successful.schedules = schedule_parser.parse(server_log_without_failed)
        node_with_failed.schedules = schedule_parser.parse(server_log_with_failed)
        node_with_missed.schedules = schedule_parser.parse(server_log_with_missed)

        self.assertTrue(node_successful.has_client_schedules())
        self.assertFalse(node_successful.has_non_successful_schedules())

        self.assertTrue(node_with_failed.has_client_schedules())
        self.assertTrue(node_with_failed.has_non_successful_schedules())

        self.assertTrue(node_with_missed.has_client_schedules())
        self.assertTrue(node_with_missed.has_non_successful_schedules())

        # Test policy domain with only successful backup schedules
        policy_domain = PolicyDomain([
            node_successful
        ], "TEST_DOMAIN")

        self.assertTrue(policy_domain.has_client_schedules())
        self.assertFalse(policy_domain.has_non_successful_schedules())

        # Add non successful backup schedules
        policy_domain.nodes.extend([node_with_failed, node_with_missed])
        self.assertTrue(policy_domain.has_client_schedules())
        self.assertTrue(policy_domain.has_non_successful_schedules())

if __name__ == '__main__':
    unittest.main()
