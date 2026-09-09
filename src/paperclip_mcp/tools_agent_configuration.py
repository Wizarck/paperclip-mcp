from __future__ import annotations

from .client import JsonValue, PaperclipClient
from .registry import ToolRegistrar
from .tools_common import patch_json, put_json


class AgentConfigurationTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def get_agent_configuration(self, agent_id: str) -> JsonValue:
        """Get the effective configuration for an agent; Paperclip redacts secret-bearing fields."""
        return await self._client.get(f"/agents/{agent_id}/configuration")

    async def list_agent_config_revisions(self, agent_id: str) -> JsonValue:
        """List redacted configuration revisions for an agent."""
        return await self._client.get(f"/agents/{agent_id}/config-revisions")

    async def get_agent_config_revision(self, agent_id: str, revision_id: str) -> JsonValue:
        """Get one redacted configuration revision."""
        return await self._client.get(f"/agents/{agent_id}/config-revisions/{revision_id}")

    async def rollback_agent_config_revision(self, agent_id: str, revision_id: str) -> JsonValue:
        """Roll an agent back to a permitted prior configuration revision."""
        return await self._client.post(
            f"/agents/{agent_id}/config-revisions/{revision_id}/rollback"
        )

    async def list_company_agent_configurations(self) -> JsonValue:
        """List company agent configurations with secret-bearing fields redacted."""
        return await self._client.get(f"/companies/{self._company_id}/agent-configurations")

    async def update_agent_instructions_path(self, agent_id: str, body_json: str) -> JsonValue:
        """Update file-based instructions path configuration using a JSON object."""
        return await patch_json(self._client, f"/agents/{agent_id}/instructions-path", body_json)

    async def get_agent_instructions_bundle(self, agent_id: str) -> JsonValue:
        """Get the file-based instructions bundle metadata for an agent."""
        return await self._client.get(f"/agents/{agent_id}/instructions-bundle")

    async def update_agent_instructions_bundle(self, agent_id: str, body_json: str) -> JsonValue:
        """Update an agent's instructions bundle metadata from a JSON object."""
        return await patch_json(self._client, f"/agents/{agent_id}/instructions-bundle", body_json)

    async def get_agent_instructions_file(self, agent_id: str, path: str = "") -> JsonValue:
        """Read an instructions-bundle file, optionally selecting a path query parameter."""
        params = {"path": path} if path else None
        return await self._client.get(f"/agents/{agent_id}/instructions-bundle/file", params)

    async def put_agent_instructions_file(self, agent_id: str, body_json: str) -> JsonValue:
        """Create or replace one instructions-bundle file from a JSON object."""
        return await put_json(
            self._client, f"/agents/{agent_id}/instructions-bundle/file", body_json
        )

    async def delete_agent_instructions_file(self, agent_id: str, path: str) -> JsonValue:
        """Delete one file from an agent's instructions bundle."""
        return await self._client.delete(
            f"/agents/{agent_id}/instructions-bundle/file", {"path": path}
        )


def register_agent_configuration_tools(
    registrar: ToolRegistrar, client: PaperclipClient, company_id: str
) -> None:
    tools = AgentConfigurationTools(client, company_id)
    registrar.add(
        tools.get_agent_configuration,
        tools.list_agent_config_revisions,
        tools.get_agent_config_revision,
        tools.rollback_agent_config_revision,
        tools.list_company_agent_configurations,
        tools.update_agent_instructions_path,
        tools.get_agent_instructions_bundle,
        tools.update_agent_instructions_bundle,
        tools.get_agent_instructions_file,
        tools.put_agent_instructions_file,
        tools.delete_agent_instructions_file,
    )
