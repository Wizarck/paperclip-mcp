#!/usr/bin/env python3
"""
paperclip-mcp — MCP server for the Paperclip AI agent orchestration platform.

Exposes Paperclip's REST API as MCP tools so that AI assistants can manage
issues, agents, goals, approvals, costs, and activity via natural language.

Documentation: https://github.com/paperclipai/paperclip
MCP spec:      https://modelcontextprotocol.io

Configuration (environment variables):
    PAPERCLIP_API_KEY      Required. Board API key (prefix: pcp_board_) — generate
                           via CLI auth challenge: POST /api/cli-auth/challenges
                           with {"command":"login"}, approve the returned
                           approvalUrl in a browser, then use boardApiToken.
    PAPERCLIP_COMPANY_ID   Required. Company UUID shown in the Paperclip UI URL
                           when viewing your company: /companies/{uuid}.
    PAPERCLIP_BASE_URL     Optional. Default: http://localhost:3100/api
    PAPERCLIP_SERVER_NAME  Optional. MCP server name reported to the client.
                           Set a distinct value per instance when running
                           multiple servers for different companies
                           (e.g. "paperclip-acme", "paperclip-school").
                           Default: "paperclip"
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastmcp import FastMCP

# ── Configuration ──────────────────────────────────────────────────────────────

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can be set by the shell

BASE_URL: str     = os.environ.get("PAPERCLIP_BASE_URL", "http://localhost:3100/api").rstrip("/")
API_KEY: str      = os.environ.get("PAPERCLIP_API_KEY", "")
COMPANY: str      = os.environ.get("PAPERCLIP_COMPANY_ID", "")
SERVER_NAME: str  = os.environ.get("PAPERCLIP_SERVER_NAME", "paperclip")

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] paperclip-mcp %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stderr,
)
log = logging.getLogger(__name__)

# ── HTTP client ────────────────────────────────────────────────────────────────

_HTTP_TIMEOUT = 30  # seconds


def _headers() -> dict[str, str]:
    """Build per-request headers.  Omit X-Paperclip-Run-Id — a fake UUID causes
    FK violations against heartbeat_runs when the API logs activity."""
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _err(message: str, status: int | None = None) -> dict[str, Any]:
    """Return a structured error payload that signals isError to the MCP client."""
    payload: dict[str, Any] = {"isError": True, "message": message}
    if status is not None:
        payload["status"] = status
    return payload


async def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    url = f"{BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.request(
                method,
                url,
                headers=_headers(),
                params=params,
                json=body,
            )
            # 409 Conflict on checkout: another agent owns the issue — do not retry.
            if r.status_code == 409:
                return _err(
                    "Conflict (409): resource is already checked out or owned by another agent. "
                    "Do not retry this request.",
                    status=409,
                )
            r.raise_for_status()
            # 204 No Content
            if r.status_code == 204 or not r.content:
                return {"ok": True}
            return r.json()
    except httpx.HTTPStatusError as exc:
        return _err(
            f"HTTP {exc.response.status_code} from Paperclip API: {exc.response.text[:400]}",
            status=exc.response.status_code,
        )
    except httpx.RequestError as exc:
        return _err(
            f"Could not reach Paperclip at {BASE_URL}. "
            f"Is the server running? Error: {exc}"
        )


async def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    return await _request("GET", path, params=params)


async def _post(path: str, body: dict[str, Any] | None = None) -> Any:
    return await _request("POST", path, body=body)


async def _patch(path: str, body: dict[str, Any]) -> Any:
    return await _request("PATCH", path, body=body)


async def _delete(path: str) -> Any:
    return await _request("DELETE", path)


# ── Startup validation ─────────────────────────────────────────────────────────

def _validate_config() -> None:
    """Fail fast with actionable error messages if required env vars are missing."""
    missing = [k for k, v in {
        "PAPERCLIP_API_KEY": API_KEY,
        "PAPERCLIP_COMPANY_ID": COMPANY,
    }.items() if not v]
    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        log.error(
            "Copy .env.example to .env, fill in the values, then:\n"
            "  source .env && python -m paperclip_mcp\n"
            "Or set them in your shell before starting the server."
        )
        sys.exit(1)


@asynccontextmanager
async def _lifespan(_server: FastMCP):  # type: ignore[type-arg]
    _validate_config()
    log.info("paperclip-mcp started — base: %s | company: %s", BASE_URL, COMPANY)
    yield
    log.info("paperclip-mcp stopped.")


# ── MCP Server ─────────────────────────────────────────────────────────────────

mcp = FastMCP(
    name=SERVER_NAME,
    instructions=(
        "Manage a Paperclip AI agent orchestration platform. "
        "Use these tools to create and track issues (tasks), inspect agents, "
        "set goals, handle approvals, and monitor costs. "
        "All operations target a single Paperclip company configured via "
        "PAPERCLIP_COMPANY_ID."
    ),
    lifespan=_lifespan,
)


# ── ISSUES ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_issues(
    status: str = "todo,in_progress",
    assignee_agent_id: str = "",
    project_id: str = "",
    label: str = "",
    limit: int = 50,
) -> Any:
    """List issues (tasks) in the active company.

    Args:
        status: Comma-separated issue statuses to include.
                Allowed values: todo, in_progress, blocked, done, cancelled.
                Default: "todo,in_progress"
        assignee_agent_id: UUID of the agent to filter by. Leave empty for all agents.
        project_id: UUID of the project to filter by. Leave empty for all projects.
        label: Label name to filter by. Leave empty to skip label filtering.
        limit: Maximum number of results to return (1–200). Default: 50.
    """
    params: dict[str, Any] = {"status": status, "limit": max(1, min(limit, 200))}
    if assignee_agent_id:
        params["assigneeAgentId"] = assignee_agent_id
    if project_id:
        params["projectId"] = project_id
    if label:
        params["label"] = label
    return await _get(f"/companies/{COMPANY}/issues", params)


@mcp.tool()
async def get_issue(issue_id: str) -> Any:
    """Get the full details of a single issue.

    Args:
        issue_id: Issue UUID or human-readable identifier (e.g. "CY-42").
    """
    return await _get(f"/issues/{issue_id}")


@mcp.tool()
async def create_issue(
    title: str,
    description: str = "",
    assignee_agent_id: str = "",
    project_id: str = "",
    parent_issue_id: str = "",
    priority: str = "medium",
) -> Any:
    """Create a new issue (task) and optionally assign it to an agent.

    Use this to delegate work to agents, create subtasks, or track action items.

    Args:
        title: Short, imperative task title (e.g. "Search cheese suppliers in Barcelona").
        description: Full instructions or context for the agent (Markdown supported).
        assignee_agent_id: UUID of the agent to assign. Leave empty to leave unassigned.
        project_id: UUID of the project this issue belongs to. Leave empty for no project.
        parent_issue_id: UUID of the parent issue when creating a subtask. Leave empty for top-level.
        priority: Task priority — urgent, high, medium, or low. Default: medium.
    """
    body: dict[str, Any] = {"title": title, "priority": priority}
    if description:
        body["description"] = description
    if assignee_agent_id:
        body["assigneeAgentId"] = assignee_agent_id
    if project_id:
        body["projectId"] = project_id
    if parent_issue_id:
        body["parentIssueId"] = parent_issue_id
    return await _post(f"/companies/{COMPANY}/issues", body)


@mcp.tool()
async def update_issue(
    issue_id: str,
    title: str = "",
    description: str = "",
    status: str = "",
    assignee_agent_id: str = "",
    priority: str = "",
) -> Any:
    """Update an existing issue. Only fields you provide are changed.

    Args:
        issue_id: Issue UUID or identifier (e.g. "CY-42").
        title: New title. Leave empty to keep current value.
        description: New description (Markdown). Leave empty to keep current.
        status: New status — todo, in_progress, blocked, done, or cancelled.
                Leave empty to keep current.
        assignee_agent_id: New agent UUID. Leave empty to keep current assignee.
        priority: New priority — urgent, high, medium, or low. Leave empty to keep current.
    """
    body: dict[str, Any] = {}
    if title:
        body["title"] = title
    if description:
        body["description"] = description
    if status:
        if status not in {"todo", "in_progress", "blocked", "done", "cancelled"}:
            return _err(f"Invalid status '{status}'. Allowed: todo, in_progress, blocked, done, cancelled.")
        body["status"] = status
    if assignee_agent_id:
        body["assigneeAgentId"] = assignee_agent_id
    if priority:
        if priority not in {"urgent", "high", "medium", "low"}:
            return _err(f"Invalid priority '{priority}'. Allowed: urgent, high, medium, low.")
        body["priority"] = priority
    if not body:
        return _err("No fields to update. Provide at least one of: title, description, status, assignee_agent_id, priority.")
    return await _patch(f"/issues/{issue_id}", body)


@mcp.tool()
async def checkout_issue(issue_id: str) -> Any:
    """Atomically assign an issue to the current agent and mark it in_progress.

    A 409 Conflict response means another agent already owns this issue — do NOT retry.
    Use release_issue to undo a checkout.

    Args:
        issue_id: Issue UUID or identifier to check out.
    """
    return await _post(f"/issues/{issue_id}/checkout")


@mcp.tool()
async def release_issue(issue_id: str) -> Any:
    """Release an issue: unassign it and revert it to its previous state.

    This is the inverse of checkout_issue. Use when an agent cannot complete a task
    and it should be returned to the queue.

    Args:
        issue_id: Issue UUID or identifier to release.
    """
    return await _post(f"/issues/{issue_id}/release")


@mcp.tool()
async def comment_on_issue(
    issue_id: str,
    body: str,
    reopen: bool = False,
) -> Any:
    """Add a comment to an issue (supports Markdown).

    Args:
        issue_id: Issue UUID or identifier.
        body: Comment text. Markdown is supported.
        reopen: Set to true to reopen the issue when posting this comment.
                Only effective if the issue is currently closed.
    """
    payload: dict[str, Any] = {"body": body}
    if reopen:
        payload["reopen"] = True
    return await _post(f"/issues/{issue_id}/comments", payload)


@mcp.tool()
async def delete_issue(issue_id: str) -> Any:
    """Permanently delete an issue. This action cannot be undone.

    Args:
        issue_id: Issue UUID or identifier to delete.
    """
    return await _delete(f"/issues/{issue_id}")


# ── AGENTS ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_agents() -> Any:
    """List all agents in the active company with their name, role, status, and config."""
    return await _get(f"/companies/{COMPANY}/agents")


@mcp.tool()
async def get_agent(agent_id: str = "me") -> Any:
    """Get details for a specific agent, or the currently authenticated agent.

    Args:
        agent_id: Agent UUID, or the literal string "me" to get the current agent identity.
                  Default: "me"
    """
    path = "/agents/me" if agent_id.strip().lower() == "me" else f"/agents/{agent_id}"
    return await _get(path)


@mcp.tool()
async def invoke_agent_heartbeat(agent_id: str) -> Any:
    """Manually trigger an immediate heartbeat (work cycle) for an agent.

    Use this to wake an idle agent, force it to pick up new assignments,
    or run it outside its normal schedule.

    Args:
        agent_id: UUID of the agent to trigger.
    """
    return await _post(f"/agents/{agent_id}/heartbeat/invoke")


# ── GOALS ──────────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_goals() -> Any:
    """List all strategic goals and projects for the active company."""
    return await _get(f"/companies/{COMPANY}/goals")


@mcp.tool()
async def create_goal(title: str, description: str = "") -> Any:
    """Create a new strategic goal for the active company.

    Goals provide high-level direction to agents. They appear in agent context
    so agents can align their work accordingly.

    Args:
        title: Goal title (e.g. "Reach 300 packs/month in sales by June 2026").
        description: Extended context, success criteria, and constraints (Markdown supported).
    """
    body: dict[str, Any] = {"title": title}
    if description:
        body["description"] = description
    return await _post(f"/companies/{COMPANY}/goals", body)


@mcp.tool()
async def update_goal(
    goal_id: str,
    title: str = "",
    description: str = "",
) -> Any:
    """Update an existing goal's title or description.

    Args:
        goal_id: Goal UUID.
        title: New title. Leave empty to keep current.
        description: New description. Leave empty to keep current.
    """
    body: dict[str, Any] = {}
    if title:
        body["title"] = title
    if description:
        body["description"] = description
    if not body:
        return _err("No fields to update. Provide at least one of: title, description.")
    return await _patch(f"/goals/{goal_id}", body)


# ── APPROVALS ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_approvals(status: str = "pending") -> Any:
    """List approval requests in the active company.

    Args:
        status: Filter by status. Allowed values:
                pending, approved, rejected, revision_requested.
                Default: "pending"
    """
    allowed = {"pending", "approved", "rejected", "revision_requested"}
    if status not in allowed:
        return _err(f"Invalid status '{status}'. Allowed: {', '.join(sorted(allowed))}.")
    return await _get(f"/companies/{COMPANY}/approvals", {"status": status})


@mcp.tool()
async def approve(approval_id: str, comment: str = "") -> Any:
    """Approve a pending approval request.

    Args:
        approval_id: Approval UUID.
        comment: Optional approval note to attach (e.g. conditions, context).
    """
    body: dict[str, Any] = {}
    if comment:
        body["comment"] = comment
    return await _post(f"/approvals/{approval_id}/approve", body)


@mcp.tool()
async def reject(approval_id: str, comment: str = "") -> Any:
    """Reject a pending approval request.

    Args:
        approval_id: Approval UUID.
        comment: Reason for rejection — strongly recommended so the agent understands why.
    """
    body: dict[str, Any] = {}
    if comment:
        body["comment"] = comment
    return await _post(f"/approvals/{approval_id}/reject", body)


@mcp.tool()
async def request_approval_revision(approval_id: str, comment: str) -> Any:
    """Request a revision on a pending approval without fully rejecting it.

    The submitting agent will receive the comment and can resubmit.

    Args:
        approval_id: Approval UUID.
        comment: Required. Specific feedback describing what must change before approval.
    """
    if not comment.strip():
        return _err("A comment is required when requesting a revision.")
    return await _post(f"/approvals/{approval_id}/request-revision", {"comment": comment})


# ── COSTS & MONITORING ─────────────────────────────────────────────────────────

@mcp.tool()
async def get_cost_summary() -> Any:
    """Get aggregate token usage and spend for the active company this billing period.

    Returns total spend, remaining budget, and a per-agent cost breakdown.
    Use this to monitor AI spend and detect runaway agents.
    """
    return await _get(f"/companies/{COMPANY}/costs/summary")


@mcp.tool()
async def get_dashboard() -> Any:
    """Get a high-level health summary for the active company.

    Returns: agent count, open/in-progress/blocked issue counts, stale tasks,
    recent activity digest, and current-period cost totals.
    """
    return await _get(f"/companies/{COMPANY}/dashboard")


@mcp.tool()
async def list_activity(
    agent_id: str = "",
    limit: int = 20,
) -> Any:
    """Retrieve the audit trail of recent actions in the active company.

    Args:
        agent_id: Filter to a specific agent UUID. Leave empty for all agents.
        limit: Maximum number of entries to return (1–100). Default: 20.
    """
    params: dict[str, Any] = {"limit": max(1, min(limit, 100))}
    if agent_id:
        params["agentId"] = agent_id
    return await _get(f"/companies/{COMPANY}/activity", params)


# ── ENTRY POINT ────────────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point — invoked via `paperclip-mcp` or `python -m paperclip_mcp`."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="paperclip-mcp",
        description="MCP server for the Paperclip AI agent orchestration platform.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address. Use 0.0.0.0 only in trusted local networks.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9011,
        help="Bind port.",
    )
    parser.add_argument(
        "--transport",
        default="streamable-http",
        choices=["streamable-http", "sse", "stdio"],
        help=(
            "MCP transport protocol. "
            "'streamable-http' for Claude Code / mcp-proxy; "
            "'stdio' for Claude Desktop."
        ),
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
