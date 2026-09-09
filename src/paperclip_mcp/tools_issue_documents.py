from __future__ import annotations

from .client import JsonValue, PaperclipClient
from .registry import ToolRegistrar
from .tools_common import post_json


class IssueDocumentTools:
    def __init__(self, client: PaperclipClient) -> None:
        self._client = client

    async def list_issue_documents(self, issue_id: str) -> JsonValue:
        """List keyed, revisioned documents attached to an issue."""
        return await self._client.get(f"/issues/{issue_id}/documents")

    async def get_issue_document(
        self, issue_id: str, key: str, include_annotations: bool = False
    ) -> JsonValue:
        """Get an issue document, optionally including its annotation threads."""
        params = {"includeAnnotations": "true"} if include_annotations else None
        return await self._client.get(f"/issues/{issue_id}/documents/{key}", params)

    async def lock_issue_document(self, issue_id: str, key: str) -> JsonValue:
        """Lock an issue document so agent updates create derived revisions instead."""
        return await self._client.post(f"/issues/{issue_id}/documents/{key}/lock")

    async def unlock_issue_document(self, issue_id: str, key: str) -> JsonValue:
        """Unlock an issue document."""
        return await self._client.post(f"/issues/{issue_id}/documents/{key}/unlock")

    async def list_issue_document_revisions(self, issue_id: str, key: str) -> JsonValue:
        """List document revisions from newest to oldest."""
        return await self._client.get(f"/issues/{issue_id}/documents/{key}/revisions")

    async def restore_issue_document_revision(
        self, issue_id: str, key: str, revision_id: str
    ) -> JsonValue:
        """Restore a prior revision by creating it again as the latest document revision."""
        return await self._client.post(
            f"/issues/{issue_id}/documents/{key}/revisions/{revision_id}/restore"
        )

    async def delete_issue_document(self, issue_id: str, key: str) -> JsonValue:
        """Delete a document and its revision history; this is board-only in Paperclip."""
        return await self._client.delete(f"/issues/{issue_id}/documents/{key}")

    async def list_document_annotations(
        self, issue_id: str, key: str, status: str = "all", include_comments: bool = True
    ) -> JsonValue:
        """List annotation threads for a document, with comments included by default."""
        return await self._client.get(
            f"/issues/{issue_id}/documents/{key}/annotations",
            {"status": status, "includeComments": str(include_comments).lower()},
        )

    async def create_document_annotation(
        self, issue_id: str, key: str, body_json: str
    ) -> JsonValue:
        """Create an anchored annotation thread using the current document revision in body_json."""
        return await post_json(
            self._client, f"/issues/{issue_id}/documents/{key}/annotations", body_json
        )

    async def reply_to_document_annotation(
        self, issue_id: str, key: str, annotation_id: str, body: str
    ) -> JsonValue:
        """Add a Markdown reply to one document annotation thread."""
        return await self._client.post(
            f"/issues/{issue_id}/documents/{key}/annotations/{annotation_id}/comments",
            {"body": body},
        )

    async def resolve_document_annotation(
        self, issue_id: str, key: str, annotation_id: str
    ) -> JsonValue:
        """Resolve an annotation thread once its review discussion is settled."""
        return await self._client.patch(
            f"/issues/{issue_id}/documents/{key}/annotations/{annotation_id}",
            {"status": "resolved"},
        )

    async def reopen_document_annotation(
        self, issue_id: str, key: str, annotation_id: str
    ) -> JsonValue:
        """Reopen a resolved document annotation thread."""
        return await self._client.patch(
            f"/issues/{issue_id}/documents/{key}/annotations/{annotation_id}",
            {"status": "open"},
        )


def register_issue_document_tools(registrar: ToolRegistrar, client: PaperclipClient) -> None:
    tools = IssueDocumentTools(client)
    registrar.add(
        tools.list_issue_documents,
        tools.get_issue_document,
        tools.lock_issue_document,
        tools.unlock_issue_document,
        tools.list_issue_document_revisions,
        tools.restore_issue_document_revision,
        tools.delete_issue_document,
        tools.list_document_annotations,
        tools.create_document_annotation,
        tools.reply_to_document_annotation,
        tools.resolve_document_annotation,
        tools.reopen_document_annotation,
    )
