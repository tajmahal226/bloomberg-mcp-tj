# Setup Guide

This guide wires the Bloomberg MCP server into the AI clients you use:
**Claude Desktop**, **Claude Code**, **OpenAI Codex CLI**, and **ChatGPT**.

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
| **stdio** (default) | `bloomberg-mcp` | Claude Desktop, Claude Code, Codex — the client launches the process |
| **HTTP** | `bloomberg-mcp --http --port=8080` | ChatGPT connectors, remote/web clients |
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

### OpenAI Codex CLI

Add the block from [`mcp-configs/codex-config.toml`](mcp-configs/codex-config.toml)
to `~/.codex/config.toml`. Codex launches it over stdio like the Claude clients.

### ChatGPT

ChatGPT can't spawn a local process — it connects to a **remote MCP server over
a public HTTPS URL**, so there are extra steps:

1. Run the server in HTTP mode on the Terminal machine:
   ```bash
   bloomberg-mcp --http --port=8080
   ```
2. Expose it over HTTPS with a tunnel — [ngrok](https://ngrok.com),
   [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/),
   or [Tailscale](https://tailscale.com). Example:
   ```bash
   ngrok http 8080
   ```
3. In ChatGPT, open **Settings → Connectors** (Developer Mode), add a custom
   connector, and paste the public URL from your tunnel
   (e.g. `https://<subdomain>.ngrok.app/mcp`).

> ⚠️ **Security:** a tunnel exposes live Terminal data to the public internet.
> Always put authentication in front of it (ngrok auth, Cloudflare Access, or a
> Tailscale-only network) and never leave an open tunnel running unattended.
> Your Bloomberg Subscriber Agreement governs redistribution of this data —
> keep it to your own use.

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
| ChatGPT can't reach the server | Tunnel down, or URL missing the transport path (e.g. `/mcp` for HTTP) |
| Port 8194 in use | Another blpapi client/instance is bound; close it or set `BLOOMBERG_PORT` |
