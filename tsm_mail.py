#!/usr/bin/env python

"""
tsm_mail.py is the main entrypoint to the tsm mail program
"""

import getpass
import re
import os
import sys
import pickle
import logging
import logging.handlers
import json
import argparse
from string import Template
from typing import Dict, List, Any
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from parsing.helper import check_non_successful_schedules

from parsing.tsm_data import TSMData
from parsing.node import Node
from parsing.policy_domain import PolicyDomain
from parsing.schedule_status import ScheduleStatusEnum
from parsing.constants import LOG_LEVEL_DEBUG_STR, LOG_LEVEL_ERROR_STR, LOG_LEVEL_INFO_STR, \
    LOG_LEVEL_WARN_STR

from collector import Collector

from mailer.status_mailer import StatusMailer

logger = logging.getLogger("main")

def parse_contacts(contact_str: str) -> str:
    # Mail regex for validating mail addresses
    regex = r'(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7},? *\b)+'

    contacts = contact_str.replace(";", ",")

    if not re.fullmatch(regex, contacts):
        logger.error(f"Error validating mail address: {contacts}. Mail address is not valid.")
        return None

    return contacts

def collect_loose_nodes(pd_name: str, nodes: List[Node]) -> Dict[str, PolicyDomain]:
    loose_nodes_collection: Dict[str, PolicyDomain] = {}

    for node in nodes:
        if node.contact != "":
            contacts = parse_contacts(node.contact)
            if contacts not in loose_nodes_collection:
                loose_nodes_collection[contacts] = PolicyDomain([node], pd_name)
            else:
                loose_nodes_collection[contacts].nodes.append(node)

            loose_nodes_collection[contacts].client_backup_summary += node.backupresult

            # Check if node has any client backups done
            if node.backupresult.inspected > 0:
                loose_nodes_collection[contacts].has_client_backups = True

            # Also check if any node has any VM backups
            if len(node.vm_results) > 0:
                loose_nodes_collection[contacts].has_vm_backups = True

            # Check if node has any failed schedules
            loose_nodes_collection[contacts].has_non_successful_schedules = \
                check_non_successful_schedules(loose_nodes_collection[contacts], node)

    return loose_nodes_collection

def send_mail(config: Dict[str, Any], mailer: StatusMailer,
              policy_domain: PolicyDomain, sender_addr: str,
              receiver_addr: str, reply_to: str, bcc: str,
              instance: str, time_string: str):
    if not policy_domain.has_client_backups and not policy_domain.has_vm_backups:
        logger.info(f"No backups in 24 hours detected for {policy_domain.name}.")
    else:
        subject_template = Template(config["mail_subject_template"])

        logger.info(f"Parsing mail template for {receiver_addr}.")
        subject = subject_template.substitute({
            "status": "OKAY" if not policy_domain.has_non_successful_schedules else "WARN",
            "tsm_inst": instance,
            "pd_name": policy_domain.name,
            "time": time_string
        })

        mailer.send_to(policy_domain, sender_addr, receiver_addr, subject, reply_to, bcc)

def send_mail_reports(config: Dict[str, Any],
                      data: Dict[str, TSMData]):
    mailer = StatusMailer(config["mail_server_host"],
                          config["mail_server_port"],
                          config["mail_template_path"])

    current_time = datetime.now()
    time_string = current_time.strftime("%d.%m.%Y %H:%M:%S")

    bcc = config["mail_bcc_addr"] if "mail_bcc_addr" in config \
        and config["mail_bcc_addr"] != "" else ""
    reply_to = config["mail_replyto_addr"] if "mail_replyto_addr" in config \
        and config["mail_replyto_addr"] != "" else ""

    logger.info("Preparing mail reports...")
    for inst in config["tsm_instances"]:
        if inst not in data:
            logger.error("Instance name not found in pickled data.")
            break

        # Nodes to be collected when policy domain has no contact specified
        loose_nodes: Dict[str, PolicyDomain] = {}

        for policy_domain in data[inst].domains.values():
            if policy_domain.contact != "":
                contacts = parse_contacts(policy_domain.contact)
                send_mail(config, mailer, policy_domain, config["mail_from_addr"],
                          contacts, reply_to, bcc, inst, time_string)
            elif not loose_nodes:
                loose_nodes = collect_loose_nodes(policy_domain.name, policy_domain.nodes)

                if not loose_nodes:
                    logger.warning("No node has contact specified in \
                                    PolicyDomain without contact information.")

        # Send mail reports for collected loose nodes
        for contact, policy_domain in loose_nodes.items():
            send_mail(config, mailer, policy_domain, config["mail_from_addr"],
                      contact, reply_to, bcc, inst, time_string)

def get_password(config: Dict[str, Any]) -> str:
    if config["tsm_password_file"] != "":
        if os.path.isfile(config["tsm_password_file"]):
            with open(config["tsm_password_file"], "r") as pwd_file:
                pwd = pwd_file.read()
        else:
            logger.error(f'Password file "{config["tsm_password_file"]}" \
                          supplied in config does not exist.')
            sys.exit(1)
    else:
        pwd = getpass.getpass()

    return pwd

def load_config(path: str) -> Dict[str, Any]:
    if os.path.isfile(path):
        with open(path, "r") as cfg_file:
            print("Loaded config from config.json")
            return json.load(cfg_file)
    else:
        print("ERROR: No config.json, file missing.")
        sys.exit(1)

def setup_logger(config: Dict[str, Any]):
    logger = logging.getLogger("main")

    log_level = None

    if "log_level" in config:
        if config["log_level"].upper() == LOG_LEVEL_DEBUG_STR:
            log_level = logging.DEBUG
        elif config["log_level"].upper() == LOG_LEVEL_INFO_STR:
            log_level = logging.INFO
        elif config["log_level"].upper() == LOG_LEVEL_WARN_STR:
            log_level = logging.WARN
        elif config["log_level"].upper() == LOG_LEVEL_ERROR_STR:
            log_level = logging.ERROR
        else:
            raise ValueError(f'ERROR: log_level "{config["log_level"]}" \
                              not recognized. Accepted values: DEBUG, INFO, WARN, ERROR')
    else:
        print("WARNING: log_level argument not supplied in config, defaulting to ERROR.")
        log_level = logging.ERROR

    logger.setLevel(log_level)

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s, %(module)s: %(message)s")
    format_handler = logging.StreamHandler()
    format_handler.setLevel(log_level)
    format_handler.setFormatter(formatter)

    logger.addHandler(format_handler)

    if "log_path" in config:
        if config["log_rotate"]:
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
    template_file_loader = FileSystemLoader(os.path.dirname(config["mail_template_path"]))
    template_env = Environment(loader=template_file_loader, extensions=['jinja2.ext.do'])

    template = template_env.get_template(os.path.basename(config["mail_template_path"]))
    template.globals["ScheduleStatusEnum"] = ScheduleStatusEnum

    for inst in config["tsm_instances"]:
        if inst not in data:
            logger.error("Instance name not found in pickled data.")
            break

        for policy_domain in data[inst].domains.values():
            html_test_render = template.render(pd=policy_domain)

            with open(f"{inst}_{policy_domain.name}_report.html", "w") as file:
                file.write(html_test_render)

def collect_and_parse_instance(config: Dict[str, Any], inst: str, pwd: str):
    collector = Collector(config, inst, pwd)
    # Collect overall data from the environment
    nodes_and_domains = collector.collect_nodes_and_domains()
    vms_list = collector.collect_vm_schedules()

    # Collect logs for each node
    node_schedule_logs = collector.collect_schedule_logs(nodes_and_domains)
    client_backup_logs = collector.collect_client_backup_results(nodes_and_domains)

    data = TSMData()

    # Parse data
    data.parse_nodes(nodes_and_domains)
    data.parse_schedules_and_backup_results(node_schedule_logs, client_backup_logs)
    data.parse_vm_schedules(vms_list)

    return data

def main():
    data: Dict[str, TSMData] = {}
    pwd = ""

    argparser = argparse.ArgumentParser(
        prog="tsm_mail.py",
        description="TSM Mail generates and distributes HTML \
                     reports of an IBM TSM / ISP environment.")

    argparser.add_argument("-c", "--config", # Config file argument
                           metavar="PATH", help="path to config.json file", required=True)
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

    if args.pickle:
        if os.path.isfile(args.pickle):
            logger.info(f"Pickled data found in {args.pickle}. Loading...")
            data = pickle.load(open(args.pickle, "rb"))
        else:
            logger.warning(f"{args.pickle} not found!")
    else:
        logger.info("No pickled data supplied, fetching from TSM.")

    if config["tsm_instances"] is not None and not data:
        for inst in config["tsm_instances"]:
            data[inst] = collect_and_parse_instance(config, inst, pwd)

    if not args.disable_mail_send:
        send_mail_reports(config, data)

    if args.export:
        export_to_html(config, data)

    if args.pickle:
        logger.info(f"Pickling data to {args.pickle}")
        pickle.dump(data, open(args.pickle, "wb"))

if __name__ == "__main__":
    main()
