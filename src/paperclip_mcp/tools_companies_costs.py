from __future__ import annotations

from .client import JsonValue, PaperclipClient, QueryParameters, error_response
from .registry import ToolRegistrar
from .tools_common import patch_json, post_json


class CompanyCostTools:
    def __init__(self, client: PaperclipClient, company_id: str) -> None:
        self._client = client
        self._company_id = company_id

    async def list_companies(self) -> JsonValue:
        """List companies available to the current board caller."""
        return await self._client.get("/companies")

    async def get_company(self, company_id: str = "") -> JsonValue:
        """Get the configured company by default, or a specified company ID."""
        return await self._client.get(f"/companies/{company_id or self._company_id}")

    async def create_company(self, body_json: str) -> JsonValue:
        """Create a company from a JSON object with name and optional company configuration."""
        return await post_json(self._client, "/companies", body_json)

    async def update_company(self, body_json: str, company_id: str = "") -> JsonValue:
        """Partially update the configured or specified company using a JSON object."""
        return await patch_json(
            self._client, f"/companies/{company_id or self._company_id}", body_json
        )

    async def update_company_branding(self, body_json: str, company_id: str = "") -> JsonValue:
        """Update company name, description, or logoAssetId through the branding-only route."""
        return await patch_json(
            self._client, f"/companies/{company_id or self._company_id}/branding", body_json
        )

    async def upload_company_logo(self, file_path: str, company_id: str = "") -> JsonValue:
        """Upload a local logo image; set its returned assetId as logoAssetId to attach it."""
        return await self._client.upload_file(
            f"/companies/{company_id or self._company_id}/logo", file_path
        )

    async def get_cost_summary(self) -> JsonValue:
        """Get aggregate spend and budget utilization for the configured company."""
        return await self._client.get(f"/companies/{self._company_id}/costs/summary")

    async def get_cost_details(
        self, breakdown: str = "by-agent", from_date: str = "", to_date: str = ""
    ) -> JsonValue:
        """Get a cost breakdown by agent, agent-model, provider, biller, or project."""
        allowed = {"by-agent", "by-agent-model", "by-provider", "by-biller", "by-project"}
        if breakdown not in allowed:
            return error_response(f"Invalid breakdown. Allowed: {', '.join(sorted(allowed))}.")
        params: dict[str, str] = {}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return await self._client.get(
            f"/companies/{self._company_id}/costs/{breakdown}", params or None
        )

    async def get_cost_window_spend(self) -> JsonValue:
        """Get rolling five-hour, 24-hour, and seven-day spend for the configured company."""
        return await self._client.get(f"/companies/{self._company_id}/costs/window-spend")

    async def get_dashboard(self) -> JsonValue:
        """Get the configured company's high-level health and work summary."""
        return await self._client.get(f"/companies/{self._company_id}/dashboard")

    async def list_activity(self, agent_id: str = "", limit: int = 20) -> JsonValue:
        """List recent company activity, optionally filtering to an agent."""
        params: QueryParameters = {"limit": max(1, min(limit, 100))}
        if agent_id:
            params["agentId"] = agent_id
        return await self._client.get(f"/companies/{self._company_id}/activity", params)


def register_company_cost_tools(
    registrar: ToolRegistrar, client: PaperclipClient, company_id: str
) -> None:
    tools = CompanyCostTools(client, company_id)
    registrar.add(
        tools.list_companies,
        tools.get_company,
        tools.create_company,
        tools.update_company,
        tools.update_company_branding,
        tools.upload_company_logo,
        tools.get_cost_summary,
        tools.get_cost_details,
        tools.get_cost_window_spend,
        tools.get_dashboard,
        tools.list_activity,
    )
