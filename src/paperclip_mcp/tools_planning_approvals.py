from __future__ import annotations

from .client import JsonObject, JsonValue, PaperclipClient, error_response
from .registry import ToolRegistrar
from .tools_common import patch_json, post_json


class PlanningTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_goals(self) -> JsonValue:
        """List goals in the configured company."""
        return await self._client.get(f"/companies/{self._company_id}/goals")

    async def get_goal(self, goal_id: str) -> JsonValue:
        """Get a goal by ID."""
        return await self._client.get(f"/goals/{goal_id}")

    async def create_goal(self, title: str, description: str = "") -> JsonValue:
        """Create a strategic goal with an optional Markdown description."""
        body: JsonObject = {"title": title}
        if description:
            body["description"] = description
        return await self._client.post(f"/companies/{self._company_id}/goals", body)

    async def update_goal(self, goal_id: str, title: str = "", description: str = "") -> JsonValue:
        """Update supplied title or description fields on a goal."""
        body: JsonObject = {}
        if title:
            body["title"] = title
        if description:
            body["description"] = description
        if not body:
            return error_response("No fields to update. Provide title or description.")
        return await self._client.patch(f"/goals/{goal_id}", body)

    async def delete_goal(self, goal_id: str) -> JsonValue:
        """Delete a goal."""
        return await self._client.delete(f"/goals/{goal_id}")

    async def list_projects(self, include_archived: bool = False) -> JsonValue:
        """List active projects, or include archived projects when requested."""
        params = {"includeArchived": "true"} if include_archived else None
        return await self._client.get(f"/companies/{self._company_id}/projects", params)

    async def get_project(self, project_id: str) -> JsonValue:
        """Get a project by UUID or unambiguous project shortname."""
        return await self._client.get(f"/projects/{project_id}")

    async def create_project(self, body_json: str) -> JsonValue:
        """Create a project; body_json can include goalIds, workspace, and runtime policy fields."""
        return await post_json(self._client, f"/companies/{self._company_id}/projects", body_json)

    async def update_project(self, project_id: str, body_json: str) -> JsonValue:
        """Partially update a project using a documented project JSON object."""
        return await patch_json(self._client, f"/projects/{project_id}", body_json)

    async def delete_project(self, project_id: str) -> JsonValue:
        """Delete a project."""
        return await self._client.delete(f"/projects/{project_id}")

    async def list_project_workspaces(self, project_id: str) -> JsonValue:
        """List execution workspaces attached to a project."""
        return await self._client.get(f"/projects/{project_id}/workspaces")

    async def create_project_workspace(self, project_id: str, body_json: str) -> JsonValue:
        """Create a project workspace from a documented workspace JSON object."""
        return await post_json(self._client, f"/projects/{project_id}/workspaces", body_json)

    async def update_project_workspace(
        self, project_id: str, workspace_id: str, body_json: str
    ) -> JsonValue:
        """Partially update a project workspace using a JSON object."""
        return await patch_json(
            self._client, f"/projects/{project_id}/workspaces/{workspace_id}", body_json
        )

    async def delete_project_workspace(self, project_id: str, workspace_id: str) -> JsonValue:
        """Delete a project workspace."""
        return await self._client.delete(f"/projects/{project_id}/workspaces/{workspace_id}")

    async def manage_workspace_runtime_service(
        self, project_id: str, workspace_id: str, action: str
    ) -> JsonValue:
        """Start, stop, or restart a workspace runtime service."""
        if action not in {"start", "stop", "restart"}:
            return error_response("Invalid action. Allowed: start, stop, restart.")
        return await self._client.post(
            f"/projects/{project_id}/workspaces/{workspace_id}/runtime-services/{action}"
        )


class ApprovalTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_approvals(self, status: str = "pending") -> JsonValue:
        """List company approval requests with a validated lifecycle status filter."""
        allowed = {"pending", "approved", "rejected", "revision_requested"}
        if status not in allowed:
            return error_response(f"Invalid status. Allowed: {', '.join(sorted(allowed))}.")
        return await self._client.get(
            f"/companies/{self._company_id}/approvals", {"status": status}
        )

    async def get_approval(self, approval_id: str) -> JsonValue:
        """Get one approval record with its redacted request payload."""
        return await self._client.get(f"/approvals/{approval_id}")

    async def create_approval(self, body_json: str) -> JsonValue:
        """Create an approval from a JSON object containing type, payload, and optional issueIds."""
        return await post_json(self._client, f"/companies/{self._company_id}/approvals", body_json)

    async def approve(self, approval_id: str, comment: str = "") -> JsonValue:
        """Approve a pending approval request with an optional note."""
        body = {"decisionNote": comment} if comment else {}
        return await self._client.post(f"/approvals/{approval_id}/approve", body)

    async def reject(self, approval_id: str, comment: str = "") -> JsonValue:
        """Reject a pending approval request with an optional note."""
        body = {"decisionNote": comment} if comment else {}
        return await self._client.post(f"/approvals/{approval_id}/reject", body)

    async def request_approval_revision(self, approval_id: str, comment: str) -> JsonValue:
        """Request a revision with the required feedback note."""
        if not comment.strip():
            return error_response("A comment is required when requesting a revision.")
        return await self._client.post(
            f"/approvals/{approval_id}/request-revision", {"decisionNote": comment}
        )

    async def list_approval_linked_issues(self, approval_id: str) -> JsonValue:
        """List issues linked to an approval request."""
        return await self._client.get(f"/approvals/{approval_id}/issues")

    async def list_approval_comments(self, approval_id: str) -> JsonValue:
        """List the review thread attached to an approval."""
        return await self._client.get(f"/approvals/{approval_id}/comments")

    async def comment_on_approval(self, approval_id: str, body: str) -> JsonValue:
        """Add a Markdown comment to an approval's review thread."""
        return await self._client.post(f"/approvals/{approval_id}/comments", {"body": body})

    async def resubmit_approval(self, approval_id: str, body_json: str = "{}") -> JsonValue:
        """Resubmit a revision-requested approval, optionally replacing its payload."""
        return await post_json(self._client, f"/approvals/{approval_id}/resubmit", body_json)


def register_planning_and_approval_tools(
    registrar: ToolRegistrar, client: PaperclipClient, company_id: str
) -> None:
    planning = PlanningTools(client, company_id)
    approvals = ApprovalTools(client, company_id)
    registrar.add(
        planning.list_goals,
        planning.get_goal,
        planning.create_goal,
        planning.update_goal,
        planning.delete_goal,
        planning.list_projects,
        planning.get_project,
        planning.create_project,
        planning.update_project,
        planning.delete_project,
        planning.list_project_workspaces,
        planning.create_project_workspace,
        planning.update_project_workspace,
        planning.delete_project_workspace,
        planning.manage_workspace_runtime_service,
        approvals.list_approvals,
        approvals.get_approval,
        approvals.create_approval,
        approvals.approve,
        approvals.reject,
        approvals.request_approval_revision,
        approvals.list_approval_linked_issues,
        approvals.list_approval_comments,
        approvals.comment_on_approval,
        approvals.resubmit_approval,
    )
