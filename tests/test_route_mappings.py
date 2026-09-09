from dataclasses import dataclass, field

import pytest

from paperclip_mcp.client import JsonObject, PaperclipClient, Settings
from paperclip_mcp.tools_agents import AgentTools
from paperclip_mcp.tools_issue_workflow import IssueWorkflowTools
from paperclip_mcp.tools_issues import IssueTools
from paperclip_mcp.tools_planning_approvals import ApprovalTools
from paperclip_mcp.tools_routines_secrets import RoutineTools, SecretTools


@dataclass
class CapturedCall:
    method: str
    path: str
    body: JsonObject | None
    params: JsonObject | None


@dataclass
class CapturingClient:
    calls: list[CapturedCall] = field(default_factory=list)

    async def get(self, path: str, params: JsonObject | None = None) -> JsonObject:
        self.calls.append(CapturedCall("GET", path, None, params))
        return {"ok": True}

    async def post(self, path: str, body: JsonObject | None = None) -> JsonObject:
        self.calls.append(CapturedCall("POST", path, body, None))
        return {"ok": True}

    async def patch(self, path: str, body: JsonObject) -> JsonObject:
        self.calls.append(CapturedCall("PATCH", path, body, None))
        return {"ok": True}

    async def put(self, path: str, body: JsonObject | None = None) -> JsonObject:
        self.calls.append(CapturedCall("PUT", path, body, None))
        return {"ok": True}

    async def delete(self, path: str) -> JsonObject:
        self.calls.append(CapturedCall("DELETE", path, None, None))
        return {"ok": True}


@pytest.mark.asyncio
async def test_issue_extension_tools_use_documented_routes() -> None:
    # Given: a request-capturing Paperclip client
    client = CapturingClient()
    tools = IssueTools(client, company_id="company-1")
    workflow_tools = IssueWorkflowTools(client, company_id="company-1")

    # When: issue context, document, and inbox tools are invoked
    await tools.get_issue_heartbeat_context("PAP-1")
    await tools.get_issue_blocker_diagnostics("PAP-1")
    await tools.upsert_issue_document("PAP-1", "plan", '{"body":"# Plan"}')
    await workflow_tools.archive_issue_inbox("PAP-1")

    # Then: they target the documented endpoints with JSON bodies
    assert client.calls == [
        CapturedCall("GET", "/issues/PAP-1/heartbeat-context", None, None),
        CapturedCall("GET", "/issues/PAP-1/diagnostics/blockers", None, None),
        CapturedCall("PUT", "/issues/PAP-1/documents/plan", {"body": "# Plan"}, None),
        CapturedCall("POST", "/issues/PAP-1/inbox-archive", None, None),
    ]


@pytest.mark.asyncio
async def test_current_issue_routes_use_required_fields() -> None:
    # Given: issue tools using the latest checkout and list schemas
    client = CapturingClient()
    tools = IssueTools(client, company_id="company-1")

    # When: list and checkout calls are made
    await tools.list_issues(label="label-1")
    await tools.checkout_issue("PAP-2", agent_id="agent-1")
    update_result = await tools.update_issue("PAP-2", status="in_review", priority="critical")

    # Then: current field names and status values are accepted
    assert update_result == {"ok": True}
    assert client.calls == [
        CapturedCall(
            "GET",
            "/companies/company-1/issues",
            None,
            {"status": "todo,in_progress", "limit": 50, "labelId": "label-1"},
        ),
        CapturedCall(
            "POST",
            "/issues/PAP-2/checkout",
            {"agentId": "agent-1", "expectedStatuses": ["todo", "backlog", "blocked", "in_review"]},
            None,
        ),
        CapturedCall(
            "PATCH", "/issues/PAP-2", {"status": "in_review", "priority": "critical"}, None
        ),
    ]


@pytest.mark.asyncio
async def test_approval_decision_routes_use_decision_note() -> None:
    # Given: approval tools and review notes
    client = CapturingClient()
    tools = ApprovalTools(client, company_id="company-1")

    # When: approval decisions are submitted
    await tools.approve("approval-1", "ship it")
    await tools.reject("approval-2", "not safe")
    await tools.request_approval_revision("approval-3", "revise budget")

    # Then: Paperclip receives the current decisionNote field
    assert client.calls == [
        CapturedCall("POST", "/approvals/approval-1/approve", {"decisionNote": "ship it"}, None),
        CapturedCall("POST", "/approvals/approval-2/reject", {"decisionNote": "not safe"}, None),
        CapturedCall(
            "POST",
            "/approvals/approval-3/request-revision",
            {"decisionNote": "revise budget"},
            None,
        ),
    ]


@pytest.mark.asyncio
async def test_agent_routine_and_secret_tools_use_company_scoped_routes() -> None:
    # Given: a request-capturing Paperclip client
    client = CapturingClient()
    agents = AgentTools(client, company_id="company-1")
    routines = RoutineTools(client, company_id="company-1")
    secrets = SecretTools(client, company_id="company-1")

    # When: representative control-plane tools are invoked
    await agents.create_agent('{"name":"Worker","role":"engineer","adapterType":"codex_local"}')
    await routines.run_routine("routine-1", '{"source":"manual"}')
    await secrets.list_secret_providers()

    # Then: routes and methods match the API reference
    assert client.calls == [
        CapturedCall(
            "POST",
            "/companies/company-1/agents",
            {"name": "Worker", "role": "engineer", "adapterType": "codex_local"},
            None,
        ),
        CapturedCall("POST", "/routines/routine-1/run", {"source": "manual"}, None),
        CapturedCall("GET", "/companies/company-1/secret-providers", None, None),
    ]


def test_run_header_is_only_sent_when_configured() -> None:
    # Given: clients with and without a real active Paperclip run id
    without_run = PaperclipClient(
        Settings("http://paperclip.test/api", "api-key", "company-1", "", frozenset())
    )
    with_run = PaperclipClient(
        Settings("http://paperclip.test/api", "api-key", "company-1", "run-123", frozenset())
    )

    # When: request headers are constructed
    without_headers = without_run.headers()
    with_headers = with_run.headers()

    # Then: no placeholder is synthesized, and a configured run is forwarded
    assert "X-Paperclip-Run-Id" not in without_headers
    assert with_headers["X-Paperclip-Run-Id"] == "run-123"
