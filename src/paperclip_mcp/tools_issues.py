from __future__ import annotations

from .client import JsonObject, JsonValue, PaperclipClient, QueryParameters, error_response
from .registry import ToolRegistrar
from .tools_common import put_json


class IssueTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_issues(
        self,
        status: str = "todo,in_progress",
        assignee_agent_id: str = "",
        project_id: str = "",
        label: str = "",
        limit: int = 50,
    ) -> JsonValue:
        """List issues filtered by status, assignee, project, or label."""
        params: QueryParameters = {"status": status, "limit": max(1, min(limit, 200))}
        if assignee_agent_id:
            params["assigneeAgentId"] = assignee_agent_id
        if project_id:
            params["projectId"] = project_id
        if label:
            params["labelId"] = label
        return await self._client.get(f"/companies/{self._company_id}/issues", params)

    async def get_issue(self, issue_id: str) -> JsonValue:
        """Get a full issue by UUID or human-readable identifier such as PAP-42."""
        return await self._client.get(f"/issues/{issue_id}")

    async def create_issue(
        self,
        title: str,
        description: str = "",
        assignee_agent_id: str = "",
        project_id: str = "",
        parent_issue_id: str = "",
        priority: str = "medium",
    ) -> JsonValue:
        """Create an issue and optionally place it in a project, hierarchy, or agent queue."""
        body: JsonObject = {"title": title, "priority": priority}
        if description:
            body["description"] = description
        if assignee_agent_id:
            body["assigneeAgentId"] = assignee_agent_id
        if project_id:
            body["projectId"] = project_id
        if parent_issue_id:
            body["parentIssueId"] = parent_issue_id
        return await self._client.post(f"/companies/{self._company_id}/issues", body)

    async def update_issue(
        self,
        issue_id: str,
        title: str = "",
        description: str = "",
        status: str = "",
        assignee_agent_id: str = "",
        priority: str = "",
    ) -> JsonValue:
        """Update supplied issue fields while preserving all fields left empty."""
        body: JsonObject = {}
        if title:
            body["title"] = title
        if description:
            body["description"] = description
        if status:
            if status not in {
                "backlog",
                "todo",
                "in_progress",
                "blocked",
                "in_review",
                "done",
                "cancelled",
            }:
                return error_response(
                    "Invalid status. Allowed: backlog, todo, in_progress, blocked, "
                    "in_review, done, cancelled."
                )
            body["status"] = status
        if assignee_agent_id:
            body["assigneeAgentId"] = assignee_agent_id
        if priority:
            if priority not in {"critical", "urgent", "high", "medium", "low"}:
                return error_response(
                    "Invalid priority. Allowed: critical, urgent, high, medium, low."
                )
            body["priority"] = priority
        if not body:
            return error_response(
                "No fields to update. Provide title, description, status, assignee_agent_id, "
                "or priority."
            )
        return await self._client.patch(f"/issues/{issue_id}", body)

    async def checkout_issue(
        self,
        issue_id: str,
        agent_id: str = "",
        expected_statuses: str = "todo,backlog,blocked,in_review",
    ) -> JsonValue:
        """Atomically assign an issue to the authenticated agent and mark it in progress."""
        statuses: list[JsonValue] = [
            status.strip() for status in expected_statuses.split(",") if status.strip()
        ]
        if not agent_id:
            return error_response("agent_id is required by Paperclip checkout.")
        if not statuses:
            return error_response("expected_statuses must include at least one status.")
        return await self._client.post(
            f"/issues/{issue_id}/checkout",
            {"agentId": agent_id, "expectedStatuses": statuses},
        )

    async def release_issue(self, issue_id: str) -> JsonValue:
        """Release an agent checkout and return the issue to the todo state."""
        return await self._client.post(f"/issues/{issue_id}/release")

    async def comment_on_issue(self, issue_id: str, body: str, reopen: bool = False) -> JsonValue:
        """Add a Markdown comment; optionally reopen a completed or cancelled issue."""
        payload: JsonObject = {"body": body}
        if reopen:
            payload["reopen"] = True
        return await self._client.post(f"/issues/{issue_id}/comments", payload)

    async def delete_issue(self, issue_id: str) -> JsonValue:
        """Permanently delete an issue."""
        return await self._client.delete(f"/issues/{issue_id}")

    async def get_issue_heartbeat_context(self, issue_id: str) -> JsonValue:
        """Get the compact execution context used for an agent wakeup on an issue."""
        return await self._client.get(f"/issues/{issue_id}/heartbeat-context")

    async def get_issue_blocker_diagnostics(self, issue_id: str) -> JsonValue:
        """Diagnose dependency readiness and stale blocker holds for one issue."""
        return await self._client.get(f"/issues/{issue_id}/diagnostics/blockers")

    async def get_issue_wake_diagnostics(self, issue_id: str) -> JsonValue:
        """Diagnose why an issue assignee was or was not woken."""
        return await self._client.get(f"/issues/{issue_id}/diagnostics/wakes")

    async def get_issue_subtree_diagnostics(self, issue_id: str) -> JsonValue:
        """Diagnose child, blocker, and wake edges across an issue subtree."""
        return await self._client.get(f"/issues/{issue_id}/diagnostics/subtree")

    async def list_issue_comments(
        self, issue_id: str, after_comment_id: str = "", order: str = "asc", limit: int = 100
    ) -> JsonValue:
        """List issue comments with optional cursor, sort order, and result limit."""
        params: QueryParameters = {"order": order, "limit": max(1, min(limit, 500))}
        if after_comment_id:
            params["afterCommentId"] = after_comment_id
        return await self._client.get(f"/issues/{issue_id}/comments", params)

    async def get_issue_comment(self, issue_id: str, comment_id: str) -> JsonValue:
        """Get one comment from an issue discussion."""
        return await self._client.get(f"/issues/{issue_id}/comments/{comment_id}")

    async def list_issue_activity(self, issue_id: str) -> JsonValue:
        """List audit activity for one issue."""
        return await self._client.get(f"/issues/{issue_id}/activity")

    async def list_issue_runs(self, issue_id: str) -> JsonValue:
        """List heartbeat runs associated with an issue."""
        return await self._client.get(f"/issues/{issue_id}/runs")

    async def upsert_issue_document(self, issue_id: str, key: str, body_json: str) -> JsonValue:
        """Create a document or add a revision using a JSON object documented by Paperclip."""
        return await put_json(self._client, f"/issues/{issue_id}/documents/{key}", body_json)


def register_issue_tools(
    registrar: ToolRegistrar, client: PaperclipClient, company_id: str
) -> None:
    tools = IssueTools(client, company_id)
    registrar.add(
        tools.list_issues,
        tools.get_issue,
        tools.create_issue,
        tools.update_issue,
        tools.checkout_issue,
        tools.release_issue,
        tools.comment_on_issue,
        tools.delete_issue,
        tools.get_issue_heartbeat_context,
        tools.get_issue_blocker_diagnostics,
        tools.get_issue_wake_diagnostics,
        tools.get_issue_subtree_diagnostics,
        tools.list_issue_comments,
        tools.get_issue_comment,
        tools.list_issue_activity,
        tools.list_issue_runs,
        tools.upsert_issue_document,
    )
