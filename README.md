# paperclip-mcp

MCP server for the [Paperclip](https://github.com/paperclipai/paperclip) AI agent orchestration platform.

Exposes Paperclip's REST API as [Model Context Protocol](https://modelcontextprotocol.io) tools, so any MCP-compatible AI assistant (Claude, etc.) can manage issues, agents, goals, approvals, and costs through natural language.

---

## Features

| Category | Tools |
|---|---|
| **Issues** | `list_issues` · `get_issue` · `create_issue` · `update_issue` · `checkout_issue` · `release_issue` · `comment_on_issue` · `delete_issue` |
| **Agents** | `list_agents` · `get_agent` · `invoke_agent_heartbeat` |
| **Goals** | `list_goals` · `create_goal` · `update_goal` |
| **Approvals** | `list_approvals` · `approve` · `reject` · `request_approval_revision` |
| **Monitoring** | `get_cost_summary` · `get_dashboard` · `list_activity` |

---

## Requirements

- Python 3.10+
- A running [Paperclip](https://github.com/paperclipai/paperclip) instance
- A board API key (generated via the CLI auth challenge flow — see below)

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
PAPERCLIP_SERVER_NAME=paperclip               # optional, default: "paperclip"
```

> **Security**: Never commit `.env` to version control. It is listed in `.gitignore`.

**Where to find these values:**
- `PAPERCLIP_API_KEY` — board API key with prefix `pcp_board_`. See [Paperclip board API key docs](https://docs.paperclip.ing/reference/api/authentication/board-api-keys). Generate via the CLI auth challenge flow:
  ```bash
  # 1. Create a challenge
  curl -s -X POST http://YOUR_HOST/api/cli-auth/challenges \
    -H "Content-Type: application/json" \
    -d '{"command":"login"}'
  # Response includes boardApiToken and approvalUrl

  # 2. Open approvalUrl in your browser and approve

  # 3. Use boardApiToken as PAPERCLIP_API_KEY
  ```
  Verify the key and find your company IDs:
  ```bash
  curl -s http://YOUR_HOST/api/cli-auth/me \
    -H "Authorization: Bearer pcp_board_YOUR_KEY"
  # Returns user, companyIds, memberships

  curl -s http://YOUR_HOST/api/companies \
    -H "Authorization: Bearer pcp_board_YOUR_KEY"
  # Returns company names mapped to UUIDs
  ```
- `PAPERCLIP_COMPANY_ID` — UUID from the `/api/companies` response above
- `PAPERCLIP_SERVER_NAME` — any string; only matters when running multiple instances (see below)

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

### Register with an MCP client

Add an entry to the `mcpServers` object in your client's config file:

```json
{
  "mcpServers": {
    "paperclip": {
      "command": "uvx",
      "args": ["paperclip-mcp"],
      "env": {
        "PAPERCLIP_API_KEY": "pcp_board_...",
        "PAPERCLIP_COMPANY_ID": "your_company_uuid",
        "PAPERCLIP_BASE_URL": "http://your-paperclip-host/api"
      }
    }
  }
}
```

**Claude Code** — `mcpServers` can go in any of:
- `~/.claude/settings.json` — user-level (all projects)
- `.claude/settings.json` — project-level (checked in)
- `.mcp.json` — project-level (separate file, gitignore-able)

**Claude Desktop** — `mcpServers` goes in:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

## Multiple companies

Add one `mcpServers` entry per company (see config file locations above). Use a distinct `PAPERCLIP_SERVER_NAME` and `PAPERCLIP_COMPANY_ID` per entry; the same board API key works across all companies.

```json
{
  "mcpServers": {
    "paperclip-acme": {
      "command": "uvx",
      "args": ["paperclip-mcp"],
      "env": {
        "PAPERCLIP_SERVER_NAME": "paperclip-acme",
        "PAPERCLIP_API_KEY": "pcp_board_...",
        "PAPERCLIP_COMPANY_ID": "uuid_acme",
        "PAPERCLIP_BASE_URL": "http://your-paperclip-host/api"
      }
    },
    "paperclip-school": {
      "command": "uvx",
      "args": ["paperclip-mcp"],
      "env": {
        "PAPERCLIP_SERVER_NAME": "paperclip-school",
        "PAPERCLIP_API_KEY": "pcp_board_...",
        "PAPERCLIP_COMPANY_ID": "uuid_school",
        "PAPERCLIP_BASE_URL": "http://your-paperclip-host/api"
      }
    }
  }
}
```

The AI assistant picks the right server by name — no per-request company switching needed.

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
# Install with dev dependencies
pip install -e ".[dev]"

# Lint
ruff check src/
ruff format src/

# Type check
mypy src/

# Tests
pytest
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
