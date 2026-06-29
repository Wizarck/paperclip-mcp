from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from paperclip_mcp import server


@pytest.mark.asyncio
async def test_issue_thread_tools_are_registered() -> None:
    tool_names = {tool.name for tool in await server.mcp.list_tools()}

    assert {
        "list_issue_comments",
        "get_issue_comment",
        "list_issue_interactions",
        "get_issue_thread",
    } <= tool_names


def test_issue_comment_params_normalizes_and_clamps() -> None:
    assert server._issue_comment_params("  comment-1  ", " ASC ", 900) == {
        "after": "comment-1",
        "order": "asc",
        "limit": 500,
    }
    assert server._issue_comment_params("", "desc", 0) == {
        "order": "desc",
        "limit": 1,
    }


def test_issue_comment_params_rejects_invalid_order() -> None:
    with pytest.raises(ValueError, match="Invalid comment order 'newest'"):
        server._issue_comment_params("", "newest", 50)


@pytest.mark.asyncio
async def test_list_issue_comments_forwards_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    get = AsyncMock(return_value=[{"id": "comment-2", "body": "complete body"}])
    monkeypatch.setattr(server, "_get", get)

    result = await server.list_issue_comments(
        "PAY-42",
        after="comment-1",
        order="asc",
        limit=25,
    )

    assert result == [{"id": "comment-2", "body": "complete body"}]
    get.assert_awaited_once_with(
        "/issues/PAY-42/comments",
        {"after": "comment-1", "order": "asc", "limit": 25},
    )


@pytest.mark.asyncio
async def test_list_issue_comments_returns_structured_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get = AsyncMock()
    monkeypatch.setattr(server, "_get", get)

    result = await server.list_issue_comments("PAY-42", order="sideways")

    assert result["isError"] is True
    assert "Expected one of: asc, desc" in result["message"]
    get.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_issue_comment_fetches_full_record(monkeypatch: pytest.MonkeyPatch) -> None:
    comment = {"id": "comment-1", "body": "complete body"}
    get = AsyncMock(return_value=comment)
    monkeypatch.setattr(server, "_get", get)

    result = await server.get_issue_comment("PAY-42", "comment-1")

    assert result == comment
    get.assert_awaited_once_with("/issues/PAY-42/comments/comment-1")


@pytest.mark.asyncio
async def test_list_issue_interactions_fetches_full_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interactions = [
        {
            "id": "interaction-1",
            "kind": "request_confirmation",
            "payload": {"prompt": "Approve this package?"},
        }
    ]
    get = AsyncMock(return_value=interactions)
    monkeypatch.setattr(server, "_get", get)

    result = await server.list_issue_interactions("PAY-42")

    assert result == interactions
    get.assert_awaited_once_with("/issues/PAY-42/interactions")


@pytest.mark.asyncio
async def test_get_issue_thread_aggregates_responses_and_preserves_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = {
        "/issues/PAY-42": {"id": "issue-1", "identifier": "PAY-42"},
        "/issues/PAY-42/comments": [{"id": "comment-1", "body": "complete body"}],
        "/issues/PAY-42/interactions": {
            "isError": True,
            "status": 403,
            "message": "Forbidden",
        },
    }

    async def fake_get(path: str, params: dict[str, object] | None = None) -> object:
        if path.endswith("/comments"):
            assert params == {"order": "desc", "limit": 10}
        else:
            assert params is None
        return responses[path]

    monkeypatch.setattr(server, "_get", fake_get)

    result = await server.get_issue_thread("PAY-42", comment_limit=10)

    assert result == {
        "issue": responses["/issues/PAY-42"],
        "comments": responses["/issues/PAY-42/comments"],
        "interactions": responses["/issues/PAY-42/interactions"],
    }


@pytest.mark.asyncio
async def test_get_issue_thread_rejects_invalid_order_before_fetching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get = AsyncMock()
    monkeypatch.setattr(server, "_get", get)

    result = await server.get_issue_thread("PAY-42", order="sideways")

    assert result["isError"] is True
    get.assert_not_awaited()
