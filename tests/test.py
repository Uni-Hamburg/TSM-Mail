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
from parsing.constants import NODE_DECOMM_STATE_NO
from parsing.tsm_data import TSMData
from parsing.schedule_status import SchedulesParser, ScheduleStatusEnum
from parsing.report_template import ReportTemplate

from tests.mock import mock_schedule_logs_successful, mock_schedule_logs_edge_cases, \
    mock_schedule_logs_failed, get_schedule_logs_missed, mock_node_log, \
    mock_backup_result_log, mock_schedule_logs

class TestParsing(unittest.TestCase):
    """
    Tests surrounding parsing of server logs.
    """
    def test_policy_domain_schedules(self):
        """
        Tests schedule parsing from server logs and "has_client_schedules" and
        "has_non_successful_schedules" methods.
        """

        domain_test_name = 'TEST_DOMAIN'

        # Normal server schedule log with successful schedules
        server_log_successful = mock_schedule_logs_successful()

        # Normal server schedule log with failed schedules
        server_log_with_failed = mock_schedule_logs_failed()

        # Normal server schedule log with missed schedules
        server_log_with_missed = get_schedule_logs_missed()

        # Testing data for edge cases and erroneous server logs
        server_log_with_errors = mock_schedule_logs_edge_cases()

        node_successful = Node('NODE_SUCCESSFUL', 'Linux', domain_test_name, NODE_DECOMM_STATE_NO)
        node_with_failed = Node('NODE_WITH_FAILED', 'Linux', domain_test_name, NODE_DECOMM_STATE_NO)
        node_with_missed = Node('NODE_WITH_MISSED', 'WinNT', domain_test_name, NODE_DECOMM_STATE_NO)
        node_with_errors = Node('NODE_WITH_ERRORS', 'Unknown Platform', domain_test_name, NODE_DECOMM_STATE_NO)

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
        ], domain_test_name)

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
        domain_a_name = 'TEST_DOMAIN_A'
        domain_z_name = 'TEST_DOMAIN_Z'
        domain_loose_name = 'TEST_DOMAIN_LOOSE'

        node_a_name = 'NODE_A'
        node_b_name = 'NODE_B'
        node_c_name = 'NODE_C'
        node_d_name = 'NODE_D'

        node_x_name = 'NODE_X'
        node_y_name = 'NODE_Y'
        node_z_name = 'NODE_Z'

        node_loose_a_name = 'LOOSE_NODE_A'
        node_loose_b_name = 'LOOSE_NODE_B'

        schedule_a_name = 'SCHEDULE_A'
        schedule_z_name = 'SCHEDULE_Z'
        schedule_loose_name = 'SCHEDULE_LOOSE'

        nodes_log = [
            # TEST_DOMAIN_A
            mock_node_log(node_a_name, 'Linux x86-64', domain_a_name, policy_domain_contact='backup@company-a.de'),
            mock_node_log(node_b_name, 'Linux x86-64', domain_a_name, policy_domain_contact='backup@company-a.de'),
            mock_node_log(node_c_name, 'Linux x86-64', domain_a_name, policy_domain_contact='backup@company-a.de'),
            mock_node_log(node_d_name, 'Linux x86-64', domain_a_name, policy_domain_contact='backup@company-a.de'),
            # TEST_DOMAIN_Z
            mock_node_log(node_x_name, 'WinNT', domain_z_name, policy_domain_contact='it.center@company-b.com'),
            mock_node_log(node_y_name, 'WinNT', domain_z_name, policy_domain_contact='it.center@company-b.com'),
            mock_node_log(node_z_name, 'WinNT', domain_z_name, policy_domain_contact='it.center@company-b.com'),
            # Loose nodes without specific domain (have a contact set for each node)
            mock_node_log(node_loose_a_name, 'Linux x86-64', domain_loose_name, node_contact='mr.a@acomp.com'),
            mock_node_log(node_loose_b_name, 'Linux x86-64', domain_loose_name, node_contact='mr.b@bcomp.com'),
        ]

        client_backup_logs = {
            node_a_name: mock_backup_result_log(node_a_name),
            node_b_name: mock_backup_result_log(node_b_name),
            node_c_name: mock_backup_result_log(node_c_name),
            node_d_name: mock_backup_result_log(node_d_name),
            node_x_name: mock_backup_result_log(node_x_name),
            node_y_name: mock_backup_result_log(node_y_name),
            node_z_name: mock_backup_result_log(node_z_name),
            node_loose_a_name: mock_backup_result_log(node_loose_a_name),
            node_loose_b_name: mock_backup_result_log(node_loose_b_name)
        }

        node_schedule_logs = {
            node_a_name: mock_schedule_logs_successful(domain_a_name, schedule_a_name, node_a_name),
            node_b_name: mock_schedule_logs_successful(domain_a_name, schedule_a_name, node_b_name),
            node_c_name: mock_schedule_logs_successful(domain_a_name, schedule_a_name, node_c_name),
            node_d_name: mock_schedule_logs_successful(domain_a_name, schedule_a_name, node_d_name),
            node_x_name: mock_schedule_logs_successful(domain_z_name, schedule_z_name, node_x_name),
            node_y_name: mock_schedule_logs_successful(domain_z_name, schedule_z_name, node_y_name),
            node_z_name: mock_schedule_logs_successful(domain_z_name, schedule_z_name, node_z_name),
            node_loose_a_name: mock_schedule_logs_successful(domain_loose_name,
                                                            schedule_loose_name,
                                                            node_loose_a_name),
            node_loose_b_name: mock_schedule_logs_successful(domain_loose_name,
                                                            schedule_loose_name,
                                                            node_loose_b_name)
        }

        data = TSMData()
        data.parse_nodes(nodes_log)
        data.parse_schedules_and_backup_results(node_schedule_logs, client_backup_logs)

        # There should be 3 policy domains and 9 nodes parsed
        self.assertEqual(len(data.domains), 3)
        self.assertEqual(len(data.nodes), 9)

        self.assertTrue(all(node.has_client_schedules() for node in data.nodes.values()))

    def test_jinja_parsing(self):
        """
        Tests parsing the HTML report from existing data.
        """

        domain_a_name = 'DOMAIN_A'
        schedule_a_name = 'SCHEDULE_A'

        data = TSMData("TSMSRV1")

        schedules_log = {
            'NODE_A': mock_schedule_logs(domain_a_name, 'NODE_A', schedule_a_name, ScheduleStatusEnum.SUCCESSFUL),
            'NODE_B': mock_schedule_logs(domain_a_name, 'NODE_B', schedule_a_name, ScheduleStatusEnum.MISSED),
            'NODE_C': mock_schedule_logs(domain_a_name, 'NODE_C', schedule_a_name, ScheduleStatusEnum.FAILED)
        }

        client_backup_logs = {
            'NODE_A': mock_backup_result_log('NODE_A'),
            'NODE_B': mock_backup_result_log('NODE_B'),
            'NODE_C': mock_backup_result_log('NODE_C')
        }

        nodes_log = [
            mock_node_log('NODE_A', 'Linux x86-64', domain_a_name, 'contact@company.com'),
            mock_node_log('NODE_B', 'Linux x86-64', domain_a_name, 'contact@company.com'),
            mock_node_log('NODE_C', 'Linux x86-64', domain_a_name, 'contact@company.com')
        ]

        data.parse_nodes(nodes_log)
        data.parse_schedules_and_backup_results(schedules_log, client_backup_logs)

        template = ReportTemplate('./templates/statusmail.j2')
        rendered_template = template.render(data.domains[domain_a_name])

        with open('./tests/rendered_template_expected.html', 'r', encoding='utf-8') as f:
            rendered_template_expected = f.read()
        self.assertEqual(rendered_template_expected, rendered_template)

if __name__ == '__main__':
    unittest.main()
