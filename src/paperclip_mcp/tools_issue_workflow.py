from __future__ import annotations

from .client import JsonValue, PaperclipClient
from .registry import ToolRegistrar
from .tools_common import post_json


class IssueWorkflowTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_issue_interactions(self, issue_id: str) -> JsonValue:
        """List structured decision and question cards attached to an issue."""
        return await self._client.get(f"/issues/{issue_id}/interactions")

    async def create_issue_interaction(self, issue_id: str, body_json: str) -> JsonValue:
        """Create a structured interaction; body_json supports Paperclip's interaction payloads."""
        return await post_json(self._client, f"/issues/{issue_id}/interactions", body_json)

    async def accept_issue_interaction(self, issue_id: str, interaction_id: str) -> JsonValue:
        """Accept a pending request-confirmation interaction."""
        return await self._client.post(f"/issues/{issue_id}/interactions/{interaction_id}/accept")

    async def reject_issue_interaction(
        self, issue_id: str, interaction_id: str, reason: str = ""
    ) -> JsonValue:
        """Reject a pending request-confirmation interaction with an optional reason."""
        body = {"reason": reason} if reason else None
        return await self._client.post(
            f"/issues/{issue_id}/interactions/{interaction_id}/reject", body
        )

    async def respond_to_issue_interaction(
        self, issue_id: str, interaction_id: str, body_json: str
    ) -> JsonValue:
        """Submit the structured answer for a pending question or suggested-task interaction."""
        return await post_json(
            self._client, f"/issues/{issue_id}/interactions/{interaction_id}/respond", body_json
        )

    async def withdraw_issue_interaction(
        self, issue_id: str, interaction_id: str, reason: str = ""
    ) -> JsonValue:
        """Withdraw a still-pending interaction created by the caller or issue assignee."""
        body = {"reason": reason} if reason else None
        return await self._client.post(
            f"/issues/{issue_id}/interactions/{interaction_id}/withdraw", body
        )

    async def list_issue_attachments(self, issue_id: str) -> JsonValue:
        """List file attachments uploaded directly to an issue."""
        return await self._client.get(f"/issues/{issue_id}/attachments")

    async def upload_issue_attachment(self, issue_id: str, file_path: str) -> JsonValue:
        """Upload a local file as an issue attachment without exposing its contents in logs."""
        return await self._client.upload_file(
            f"/companies/{self._company_id}/issues/{issue_id}/attachments", file_path
        )

    async def delete_issue_attachment(self, attachment_id: str) -> JsonValue:
        """Delete an issue attachment by ID."""
        return await self._client.delete(f"/attachments/{attachment_id}")

    async def list_issue_approval_links(self, issue_id: str) -> JsonValue:
        """List approval requests linked to an issue."""
        return await self._client.get(f"/issues/{issue_id}/approvals")

    async def link_issue_approval(self, issue_id: str, approval_id: str) -> JsonValue:
        """Link an existing approval request to an issue."""
        return await self._client.post(f"/issues/{issue_id}/approvals", {"approvalId": approval_id})

    async def unlink_issue_approval(self, issue_id: str, approval_id: str) -> JsonValue:
        """Remove an approval link from an issue."""
        return await self._client.delete(f"/issues/{issue_id}/approvals/{approval_id}")

    async def archive_issue_inbox(self, issue_id: str) -> JsonValue:
        """Archive an issue from the caller's inbox without changing its workflow state."""
        return await self._client.post(f"/issues/{issue_id}/inbox-archive")

    async def unarchive_issue_inbox(self, issue_id: str) -> JsonValue:
        """Restore an issue to the caller's inbox."""
        return await self._client.delete(f"/issues/{issue_id}/inbox-archive")


def register_issue_workflow_tools(
    registrar: ToolRegistrar, client: PaperclipClient, company_id: str
) -> None:
    tools = IssueWorkflowTools(client, company_id)
    registrar.add(
        tools.list_issue_interactions,
        tools.create_issue_interaction,
        tools.accept_issue_interaction,
        tools.reject_issue_interaction,
        tools.respond_to_issue_interaction,
        tools.withdraw_issue_interaction,
        tools.list_issue_attachments,
        tools.upload_issue_attachment,
        tools.delete_issue_attachment,
        tools.list_issue_approval_links,
        tools.link_issue_approval,
        tools.unlink_issue_approval,
        tools.archive_issue_inbox,
        tools.unarchive_issue_inbox,
    )
