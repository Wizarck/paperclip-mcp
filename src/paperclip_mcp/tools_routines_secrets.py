from __future__ import annotations

from .client import JsonValue, PaperclipClient, is_error_response, parse_json_object
from .registry import ToolRegistrar
from .tools_common import patch_json, post_json


class RoutineTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_routines(self) -> JsonValue:
        """List recurring routines in the configured company."""
        return await self._client.get(f"/companies/{self._company_id}/routines")

    async def get_routine(self, routine_id: str) -> JsonValue:
        """Get one routine with its triggers, recent runs, and active issue."""
        return await self._client.get(f"/routines/{routine_id}")

    async def create_routine(self, body_json: str) -> JsonValue:
        """Create a routine from a JSON object with title, assignee, schedule, and policy."""
        return await post_json(self._client, f"/companies/{self._company_id}/routines", body_json)

    async def update_routine(self, routine_id: str, body_json: str) -> JsonValue:
        """Partially update a routine using documented routine fields in body_json."""
        return await patch_json(self._client, f"/routines/{routine_id}", body_json)

    async def delete_routine(self, routine_id: str) -> JsonValue:
        """Delete a routine."""
        return await self._client.delete(f"/routines/{routine_id}")

    async def create_routine_trigger(self, routine_id: str, body_json: str) -> JsonValue:
        """Create a schedule, webhook, or API trigger; webhook secrets are returned only once."""
        return await post_json(self._client, f"/routines/{routine_id}/triggers", body_json)

    async def update_routine_trigger(self, trigger_id: str, body_json: str) -> JsonValue:
        """Update a routine trigger's enabled state or kind-specific settings."""
        return await patch_json(self._client, f"/routine-triggers/{trigger_id}", body_json)

    async def delete_routine_trigger(self, trigger_id: str) -> JsonValue:
        """Delete a routine trigger."""
        return await self._client.delete(f"/routine-triggers/{trigger_id}")

    async def rotate_routine_trigger_secret(self, trigger_id: str) -> JsonValue:
        """Rotate a webhook trigger secret; Paperclip returns the replacement material once."""
        return await self._client.post(f"/routine-triggers/{trigger_id}/rotate-secret")

    async def run_routine(self, routine_id: str, body_json: str = "{}") -> JsonValue:
        """Start a manual or API routine run with optional variables and idempotency key."""
        return await post_json(self._client, f"/routines/{routine_id}/run", body_json)

    async def fire_public_routine_trigger(
        self,
        public_id: str,
        body_json: str = "{}",
        authorization: str = "",
        signature: str = "",
        timestamp: str = "",
    ) -> JsonValue:
        """Fire a public webhook trigger with optional bearer or HMAC credentials."""
        body = parse_json_object(body_json)
        if is_error_response(body):
            return body
        headers: dict[str, str] = {}
        if authorization:
            headers["Authorization"] = f"Bearer {authorization}"
        if signature:
            headers["X-Paperclip-Signature"] = signature
        if timestamp:
            headers["X-Paperclip-Timestamp"] = timestamp
        return await self._client.request(
            "POST",
            f"/routine-triggers/public/{public_id}/fire",
            body=body,
            additional_headers=headers,
        )

    async def list_routine_runs(self, routine_id: str, limit: int = 50) -> JsonValue:
        """List recent routine runs, capped by Paperclip at 200 records."""
        return await self._client.get(
            f"/routines/{routine_id}/runs", {"limit": max(1, min(limit, 200))}
        )


class SecretTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_secret_providers(self) -> JsonValue:
        """List configured secret providers and their supported capabilities."""
        return await self._client.get(f"/companies/{self._company_id}/secret-providers")

    async def list_secrets(self) -> JsonValue:
        """List secret metadata; Paperclip never returns plaintext values from this route."""
        return await self._client.get(f"/companies/{self._company_id}/secrets")

    async def list_secret_catalog(self) -> JsonValue:
        """List the compact bindable-secret catalog without provider metadata or values."""
        return await self._client.get(f"/companies/{self._company_id}/secrets/catalog")

    async def create_secret(self, body_json: str) -> JsonValue:
        """Create a secret from a JSON object without server-side plaintext logging."""
        return await post_json(self._client, f"/companies/{self._company_id}/secrets", body_json)

    async def update_secret(self, secret_id: str, body_json: str) -> JsonValue:
        """Update secret metadata or an external reference, never a plaintext value."""
        return await patch_json(self._client, f"/secrets/{secret_id}", body_json)

    async def rotate_secret(self, secret_id: str, body_json: str) -> JsonValue:
        """Rotate a secret from a JSON object without server-side plaintext logging."""
        return await post_json(self._client, f"/secrets/{secret_id}/rotate", body_json)

    async def delete_secret(self, secret_id: str) -> JsonValue:
        """Hard-delete a secret and its version history."""
        return await self._client.delete(f"/secrets/{secret_id}")

    async def list_secret_proposals(self) -> JsonValue:
        """List board-reviewable secret and binding proposals for the configured company."""
        return await self._client.get(f"/companies/{self._company_id}/secret-proposals")

    async def approve_secret_proposal(self, proposal_id: str, body_json: str = "{}") -> JsonValue:
        """Approve a secret proposal, optionally cascading a prerequisite secret proposal."""
        return await post_json(
            self._client,
            f"/companies/{self._company_id}/secret-proposals/{proposal_id}/approve",
            body_json,
        )

    async def reject_secret_proposal(self, proposal_id: str, body_json: str = "{}") -> JsonValue:
        """Reject a board-reviewable secret proposal with an optional JSON decision payload."""
        return await post_json(
            self._client,
            f"/companies/{self._company_id}/secret-proposals/{proposal_id}/reject",
            body_json,
        )

    async def list_my_secret_proposals(self, limit: int = 100, offset: int = 0) -> JsonValue:
        """List run-bound secret proposals raised by or targeted at the authenticated agent."""
        return await self._client.get(
            "/agents/me/secret-proposals",
            {"limit": max(1, min(limit, 200)), "offset": max(0, offset)},
        )

    async def create_secret_proposal(self, body_json: str) -> JsonValue:
        """Propose a secret or binding without server-side plaintext logging."""
        return await post_json(self._client, "/agents/me/secret-proposals", body_json)

    async def withdraw_secret_proposal(self, proposal_id: str) -> JsonValue:
        """Withdraw one pending secret proposal from the authenticated agent."""
        return await self._client.delete(f"/agents/me/secret-proposals/{proposal_id}")


def register_routine_and_secret_tools(
    registrar: ToolRegistrar, client: PaperclipClient, company_id: str
) -> None:
    routines = RoutineTools(client, company_id)
    secrets = SecretTools(client, company_id)
    registrar.add(
        routines.list_routines,
        routines.get_routine,
        routines.create_routine,
        routines.update_routine,
        routines.delete_routine,
        routines.create_routine_trigger,
        routines.update_routine_trigger,
        routines.delete_routine_trigger,
        routines.rotate_routine_trigger_secret,
        routines.run_routine,
        routines.fire_public_routine_trigger,
        routines.list_routine_runs,
        secrets.list_secret_providers,
        secrets.list_secrets,
        secrets.list_secret_catalog,
        secrets.create_secret,
        secrets.update_secret,
        secrets.rotate_secret,
        secrets.delete_secret,
        secrets.list_secret_proposals,
        secrets.approve_secret_proposal,
        secrets.reject_secret_proposal,
        secrets.list_my_secret_proposals,
        secrets.create_secret_proposal,
        secrets.withdraw_secret_proposal,
    )
