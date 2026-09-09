from __future__ import annotations

from .client import JsonValue, PaperclipClient
from .registry import ToolRegistrar
from .tools_common import patch_json, post_json


class AgentTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_agents(self) -> JsonValue:
        """List active agents in the configured company."""
        return await self._client.get(f"/companies/{self._company_id}/agents")

    async def get_agent(self, agent_id: str = "me") -> JsonValue:
        """Get an agent by ID, or get the authenticated agent when agent_id is me."""
        path = "/agents/me" if agent_id.strip().lower() == "me" else f"/agents/{agent_id}"
        return await self._client.get(path)

    async def invoke_agent_heartbeat(self, agent_id: str) -> JsonValue:
        """Trigger a simple immediate heartbeat for an agent."""
        return await self._client.post(f"/agents/{agent_id}/heartbeat/invoke")

    async def create_agent(self, body_json: str) -> JsonValue:
        """Create an agent from a Paperclip agent JSON object."""
        return await post_json(self._client, f"/companies/{self._company_id}/agents", body_json)

    async def hire_agent(self, body_json: str) -> JsonValue:
        """Create an approval-aware agent hire from a Paperclip hire JSON object."""
        return await post_json(
            self._client, f"/companies/{self._company_id}/agent-hires", body_json
        )

    async def update_agent(self, agent_id: str, body_json: str) -> JsonValue:
        """Partially update an agent using documented agent fields in body_json."""
        return await patch_json(self._client, f"/agents/{agent_id}", body_json)

    async def update_agent_permissions(self, agent_id: str, body_json: str) -> JsonValue:
        """Update an agent's permissions through Paperclip's dedicated permissions route."""
        return await patch_json(self._client, f"/agents/{agent_id}/permissions", body_json)

    async def pause_agent(self, agent_id: str) -> JsonValue:
        """Pause an agent so it stops taking new work."""
        return await self._client.post(f"/agents/{agent_id}/pause")

    async def resume_agent(self, agent_id: str) -> JsonValue:
        """Resume a paused agent."""
        return await self._client.post(f"/agents/{agent_id}/resume")

    async def terminate_agent(self, agent_id: str) -> JsonValue:
        """Terminate an agent and revoke its API keys while retaining its record."""
        return await self._client.post(f"/agents/{agent_id}/terminate")

    async def delete_agent(self, agent_id: str) -> JsonValue:
        """Hard-delete an agent and related runtime state."""
        return await self._client.delete(f"/agents/{agent_id}")

    async def list_agent_keys(self, agent_id: str) -> JsonValue:
        """List an agent's API key metadata without returning key tokens."""
        return await self._client.get(f"/agents/{agent_id}/keys")

    async def create_agent_key(self, agent_id: str, name: str) -> JsonValue:
        """Create an agent API key; the returned token is shown only once by Paperclip."""
        return await self._client.post(f"/agents/{agent_id}/keys", {"name": name})

    async def revoke_agent_key(self, agent_id: str, key_id: str) -> JsonValue:
        """Revoke one agent API key."""
        return await self._client.delete(f"/agents/{agent_id}/keys/{key_id}")

    async def wake_agent(self, agent_id: str, body_json: str = "{}") -> JsonValue:
        """Queue a rich agent wakeup with optional context, payload, and idempotency key."""
        return await post_json(self._client, f"/agents/{agent_id}/wakeup", body_json)

    async def get_company_org(self) -> JsonValue:
        """Get the JSON organization chart for the configured company."""
        return await self._client.get(f"/companies/{self._company_id}/org")

    async def list_adapter_models(self, adapter_type: str) -> JsonValue:
        """List models available for an adapter type in the configured company."""
        return await self._client.get(
            f"/companies/{self._company_id}/adapters/{adapter_type}/models"
        )

    async def detect_adapter_model(self, adapter_type: str) -> JsonValue:
        """Ask Paperclip to detect the recommended model for an adapter."""
        return await self._client.get(
            f"/companies/{self._company_id}/adapters/{adapter_type}/detect-model"
        )

    async def test_adapter_environment(self, adapter_type: str, body_json: str = "{}") -> JsonValue:
        """Test an adapter environment with an optional candidate configuration."""
        return await post_json(
            self._client,
            f"/companies/{self._company_id}/adapters/{adapter_type}/test-environment",
            body_json,
        )

    async def list_agent_skills(self, agent_id: str) -> JsonValue:
        """List skills currently available to an agent."""
        return await self._client.get(f"/agents/{agent_id}/skills")

    async def sync_agent_skills(self, agent_id: str, body_json: str) -> JsonValue:
        """Synchronize desired skills using Paperclip's required sync mode in body_json."""
        return await post_json(self._client, f"/agents/{agent_id}/skills/sync", body_json)

    async def list_granted_secrets(self) -> JsonValue:
        """List aliases granted to the authenticated live agent run; values are never returned."""
        return await self._client.get("/agents/me/secrets")

    async def read_granted_secret_value(self, key: str) -> JsonValue:
        """Read one run-bound granted secret value; do not repeat or persist the returned value."""
        return await self._client.post(f"/agents/me/secrets/{key}/value")


def register_agent_tools(
    registrar: ToolRegistrar, client: PaperclipClient, company_id: str
) -> None:
    tools = AgentTools(client, company_id)
    registrar.add(
        tools.list_agents,
        tools.get_agent,
        tools.invoke_agent_heartbeat,
        tools.create_agent,
        tools.hire_agent,
        tools.update_agent,
        tools.update_agent_permissions,
        tools.pause_agent,
        tools.resume_agent,
        tools.terminate_agent,
        tools.delete_agent,
        tools.list_agent_keys,
        tools.create_agent_key,
        tools.revoke_agent_key,
        tools.wake_agent,
        tools.get_company_org,
        tools.list_adapter_models,
        tools.detect_adapter_model,
        tools.test_adapter_environment,
        tools.list_agent_skills,
        tools.sync_agent_skills,
        tools.list_granted_secrets,
        tools.read_granted_secret_value,
    )
