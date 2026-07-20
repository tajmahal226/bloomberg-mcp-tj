# MCP Client Config Templates

Drop-in configuration for connecting AI clients to the Bloomberg MCP server.
See [`../SETUP.md`](../SETUP.md) for full instructions.

In every template, replace `/ABSOLUTE/PATH/TO/bloomberg-mcp-tj` with the real
path to this repo on the machine that runs your Bloomberg Terminal.

| File | Client | Where it goes |
|------|--------|---------------|
| `claude-desktop.json` | Claude Desktop | merge into `claude_desktop_config.json` |
| `claude-code.mcp.json` | Claude Code | save as `.mcp.json` at your project root |
| `codex-config.toml` | ChatGPT desktop, Codex CLI, Codex IDE | merge into `~/.codex/config.toml` |

The **ChatGPT desktop app** shares the Codex MCP configuration and can launch
this local stdio server directly. **ChatGPT web** needs a remote connection;
use OpenAI Secure MCP Tunnel rather than exposing the server publicly. See
`../SETUP.md`.

## Using a virtualenv?

The templates assume `bloomberg-mcp` is on your PATH. If you installed into a
virtualenv, point at its interpreter instead, e.g.:

```json
{
  "command": "/ABSOLUTE/PATH/TO/venv/bin/python",
  "args": ["-m", "bloomberg_mcp.server"]
}
```
