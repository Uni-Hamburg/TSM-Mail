"""
Contains the ReportTemplate class which holds all inforamtion and handling
regarding the report mail HTML templates.
"""
import os

from jinja2 import Environment, FileSystemLoader

from parsing.schedule_status import ScheduleStatusEnum
from parsing.policy_domain import PolicyDomain

class ReportTemplate():
    """
    ReportTemplate handles the creation and rendering of the report
    mail template.
    """
    def __init__(self, template_path: str):
        # Load jinja2 mail HTML template
        self.__template_file_loader = FileSystemLoader(os.path.dirname(template_path))
        self.__template_env = Environment(loader=self.__template_file_loader,
                                          extensions=['jinja2.ext.do'])
        self.__template = self.__template_env.get_template(os.path.basename(template_path))
        self.__template.globals["ScheduleStatusEnum"] = ScheduleStatusEnum
    
    def render(self, policy_domain: PolicyDomain) -> str:
        """
        Renders the report template and returns a HTML string.
        """
        return self.__template.render(pd=policy_domain)
