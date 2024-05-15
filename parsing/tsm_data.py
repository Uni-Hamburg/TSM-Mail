from typing import Dict, List

from parsing.helper import check_non_successful_schedules

from parsing.node import Node
from parsing.constants import LINE_DELIM, COLUMN_NODE_NAME, COLUMN_PLATFORM_NAME, COLUMN_PD_NAME, \
    COLUMN_DECOMM_STATE, COLUMN_DOMAIN_CONTACT, COLUMN_NODE_CONTACT, COLUMN_VM_SCHED_NAME, \
    COLUMN_VM_NAME, COLUMN_VM_START_TIME, COLUMN_VM_END_TIME, COLUMN_VM_SUCCESS, \
    COLUMN_VM_ACTIVITY, COLUMN_VM_ACT_TYPE, COLUMN_VM_BYTES, COLUMN_VM_ENTITY
from parsing.policy_domain import PolicyDomain
from parsing.vmresult import VMResult
from parsing.schedule_status import SchedulesParser
from parsing.client_backup_result import ClientBackupResult

class TSMData:
    """
    TSMData contains dictionaries holding nodes and policy domains parsed from the
    TSM environment.

    Args:
        instance_id:    ID of the associated instance with the data
    """
    def __init__(self, instance_id: str = ""):
        self.instance_id: str = instance_id
        self.nodes: Dict[str, Node] = {}
        self.domains: Dict[str, PolicyDomain] = {}
        self.vm_results: Dict[str, VMResult] = {}

    def parse_nodes(self, nodes_log: List[str]):
        for line in nodes_log:
            # Split line using , as delimiter
            line_split = line.split(LINE_DELIM)

            # First three columns contain information about the node
            node_name = line_split[COLUMN_NODE_NAME]
            platform_name = line_split[COLUMN_PLATFORM_NAME]
            policy_domain_name = line_split[COLUMN_PD_NAME]

            # Get the state of decomissionment
            node_decomm_state = line_split[COLUMN_DECOMM_STATE]

            # If a contact is specified in the node itself, use this contact,
            # otherwise use contact from the description field of the policy domain
            domain_description_field = line_split[COLUMN_DOMAIN_CONTACT].strip()
            node_contact_field = line_split[COLUMN_NODE_CONTACT].strip()

            # Create node with platform and email contact, if node has specific contact
            if node_contact_field != "" and domain_description_field == "":
                # Remove string delimiters when multiple mail contacts are supplied
                if node_contact_field.startswith('"'):
                    node_contact_field = node_contact_field[1:len(node_contact_field - 1)]
                self.nodes[node_name] = Node(node_name, platform_name, policy_domain_name,
                                             node_decomm_state, node_contact_field)
            else:
                self.nodes[node_name] = Node(node_name, platform_name, policy_domain_name,
                                             node_decomm_state)

            # Check if domain already exists
            if policy_domain_name not in self.domains:
                # If not, create new policy domain with nodes list
                self.domains[policy_domain_name] = PolicyDomain(name=policy_domain_name)

            # Update policy domain
            self.domains[policy_domain_name].nodes.append(self.nodes[node_name])

            if domain_description_field != "":
                self.domains[policy_domain_name].contact = domain_description_field

    def parse_schedules_and_backup_results(self, sched_stat_logs: List[str], cl_stat_logs: List[str]):
        for _, domain in self.domains.items():
            for node in domain.nodes:
                self.__parse_node_status(domain, node, sched_stat_logs, cl_stat_logs)

                # Add to policy v summary
                if node.backupresult is not None:
                    current_processing_time = domain.client_backup_summary.processing_time

                    domain.client_backup_summary += node.backupresult

                    # Find maximum processing time for processing time summary cell
                    if current_processing_time < \
                        node.backupresult.processing_time:
                        current_processing_time = node.backupresult.processing_time

                    domain.client_backup_summary.processing_time = current_processing_time

            # Sort nodes by failed objects
            domain.nodes.sort(key=lambda x: x.backupresult.failed, reverse=True)

    def __parse_node_status(self, policy_domain: PolicyDomain, node: Node,
                            sched_stat_logs: Dict[str, List[str]],
                            cl_stat_logs: Dict[str, List[str]]):
        # Parse results
        if node.name in sched_stat_logs:
            sched_stat_log = sched_stat_logs[node.name]

            schedules_parser = SchedulesParser()
            node.schedules = schedules_parser.parse(sched_stat_log)

            policy_domain.has_non_successful_schedules = check_non_successful_schedules(policy_domain, node)

        if node.name in cl_stat_logs:
            cl_stat_log = cl_stat_logs[node.name]

            if cl_stat_log is not None and len(cl_stat_log) > 1:
                parsed_cl_res = ClientBackupResult()
                parsed_cl_res.parse(cl_stat_log)
                node.backupresult += parsed_cl_res

                policy_domain.has_client_backups = True

    def parse_vm_schedules(self, vms_log: List[str]):
        for line in vms_log:
            # Split line
            line_split = line.split(LINE_DELIM)

            vm_result = VMResult(
                line_split[COLUMN_VM_SCHED_NAME],
                line_split[COLUMN_VM_NAME],
                line_split[COLUMN_VM_START_TIME],
                line_split[COLUMN_VM_END_TIME],
                line_split[COLUMN_VM_SUCCESS] == "YES",
                line_split[COLUMN_VM_ACTIVITY],
                line_split[COLUMN_VM_ACT_TYPE],
                int(line_split[COLUMN_VM_BYTES]),
                line_split[COLUMN_VM_ENTITY]
            )

            self.vm_results[line_split[COLUMN_VM_NAME]] = vm_result

            # Add VM result to associated node
            if vm_result.entity in self.nodes:
                self.nodes[vm_result.entity].vm_results.append(vm_result)

                domain = self.domains[self.nodes[vm_result.entity].policy_domain_name]

                # Set the VM backup flag in the policy domain
                domain.has_vm_backups = True

                # Add VM result to summary
                domain.vm_backup_summary += vm_result
