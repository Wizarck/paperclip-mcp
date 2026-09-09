import json
from pathlib import Path

import pytest
from fastmcp import Client

from paperclip_mcp.client import Settings
from paperclip_mcp.registry import (
    TOOL_CATEGORIES,
    DisabledToolConfigurationError,
    disabled_tool_names,
    enabled_tool_names,
    parse_disabled_tools,
)
from paperclip_mcp.server import create_server


def test_all_tools_are_enabled_when_disabled_tools_is_empty() -> None:
    # Given: no disabled-tool configuration
    # When: the disabled names are resolved
    disabled = disabled_tool_names("")

    # Then: every registered tool remains enabled
    assert disabled == frozenset()
    assert enabled_tool_names("") == frozenset(TOOL_CATEGORIES)


def test_an_exact_tool_name_disables_only_that_tool() -> None:
    # Given: a single exact tool name
    # When: the disabled names are resolved
    disabled = disabled_tool_names("list_issue_comments")

    # Then: only that exact tool is disabled
    assert disabled == frozenset({"list_issue_comments"})


def test_a_category_disables_every_tool_in_that_category() -> None:
    # Given: the issues category
    # When: the disabled names are resolved
    disabled = disabled_tool_names("issues")

    # Then: every issues tool is disabled and other categories remain enabled
    assert {name for name, category in TOOL_CATEGORIES.items() if category == "issues"} == disabled
    assert "list_agents" not in disabled


def test_invalid_disabled_tool_token_explains_valid_tokens() -> None:
    # Given: an unknown disabled-tool token
    # When: it is parsed
    # Then: startup receives a useful configuration error
    with pytest.raises(DisabledToolConfigurationError, match="Valid categories"):
        parse_disabled_tools("not-a-paperclip-tool")


def test_server_metadata_lists_the_complete_tool_inventory() -> None:
    metadata_path = Path(__file__).parents[1] / "server.json"
    metadata = json.loads(metadata_path.read_text())

    assert set(metadata["capabilities"]["tools"]) == set(TOOL_CATEGORIES)


@pytest.mark.asyncio
async def test_server_omits_exact_and_category_disabled_tools() -> None:
    # Given: a server configured to hide one named tool and an entire category
    server = create_server(
        Settings(
            base_url="http://paperclip.test/api",
            api_key="api-key",
            company_id="company-1",
            run_id="",
            disabled_tools=disabled_tool_names("delete_agent,secrets"),
        )
    )

    # When: an in-memory MCP client discovers the registered tools
    async with Client(server) as client:
        tool_names = {tool.name for tool in await client.list_tools()}

    # Then: disabled names are absent while unrelated tools remain discoverable
    assert "delete_agent" not in tool_names
    assert "list_secrets" not in tool_names
    assert "create_secret" not in tool_names
    assert "list_agents" in tool_names
