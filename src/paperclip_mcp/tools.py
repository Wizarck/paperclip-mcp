from __future__ import annotations

from .client import PaperclipClient
from .registry import ToolRegistrar
from .tools_agent_configuration import register_agent_configuration_tools
from .tools_agents import register_agent_tools
from .tools_companies_costs import register_company_cost_tools
from .tools_issue_documents import register_issue_document_tools
from .tools_issue_workflow import register_issue_workflow_tools
from .tools_issues import register_issue_tools
from .tools_planning_approvals import register_planning_and_approval_tools
from .tools_routines_secrets import register_routine_and_secret_tools


def register_all_tools(registrar: ToolRegistrar, client: PaperclipClient, company_id: str) -> None:
    register_issue_tools(registrar, client, company_id)
    register_issue_document_tools(registrar, client)
    register_issue_workflow_tools(registrar, client, company_id)
    register_agent_tools(registrar, client, company_id)
    register_agent_configuration_tools(registrar, client, company_id)
    register_planning_and_approval_tools(registrar, client, company_id)
    register_routine_and_secret_tools(registrar, client, company_id)
    register_company_cost_tools(registrar, client, company_id)
