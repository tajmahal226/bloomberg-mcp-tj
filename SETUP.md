# Setup Guide

This guide wires the Bloomberg MCP server into the AI clients you use:
**Claude Desktop**, **Claude Code**, **ChatGPT desktop**, **OpenAI Codex CLI/IDE**,
and optionally **ChatGPT web**.

The server is a single program. You run it **once on the machine that has the
Bloomberg Terminal**, and every client talks to that one server. There is no
cloud component and no API key — authentication comes from your logged-in
Terminal session.

> **Hard requirement:** the server connects to the Terminal's local API on
> `localhost:8194`, so it **must run on the same machine** where Bloomberg
> Terminal is installed and logged in.

---

## Step 1 — Install (once, on the Terminal machine)

```bash
# 1. Point at the Bloomberg C++ SDK
export BLPAPI_ROOT=/path/to/blpapi_cpp_3.x.x.x      # Windows: set BLPAPI_ROOT=C:\blp\blpapi_cpp_3.x.x.x

# 2. Install the Bloomberg Python SDK
pip install blpapi

# 3. Install this package (from the repo root)
pip install -e .
```

This puts a `bloomberg-mcp` command on your PATH. Verify it imports:

```bash
python -c "import blpapi, bloomberg_mcp; print('ok')"
```

> **Tip:** if you use a virtualenv, note its Python path
> (`which python` / `where python`) — some clients need the absolute path to
> the interpreter or to the `bloomberg-mcp` executable.

---

## Step 2 — Pick a transport

| Transport | Command | Use it for |
|-----------|---------|------------|
| **stdio** (default) | `bloomberg-mcp` | Claude clients, ChatGPT desktop, Codex CLI/IDE — the client launches the process |
| **HTTP** | `bloomberg-mcp --http --port=8080` | Private remote clients when required |
| **SSE** | `bloomberg-mcp --sse --port=8080` | Legacy streaming clients |

stdio clients start the server for you, so you don't run anything by hand for
those. HTTP/SSE you launch yourself and leave running.

---

## Step 3 — Connect each client

Ready-to-edit config files live in [`mcp-configs/`](mcp-configs/). Copy the
relevant one, replace `/ABSOLUTE/PATH/TO/bloomberg-mcp-tj`, and drop it where
the client expects it.

### Claude Desktop

Edit `claude_desktop_config.json`:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Use [`mcp-configs/claude-desktop.json`](mcp-configs/claude-desktop.json) as the
content, then fully quit and reopen Claude Desktop.

### Claude Code

Easiest — one command from the repo root:

```bash
claude mcp add bloomberg -- bloomberg-mcp
```

Or commit a project-scoped [`.mcp.json`](mcp-configs/claude-code.mcp.json) at
the repo root (template provided). Confirm with `/mcp` inside Claude Code.

### ChatGPT desktop and OpenAI Codex

Add the block from [`mcp-configs/codex-config.toml`](mcp-configs/codex-config.toml)
to `~/.codex/config.toml`. The ChatGPT desktop app, Codex CLI, and Codex IDE
extension share this file and launch the server over stdio. Restart the desktop
app after editing, then confirm `bloomberg` under **Settings → MCP servers** or
with `/mcp`.

### ChatGPT web (optional)

ChatGPT web cannot spawn the local stdio process directly. Use OpenAI
[Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
to keep the Bloomberg server private:

1. Create a tunnel in OpenAI Platform tunnel settings.
2. Run `tunnel-client` on the Terminal machine and point its local stdio profile
   at this repo's `.venv` Python with `-m bloomberg_mcp.server`.
3. In ChatGPT developer mode, create an app and choose that tunnel connection.

> Keep the server local-only unless web access is genuinely needed. Bloomberg's
> Subscriber Agreement governs data use and redistribution.

---

## Step 4 — Verify

Once a client is connected, ask it something simple that exercises a tool:

> "Use the bloomberg tools to get PX_LAST for AAPL US Equity."

You should see it call `bloomberg_get_reference_data` and return a price. If it
errors with a connection failure, confirm the Terminal is running and logged in
and that nothing else is bound to port 8194.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BLOOMBERG_HOST` | `localhost` | Bloomberg API host |
| `BLOOMBERG_PORT` | `8194` | Bloomberg API port |
| `MCP_HOST` | `0.0.0.0` | Server bind address (HTTP/SSE only) |
| `MCP_PORT` | `8080` | Server port (HTTP/SSE only) |

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `Connection failed` / `Failed to start Bloomberg session` | Terminal not running/logged in, or server not on the Terminal machine |
| Client doesn't list the tools | Wrong `cwd`/path in config; use absolute paths and the venv's Python |
| `command not found: bloomberg-mcp` | Package not installed in the interpreter the client uses; use `python -m bloomberg_mcp.server` with an absolute python path instead |
| ChatGPT desktop doesn't list the tools | Restart the app and confirm the shared `~/.codex/config.toml` entry |
| ChatGPT web can't reach the server | Secure MCP Tunnel is stopped, unhealthy, or not associated with the target workspace |
| Port 8194 in use | Another blpapi client/instance is bound; close it or set `BLOOMBERG_PORT` |
