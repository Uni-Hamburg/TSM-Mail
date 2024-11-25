#!/usr/bin/env python

"""
Main entrypoint to the TSM mail program.
"""

import getpass
import re
import os
import sys
import pickle
import logging
import logging.handlers
import argparse
from string import Template
from typing import Dict, List, Any, Optional
from datetime import datetime

import yaml

from parsing.tsm_data import TSMData
from parsing.node import Node
from parsing.policy_domain import PolicyDomain
from parsing.constants import LOG_LEVEL_DEBUG_STR, LOG_LEVEL_ERROR_STR, LOG_LEVEL_INFO_STR, \
    LOG_LEVEL_WARN_STR
from parsing.report_template import ReportTemplate

from collector.collector import CollectorConfig, collect_nodes_and_domains, collect_vm_schedules, \
    collect_client_backup_results, collect_schedule_logs

from mailer.status_mailer import StatusMailer
from mailer.mailer import Mailer

logger = logging.getLogger("main")

def parse_contacts(contact_str: str) -> Optional[str]:
    """
    Parse e-mail strings using regex.
    """
    # Mail regex for validating mail addresses
    regex = r'(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7},? *\b)+'

    contacts = contact_str.replace(";", ",")

    if not re.fullmatch(regex, contacts):
        logger.error("Error validating mail address: %s. Mail address is not valid.", contacts)
        return None

    return contacts

def collect_loose_nodes(pd_name: str, nodes: List[Node]) -> Optional[Dict[str, PolicyDomain]]:
    """
    Create a collection containing all nodes which have individual contacts defined
    instead of being part of a policy domain with a defined contact.
    """
    loose_nodes_collection: Dict[str, PolicyDomain] = {}

    for node in nodes:
        if node.contact:
            contacts = parse_contacts(node.contact)
            if not contacts:
                logger.warning("parse_contacts didn't return a valid contact string.") 
                continue

            if contacts not in loose_nodes_collection:
                loose_nodes_collection[contacts] = PolicyDomain([node], pd_name)
            else:
                loose_nodes_collection[contacts].nodes.append(node)

    for pd in loose_nodes_collection.values():
        pd.calculate_backup_summaries()

    return loose_nodes_collection

def send_mail(config: Dict[str, Any], mailer: Mailer,
              policy_domain: PolicyDomain, sender_addr: str,
              receiver_addr: str, reply_to: str, bcc: str,
              instance: str, time_string: str):
    """
    Create mail subject and call mailer to send mail.
    """
    if not policy_domain.has_client_schedules() and not policy_domain.has_vm_backups():
        logger.info("No backups in 24 hours detected for %s.", policy_domain.name)
    else:
        subject_template = Template(config["mail_subject_template"])

        logger.info("Parsing mail template for %s.", receiver_addr)
        subject = subject_template.substitute({
            "status": "OKAY" if not policy_domain.has_non_successful_schedules() else "WARN",
            "tsm_inst": instance,
            "pd_name": policy_domain.name,
            "time": time_string
        })

        mailer.send_to(policy_domain, sender_addr, receiver_addr, subject, reply_to, bcc)

def send_mail_reports(config: Dict[str, Any],
                      mailer: Mailer,
                      data: Dict[str, TSMData]):
    """
    Prepare and send mails using the StatusMailer class.
    """

    current_time = datetime.now()
    time_string = current_time.strftime("%d.%m.%Y %H:%M:%S")

    bcc = config["mail_bcc_addr"] if "mail_bcc_addr" in config \
        and config["mail_bcc_addr"] else ""
    reply_to = config["mail_replyto_addr"] if "mail_replyto_addr" in config \
        and config["mail_replyto_addr"] else ""

    logger.info("Preparing mail reports...")
    for inst in config["tsm_instances"]:
        if inst not in data:
            logger.error("Instance name not found in pickled data.")
            break

        # Nodes to be collected when policy domain has no contact specified
        loose_nodes: Optional[Dict[str, PolicyDomain]] = {}

        for policy_domain in data[inst].domains.values():
            if policy_domain.contact:
                contacts = parse_contacts(policy_domain.contact)
                if not contacts:
                    logger.warning("parse_contacts didn't return a "
                                   "valid contact string, skipping policy domain %s.",
                                    policy_domain.name)
                    continue

                send_mail(config, mailer, policy_domain, config["mail_from_addr"],
                          contacts, reply_to, bcc, inst, time_string)
            elif not loose_nodes:
                loose_nodes = collect_loose_nodes(policy_domain.name, policy_domain.nodes)

                if not loose_nodes:
                    logger.warning("No node has contact specified in "
                                   "PolicyDomain without contact information.")

        # Send mail reports for collected loose nodes
        if not loose_nodes:
            logger.info("No nodes in loose_nodes to process.")
            continue

        for contact, policy_domain in loose_nodes.items():
            send_mail(config, mailer, policy_domain, config["mail_from_addr"],
                      contact, reply_to, bcc, inst, time_string)

def get_password(config: Dict[str, Any]) -> str:
    """
    Try to read the password file, otherwise read it directly
    from user input using getpass.
    """
    if "tsm_password_file" in config:
        if os.path.isfile(config["tsm_password_file"]):
            with open(config["tsm_password_file"], "r", encoding="utf-8") as pwd_file:
                pwd = pwd_file.read()
        else:
            logger.error('Password file "%s" supplied in config does not exist.',
                         config["tsm_password_file"])
            sys.exit(1)
    else:
        pwd = getpass.getpass()

    return pwd

def load_config(path: str) -> Dict[str, Any]:
    """
    Load the configuration file.
    """
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as cfg_file:
            try:
                sys.stdout.write(f"Loaded config from {path}\n")
                return yaml.safe_load(cfg_file)
            except yaml.YAMLError as exc:
                sys.stderr.write(f'{exc}\n')
                sys.exit(1)
    else:
        sys.stderr.write(f"ERROR: {path} not found.\n")
        sys.exit(1)

def setup_logger(config: Dict[str, Any]):
    """
    Set up the logger, checking and setting log level and log formatting.
    Also configure rotating logs to preserve disk space.
    """
    log_levels = {
        LOG_LEVEL_DEBUG_STR: logging.DEBUG,
        LOG_LEVEL_INFO_STR: logging.INFO,
        LOG_LEVEL_WARN_STR: logging.WARN,
        LOG_LEVEL_ERROR_STR: logging.ERROR
    }

    log_level = None

    if "log_level" in config:
        if config["log_level"] in log_levels:
            log_level = log_levels[config["log_level"]]
        else:
            raise ValueError(f'ERROR: log_level "{config["log_level"]}" '
                              'not recognized. Accepted values: DEBUG, INFO, WARN, ERROR')
    else:
        sys.stdout.write("WARNING: log_level argument not supplied in config, defaulting to ERROR.\n")
        log_level = logging.ERROR

    logger.setLevel(log_level)

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s, %(module)s: %(message)s")
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)

    if "log_path" in config:
        if "log_rotate" in config:
            file_handler = logging.handlers.TimedRotatingFileHandler(
                config["log_path"],
                when="W0",
                interval=1,
                backupCount=0
            )
        else:
            file_handler = logging.FileHandler(config["log_path"])

        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

def export_to_html(config: Dict[str, Any], data: Dict[str, TSMData]):
    """
    Render and export all reports to HTML files which have been parsed from the TSM data. 
    """
    template = ReportTemplate(config["mail_template_path"])

    for inst in config["tsm_instances"]:
        if inst not in data:
            logger.error("Instance name not found in pickled data.")
            break

        for policy_domain in data[inst].domains.values():
            html_test_render = template.render(policy_domain)

            with open(f"{inst}_{policy_domain.name}_report.html", "w", encoding="utf-8") as file:
                file.write(html_test_render)

def collect_and_parse_instance(config: Dict[str, Any], inst: str, pwd: str) -> TSMData:
    """
    Collect and parse all data from a TSM server instance using the Collector class and
    parsing methods from TSMData class.
    """
    collector_config = CollectorConfig(config, inst, pwd)
    # Collect overall data from the environment
    nodes_and_domains = collect_nodes_and_domains(collector_config)
    vms_list = collect_vm_schedules(collector_config)

    # Collect logs for each node
    node_schedule_logs = collect_schedule_logs(collector_config, nodes_and_domains)
    client_backup_logs = collect_client_backup_results(collector_config, nodes_and_domains)

    data = TSMData()

    # Parse data
    data.parse_nodes(nodes_and_domains)
    data.parse_schedules_and_backup_results(node_schedule_logs, client_backup_logs)
    data.parse_vm_schedules(vms_list)

    return data

def main():
    """
    Main entrypoint.
    """
    data: Dict[str, TSMData] = {}
    pwd = ""

    argparser = argparse.ArgumentParser(
        prog="tsm_mail.py",
        description="TSM Mail generates and distributes HTML \
                     reports of an IBM TSM / ISP environment.")

    argparser.add_argument("-c", "--config", # Config file argument
                           metavar="PATH", help="path to config file", required=True)
    argparser.add_argument("-p", "--pickle", action="store", type=str,
                           metavar="PATH", help="the pickle argument determines if the \
                            fetched TSM reports should be saved to file for quicker \
                            loading times while debugging. \
                            NOTE: To fetch a new report, delete the pickle file or supply \
                            a different path to the argument")
    argparser.add_argument("-e", "--export", action="store_true",
                           help="create HTML files of generated reports")
    argparser.add_argument("--disable-mail-send", action="store_true",
                           help="disable actually sending the mails for debugging purposes")

    args = argparser.parse_args()

    config = load_config(args.config)
    setup_logger(config)
    pwd = get_password(config)

    mailer = StatusMailer(
        config["mail_server_host"],
        config["mail_server_port"],
        config["mail_template_path"],
        (config["mail_server_username"],
        config["mail_server_password"])
    )

    if args.pickle:
        if os.path.isfile(args.pickle):
            logger.info("Pickled data found in %s. Loading...", args.pickle)
            with open(args.pickle, "rb") as pickle_file:
                data = pickle.load(pickle_file)
        else:
            logger.warning("%s not found!", args.pickle)
    else:
        logger.info("No pickled data supplied, fetching from TSM.")

    if "tsm_instances" in config and not data:
        for inst in config["tsm_instances"]:
            data[inst] = collect_and_parse_instance(config, inst, pwd)

    if not args.disable_mail_send:
        send_mail_reports(config, mailer, data)

    if args.export:
        export_to_html(config, data)

    if args.pickle:
        logger.info("Pickling data to %s", args.pickle)
        with open(args.pickle, "wb") as pickle_file:
            pickle.dump(data, pickle_file)

if __name__ == "__main__":
    main()
