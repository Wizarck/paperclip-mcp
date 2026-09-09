from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Final, TypeAlias

from fastmcp import FastMCP

from .json_types import JsonValue

TOOL_CATEGORIES: Final[dict[str, str]] = {
    "list_issues": "issues",
    "get_issue": "issues",
    "create_issue": "issues",
    "update_issue": "issues",
    "checkout_issue": "issues",
    "release_issue": "issues",
    "comment_on_issue": "issues",
    "delete_issue": "issues",
    "get_issue_heartbeat_context": "issues",
    "get_issue_blocker_diagnostics": "issues",
    "get_issue_wake_diagnostics": "issues",
    "get_issue_subtree_diagnostics": "issues",
    "list_issue_comments": "issues",
    "get_issue_comment": "issues",
    "list_issue_activity": "issues",
    "list_issue_runs": "issues",
    "list_issue_interactions": "issues",
    "create_issue_interaction": "issues",
    "accept_issue_interaction": "issues",
    "reject_issue_interaction": "issues",
    "respond_to_issue_interaction": "issues",
    "withdraw_issue_interaction": "issues",
    "list_issue_documents": "issues",
    "get_issue_document": "issues",
    "upsert_issue_document": "issues",
    "lock_issue_document": "issues",
    "unlock_issue_document": "issues",
    "list_issue_document_revisions": "issues",
    "restore_issue_document_revision": "issues",
    "delete_issue_document": "issues",
    "list_document_annotations": "issues",
    "create_document_annotation": "issues",
    "reply_to_document_annotation": "issues",
    "resolve_document_annotation": "issues",
    "reopen_document_annotation": "issues",
    "list_issue_attachments": "issues",
    "upload_issue_attachment": "issues",
    "delete_issue_attachment": "issues",
    "list_issue_approval_links": "issues",
    "link_issue_approval": "issues",
    "unlink_issue_approval": "issues",
    "archive_issue_inbox": "issues",
    "unarchive_issue_inbox": "issues",
    "list_agents": "agents",
    "get_agent": "agents",
    "invoke_agent_heartbeat": "agents",
    "create_agent": "agents",
    "hire_agent": "agents",
    "update_agent": "agents",
    "update_agent_permissions": "agents",
    "pause_agent": "agents",
    "resume_agent": "agents",
    "terminate_agent": "agents",
    "delete_agent": "agents",
    "list_agent_keys": "agents",
    "create_agent_key": "agents",
    "revoke_agent_key": "agents",
    "wake_agent": "agents",
    "get_company_org": "agents",
    "list_adapter_models": "agents",
    "detect_adapter_model": "agents",
    "test_adapter_environment": "agents",
    "list_agent_skills": "agents",
    "sync_agent_skills": "agents",
    "get_agent_configuration": "agents",
    "list_agent_config_revisions": "agents",
    "get_agent_config_revision": "agents",
    "rollback_agent_config_revision": "agents",
    "list_company_agent_configurations": "agents",
    "update_agent_instructions_path": "agents",
    "get_agent_instructions_bundle": "agents",
    "update_agent_instructions_bundle": "agents",
    "get_agent_instructions_file": "agents",
    "put_agent_instructions_file": "agents",
    "delete_agent_instructions_file": "agents",
    "list_granted_secrets": "agents",
    "read_granted_secret_value": "agents",
    "list_goals": "goals",
    "get_goal": "goals",
    "create_goal": "goals",
    "update_goal": "goals",
    "delete_goal": "goals",
    "list_projects": "projects",
    "get_project": "projects",
    "create_project": "projects",
    "update_project": "projects",
    "delete_project": "projects",
    "list_project_workspaces": "projects",
    "create_project_workspace": "projects",
    "update_project_workspace": "projects",
    "delete_project_workspace": "projects",
    "manage_workspace_runtime_service": "projects",
    "list_approvals": "approvals",
    "get_approval": "approvals",
    "create_approval": "approvals",
    "approve": "approvals",
    "reject": "approvals",
    "request_approval_revision": "approvals",
    "list_approval_linked_issues": "approvals",
    "list_approval_comments": "approvals",
    "comment_on_approval": "approvals",
    "resubmit_approval": "approvals",
    "get_cost_summary": "costs",
    "get_cost_details": "costs",
    "get_cost_window_spend": "costs",
    "get_dashboard": "monitoring",
    "list_activity": "monitoring",
    "list_secret_providers": "secrets",
    "list_secrets": "secrets",
    "list_secret_catalog": "secrets",
    "create_secret": "secrets",
    "update_secret": "secrets",
    "rotate_secret": "secrets",
    "delete_secret": "secrets",
    "list_secret_proposals": "secrets",
    "approve_secret_proposal": "secrets",
    "reject_secret_proposal": "secrets",
    "list_my_secret_proposals": "secrets",
    "create_secret_proposal": "secrets",
    "withdraw_secret_proposal": "secrets",
    "list_routines": "routines",
    "get_routine": "routines",
    "create_routine": "routines",
    "update_routine": "routines",
    "delete_routine": "routines",
    "create_routine_trigger": "routines",
    "update_routine_trigger": "routines",
    "delete_routine_trigger": "routines",
    "rotate_routine_trigger_secret": "routines",
    "run_routine": "routines",
    "fire_public_routine_trigger": "routines",
    "list_routine_runs": "routines",
    "list_companies": "companies",
    "get_company": "companies",
    "create_company": "companies",
    "update_company": "companies",
    "update_company_branding": "companies",
    "upload_company_logo": "companies",
}

VALID_CATEGORIES: Final[frozenset[str]] = frozenset(TOOL_CATEGORIES.values())
ToolFunction: TypeAlias = Callable[..., Awaitable[JsonValue]]


class DisabledToolConfigurationError(ValueError):
    pass


def parse_disabled_tools(raw_value: str) -> frozenset[str]:
    tokens = frozenset(token.strip() for token in raw_value.split(",") if token.strip())
    unknown_tokens = tokens - set(TOOL_CATEGORIES) - VALID_CATEGORIES
    if unknown_tokens:
        categories = ", ".join(sorted(VALID_CATEGORIES))
        tool_names = ", ".join(sorted(TOOL_CATEGORIES))
        raise DisabledToolConfigurationError(
            f"Unknown PAPERCLIP_DISABLED_TOOLS token(s): {', '.join(sorted(unknown_tokens))}. "
            f"Valid categories: {categories}. Valid tool names: {tool_names}."
        )
    return tokens


def disabled_tool_names(raw_value: str) -> frozenset[str]:
    disabled_tokens = parse_disabled_tools(raw_value)
    return frozenset(
        name
        for name, category in TOOL_CATEGORIES.items()
        if name in disabled_tokens or category in disabled_tokens
    )


def enabled_tool_names(raw_value: str) -> frozenset[str]:
    return frozenset(TOOL_CATEGORIES) - disabled_tool_names(raw_value)


@dataclass(frozen=True, slots=True)
class ToolRegistrar:
    server: FastMCP
    disabled_names: frozenset[str]

    def add(self, *tools: ToolFunction) -> None:
        for tool in tools:
            tool_name = tool.__name__
            if tool_name not in TOOL_CATEGORIES:
                raise RuntimeError(f"Tool '{tool_name}' is absent from TOOL_CATEGORIES.")
            if tool_name not in self.disabled_names:
                self.server.tool()(tool)
