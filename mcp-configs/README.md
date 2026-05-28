# MCP Client Config Templates

Drop-in configuration for connecting AI clients to the Bloomberg MCP server.
See [`../SETUP.md`](../SETUP.md) for full instructions.

In every template, replace `/ABSOLUTE/PATH/TO/bloomberg-mcp-tj` with the real
path to this repo on the machine that runs your Bloomberg Terminal.

| File | Client | Where it goes |
|------|--------|---------------|
| `claude-desktop.json` | Claude Desktop | merge into `claude_desktop_config.json` |
| `claude-code.mcp.json` | Claude Code | save as `.mcp.json` at your project root |
| `codex-config.toml` | OpenAI Codex CLI | merge into `~/.codex/config.toml` |

**ChatGPT** has no template — it connects to a remote HTTPS URL rather than a
local config file. Run `bloomberg-mcp --http --port=8080`, expose it through a
secured tunnel, and add the URL as a custom connector. See `../SETUP.md`.

## Using a virtualenv?

The templates assume `bloomberg-mcp` is on your PATH. If you installed into a
virtualenv, point at its interpreter instead, e.g.:

```json
{
  "command": "/ABSOLUTE/PATH/TO/venv/bin/python",
  "args": ["-m", "bloomberg_mcp.server"]
}
```
