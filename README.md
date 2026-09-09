# paperclip-mcp

MCP server for the [Paperclip](https://github.com/paperclipai/paperclip) AI agent orchestration platform.

Exposes Paperclip's REST API as [Model Context Protocol](https://modelcontextprotocol.io)
tools, so any MCP-compatible assistant can manage Paperclip's control plane through
natural language.

---

## Features

| Category | Tools |
|---|---|
| **Issues** | `list_issues` · `get_issue` · `create_issue` · `update_issue` · `checkout_issue` · `release_issue` · `comment_on_issue` · `delete_issue` · `get_issue_heartbeat_context` · `get_issue_blocker_diagnostics` · `get_issue_wake_diagnostics` · `get_issue_subtree_diagnostics` · `list_issue_comments` · `get_issue_comment` · `list_issue_activity` · `list_issue_runs` |
| **Issue Workflow** | `list_issue_interactions` · `create_issue_interaction` · `accept_issue_interaction` · `reject_issue_interaction` · `respond_to_issue_interaction` · `withdraw_issue_interaction` · `list_issue_attachments` · `upload_issue_attachment` · `delete_issue_attachment` · `list_issue_approval_links` · `link_issue_approval` · `unlink_issue_approval` · `archive_issue_inbox` · `unarchive_issue_inbox` |
| **Issue Documents** | `list_issue_documents` · `get_issue_document` · `upsert_issue_document` · `lock_issue_document` · `unlock_issue_document` · `list_issue_document_revisions` · `restore_issue_document_revision` · `delete_issue_document` · `list_document_annotations` · `create_document_annotation` · `reply_to_document_annotation` · `resolve_document_annotation` · `reopen_document_annotation` |
| **Agents** | `list_agents` · `get_agent` · `create_agent` · `hire_agent` · `update_agent` · `update_agent_permissions` · `pause_agent` · `resume_agent` · `terminate_agent` · `delete_agent` · `invoke_agent_heartbeat` · `wake_agent` · `list_agent_keys` · `create_agent_key` · `revoke_agent_key` · `get_company_org` |
| **Agent Config** | `list_adapter_models` · `detect_adapter_model` · `test_adapter_environment` · `list_agent_skills` · `sync_agent_skills` · `get_agent_configuration` · `list_agent_config_revisions` · `get_agent_config_revision` · `rollback_agent_config_revision` · `list_company_agent_configurations` · `update_agent_instructions_path` · `get_agent_instructions_bundle` · `update_agent_instructions_bundle` · `get_agent_instructions_file` · `put_agent_instructions_file` · `delete_agent_instructions_file` · `list_granted_secrets` · `read_granted_secret_value` |
| **Goals & Projects** | `list_goals` · `get_goal` · `create_goal` · `update_goal` · `delete_goal` · `list_projects` · `get_project` · `create_project` · `update_project` · `delete_project` · `list_project_workspaces` · `create_project_workspace` · `update_project_workspace` · `delete_project_workspace` · `manage_workspace_runtime_service` |
| **Approvals** | `list_approvals` · `get_approval` · `create_approval` · `approve` · `reject` · `request_approval_revision` · `list_approval_linked_issues` · `list_approval_comments` · `comment_on_approval` · `resubmit_approval` |
| **Routines** | `list_routines` · `get_routine` · `create_routine` · `update_routine` · `delete_routine` · `create_routine_trigger` · `update_routine_trigger` · `delete_routine_trigger` · `rotate_routine_trigger_secret` · `run_routine` · `fire_public_routine_trigger` · `list_routine_runs` |
| **Secrets** | `list_secret_providers` · `list_secrets` · `list_secret_catalog` · `create_secret` · `update_secret` · `rotate_secret` · `delete_secret` · `list_secret_proposals` · `approve_secret_proposal` · `reject_secret_proposal` · `list_my_secret_proposals` · `create_secret_proposal` · `withdraw_secret_proposal` |
| **Companies & Monitoring** | `list_companies` · `get_company` · `create_company` · `update_company` · `update_company_branding` · `upload_company_logo` · `get_cost_summary` · `get_cost_details` · `get_cost_window_spend` · `get_dashboard` · `list_activity` |

---

## Requirements

- Python 3.10+
- A running [Paperclip](https://github.com/paperclipai/paperclip) instance
- An Agent API key (generated in Paperclip UI → Settings → API Keys)

---

## Installation

### Option A — pip / uv (recommended)

```bash
# Clone the repo
git clone https://github.com/wizarck/paperclip-mcp
cd paperclip-mcp

# Install (editable for local use, or drop -e for production)
pip install -e .
# or
uv pip install -e .
```

### Option B — Run directly without installing

```bash
pip install fastmcp httpx python-dotenv
python src/paperclip_mcp/server.py
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```dotenv
PAPERCLIP_BASE_URL=http://localhost:3100/api   # default, change if needed
PAPERCLIP_API_KEY=your_api_key_here
PAPERCLIP_COMPANY_ID=your_company_uuid_here
PAPERCLIP_RUN_ID=                              # optional real active run ID only
PAPERCLIP_DISABLED_TOOLS=                      # optional comma-separated names/categories
```

> **Security**: Never commit `.env` to version control. It is listed in `.gitignore`.

**Where to find these values:**
- `PAPERCLIP_API_KEY` — Paperclip UI → Settings → API Keys → New Key
- `PAPERCLIP_COMPANY_ID` — visible in the URL when viewing your company: `/companies/{uuid}`
- `PAPERCLIP_RUN_ID` — the current real heartbeat run ID, when this MCP call is
  part of an agent run. Leave empty otherwise; the server never fabricates a run ID.

### Tool selection

Every documented tool is enabled by default. Set `PAPERCLIP_DISABLED_TOOLS` to a
comma-separated list of exact tool names, categories, or both to hide tools from
MCP clients:

```dotenv
PAPERCLIP_DISABLED_TOOLS=secrets,delete_agent,fire_public_routine_trigger
```

Valid categories are `issues`, `agents`, `goals`, `projects`, `approvals`,
`costs`, `monitoring`, `secrets`, `routines`, and `companies`. Startup fails with
the complete valid-token list if any token is unknown.

### JSON-object inputs and sensitive values

Broad control-plane tools such as `create_agent`, `update_project`,
`create_routine`, and `create_secret` accept a `body_json` string containing the
JSON object documented by the current Paperclip API. This keeps the MCP surface
useful as Paperclip adds adapter, routine, and policy fields.

Secret values, public trigger credentials, and uploaded file contents are sent to
Paperclip but are never logged by this server. `read_granted_secret_value` returns
a live run-bound secret value only when Paperclip authorizes that route; do not
repeat or persist its response.

---

## Usage

### Start the server

```bash
# HTTP (for Claude Code / mcp-proxy) — default port 9011
paperclip-mcp

# Custom port
paperclip-mcp --port 9012

# stdio transport (for Claude Desktop)
paperclip-mcp --transport stdio

# All options
paperclip-mcp --help
```

### Register with Claude Code

```bash
# HTTP transport (persistent — survives Claude restarts)
claude mcp add paperclip --transport http http://localhost:9011/mcp

# stdio transport (Claude Desktop — add to claude_desktop_config.json)
```

#### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "paperclip": {
      "command": "paperclip-mcp",
      "args": ["--transport", "stdio"],
      "env": {
        "PAPERCLIP_API_KEY": "your_api_key",
        "PAPERCLIP_COMPANY_ID": "your_company_uuid"
      }
    }
  }
}
```

---

## Example interactions

Once registered, you can ask your AI assistant:

```
"What tasks does the Purchasing agent have open?"
→ calls list_issues(assignee_agent_id="...", status="todo,in_progress")

"Create a task for the CEO agent to search for new cheese suppliers in Barcelona"
→ calls create_issue(title="Search cheese suppliers in Barcelona", assignee_agent_id="...")

"Approve the pending hire request"
→ calls list_approvals(status="pending") + approve(approval_id="...")

"How much have we spent on tokens this month, broken down by agent?"
→ calls get_cost_summary()

"Wake up the Administration agent now"
→ calls invoke_agent_heartbeat(agent_id="...")
```

---

## Auto-start with the MCP stack

Add to your stack startup script:

```bash
# Check if already running
curl -s --max-time 1 http://localhost:9011/mcp > /dev/null 2>&1 || \
  nohup paperclip-mcp > /tmp/paperclip-mcp.log 2>&1 &
```

---

## Development

```bash
# Run the test environment with dev dependencies
uv run --extra dev pytest

# Lint
uv run --extra dev ruff check src/ tests/
uv run --extra dev ruff format --check src/ tests/

# Type check
uv run --extra dev mypy src/

# Tests
uv run --extra dev pytest
```

---

## Architecture notes

- **Who should use this MCP**: Human operators managing agents via Claude Code or Claude Desktop.
- **Do agents need this MCP?**: No — Paperclip agents already interact with the REST API directly via HTTP in their HEARTBEAT protocol. This MCP is for the human operator layer.
- **Hermes agents**: If you switch to [Hermes](https://github.com/NousResearch/hermes-paperclip-adapter), this MCP is automatically available since Hermes supports MCP natively.
- **Transport choice**: Use `streamable-http` for Claude Code and mcp-proxy integrations. Use `stdio` for Claude Desktop.
- **Security**: The server binds to `127.0.0.1` by default (localhost only). Do not expose it publicly — it carries your Paperclip API key.

---

## License

MIT — see [LICENSE](LICENSE).
