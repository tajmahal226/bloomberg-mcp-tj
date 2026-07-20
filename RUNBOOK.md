# Operationalization Runbook

Every step, in order, to go from a fresh machine to Bloomberg data inside your AI
clients. Follow top to bottom — don't skip. Commands are given for **Windows
(PowerShell)** first, since Bloomberg Terminal runs on Windows, with **macOS/Linux**
notes where they differ.

Legend: 🪟 Windows · 🍎 macOS · 🐧 Linux · ⌨️ a command you type · ✅ a check you confirm

---

## Part 0 — Before you start

You need, on the **same physical machine**:

- [ ] A **Bloomberg Terminal** installed and you can log in to it.
- [ ] Admin rights to install software.
- [ ] ~30 minutes.

> ⚠️ **The #1 rule:** the MCP server and your AI client must run on the machine
> where the Terminal is logged in. The server reaches Bloomberg at
> `localhost:8194`; it cannot connect to a Terminal on a different computer.

---

## Part 1 — Confirm the Terminal API is alive

1. ⌨️ Launch Bloomberg Terminal and log in.
2. ⌨️ In the Terminal command line, type `API<GO>` (the API Developer's help page).
3. ✅ Confirm "Desktop API" / "B-PIPE" shows as enabled. The Desktop API listens
   on port `8194` — this is what the server connects to. If you don't have API
   access, contact your Bloomberg rep; nothing below will work without it.

---

## Part 2 — Install Python 3.10+

1. ⌨️ Check whether Python is already installed:
   - 🪟 `python --version`
   - 🍎🐧 `python3 --version`
2. If it prints `Python 3.10.x` or higher, skip to Part 3.
3. Otherwise install it:
   - 🪟 Download from <https://www.python.org/downloads/windows/>. **During
     install, tick "Add python.exe to PATH."**
   - 🍎 `brew install python@3.12` (or python.org installer).
   - 🐧 `sudo apt install python3 python3-venv python3-pip`
4. ✅ Re-open the terminal and confirm the version prints correctly.

---

## Part 3 — Get the code

1. ⌨️ Choose a folder and clone the repo:
   ```powershell
   cd $HOME
   git clone https://github.com/tajmahal226/bloomberg-mcp-tj.git
   cd bloomberg-mcp-tj
   ```
   (No git? Install from <https://git-scm.com/downloads>, or download the repo
   ZIP from GitHub and extract it.)
2. ✅ You are now inside the `bloomberg-mcp-tj` folder. Note its full path:
   - 🪟 `Get-Location`
   - 🍎🐧 `pwd`

   You'll need this path later. Call it **`<REPO>`**.

---

## Part 4 — Create a virtual environment (recommended)

Keeps Bloomberg deps isolated from system Python.

1. ⌨️ Create and activate it (from inside `<REPO>`):
   - 🪟 PowerShell:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
     > If activation is blocked, run once:
     > `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` then retry.
   - 🍎🐧:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
2. ✅ Your prompt now shows `(.venv)`. **Keep this shell open for Parts 5–6.**

---

## Part 5 — Install the Bloomberg SDKs

`blpapi` is **not** a normal pip package — it needs the Bloomberg **C++ SDK** on
disk and an environment variable pointing at it.

1. ⌨️ Download the **C++ Supported Release** (`blpapi_cpp_3.x.x.x`) from
   <https://www.bloomberg.com/professional/support/api-library/> and unzip it,
   e.g. to `C:\blp\blpapi_cpp_3.25.7.1`.
2. ⌨️ Point `BLPAPI_ROOT` at that folder **in the same shell**:
   - 🪟 `$env:BLPAPI_ROOT = "C:\blp\blpapi_cpp_3.25.7.1"`
   - 🍎🐧 `export BLPAPI_ROOT=/path/to/blpapi_cpp_3.25.7.1`
3. ⌨️ Install the Python SDK:
   ```
   pip install blpapi
   ```
4. ✅ Confirm it imports:
   ```
   python -c "import blpapi; print(blpapi.__version__)"
   ```
   If this errors, fix it before continuing — re-check `BLPAPI_ROOT` points at the
   folder that contains `bin/` and `include/`.

> 🪟 **Make `BLPAPI_ROOT` permanent** so you don't set it every time:
> `setx BLPAPI_ROOT "C:\blp\blpapi_cpp_3.25.7.1"` (takes effect in new shells).

---

## Part 6 — Install this package + wire up your clients (automated)

This single script installs `bloomberg-mcp` and configures every AI client it
finds. Run it from inside `<REPO>` with your venv still active.

1. ⌨️ **Preview** what it will do (changes nothing):
   ```
   python scripts/setup.py --dry-run
   ```
   ✅ Read the output. It lists the launch command and which clients it will
   configure.
2. ⌨️ **Run it for real:**
   ```
   python scripts/setup.py
   ```
   It will:
   - `pip install -e .` (creates the `bloomberg-mcp` command),
   - write/merge config for Claude Desktop, Claude Code, ChatGPT desktop, and Codex **if they're
     installed** (backing up any file it touches),
   - print optional Secure MCP Tunnel steps for ChatGPT web.
3. ✅ Note the summary at the end. Any client it skipped just means it wasn't
   detected — install that client and re-run, or configure it manually (Part 7).

> Re-running is safe and idempotent: it backs up existing config and updates the
> `bloomberg` entry in place.

If you prefer to do it by hand, skip the script and use **Part 7**.

---

## Part 7 — Manual client configuration (only if you skipped the script)

Templates live in [`mcp-configs/`](mcp-configs/). In each, replace
`/ABSOLUTE/PATH/TO/bloomberg-mcp-tj` with your **`<REPO>`** path, and — if you
used a venv — replace the command with your venv's Python (see note at the end).

### 7a. Claude Desktop
1. ⌨️ Install Claude Desktop (<https://claude.ai/download>) and run it once.
2. ⌨️ Open the config file (create it if missing):
   - 🪟 `%APPDATA%\Claude\claude_desktop_config.json`
   - 🍎 `~/Library/Application Support/Claude/claude_desktop_config.json`
3. ⌨️ Paste the contents of `mcp-configs/claude-desktop.json`, fixing the path.
4. ⌨️ **Fully quit** Claude Desktop (tray icon → Quit) and reopen it.

### 7b. Claude Code
- ⌨️ Easiest, from inside `<REPO>`:
  ```
  claude mcp add -s user bloomberg -- bloomberg-mcp
  ```
- Or commit/copy `mcp-configs/claude-code.mcp.json` as `.mcp.json` at your
  project root.

### 7c. ChatGPT desktop and OpenAI Codex
1. ⌨️ Open `~/.codex/config.toml` (create it if missing).
2. ⌨️ Append the block from `mcp-configs/codex-config.toml`, fixing the path.
3. ✅ Restart the desktop app; ChatGPT desktop, Codex CLI, and Codex IDE share
   this configuration.

### 7d. ChatGPT web — see Part 9 (optional).

---

## Part 8 — Verify each client

For **each** client you configured:

1. ⌨️ Open the client.
2. ✅ Confirm a `bloomberg` MCP server / its tools appear:
   - Claude Desktop: hammer/tools icon in the message box.
   - Claude Code: type `/mcp` and look for `bloomberg`.
   - Codex: it lists MCP servers on startup.
3. ⌨️ Ask, in plain language:
   > "Use the bloomberg tools to get PX_LAST for AAPL US Equity."
4. ✅ It should call `bloomberg_get_reference_data` and return a live price. 🎉

If it fails to connect → **Part 10**.

---

## Part 9 — ChatGPT web (optional, extra steps)

ChatGPT web cannot launch the local stdio process. Use OpenAI Secure MCP Tunnel
so the server stays private rather than publishing it on the internet.

1. ⌨️ Create a tunnel in OpenAI Platform tunnel settings.
2. ⌨️ Run `tunnel-client` on this machine with a local stdio profile pointing to
   `.venv\Scripts\python.exe -m bloomberg_mcp.server`.
3. ⌨️ In ChatGPT developer mode, create an app and select the tunnel.
4. ✅ Ask ChatGPT the same AAPL question as in Part 8.

> Keep this optional. You are responsible for complying with your Bloomberg
> Subscriber Agreement; the data is for your use only.

---

## Part 10 — Troubleshooting

| Symptom | Cause → Fix |
|---|---|
| `Connection failed` / `Failed to start Bloomberg session` | Terminal not running/logged in, or you're not on the Terminal machine. Log in and retry. |
| Client shows no `bloomberg` tools | Wrong path/command in config. Use the **absolute** `<REPO>` path and your **venv's** Python (see below). Restart the client. |
| `command not found: bloomberg-mcp` | The client uses a different Python than your venv. Point it at the venv interpreter (note below). |
| `ImportError: blpapi` | `BLPAPI_ROOT` not set in the env the client launches with, or blpapi not installed in that interpreter. Make `BLPAPI_ROOT` permanent (Part 5 note) and reinstall blpapi. |
| Port `8194` busy | Another blpapi app is bound. Close it, or set `BLOOMBERG_PORT` to your Terminal's API port. |
| ChatGPT desktop can't see tools | Restart the app and verify the shared `~/.codex/config.toml` block. |
| ChatGPT web can't reach server | Check `tunnel-client`, its health output, and the tunnel's workspace association. |

### Pointing a client at your venv's Python (common fix)
If `bloomberg-mcp` isn't found, use the venv interpreter explicitly in the config:
- 🪟 command = `<REPO>\.venv\Scripts\python.exe`, args = `["-m", "bloomberg_mcp.server"]`
- 🍎🐧 command = `<REPO>/.venv/bin/python`, args = `["-m", "bloomberg_mcp.server"]`

Find the exact path with `where python` (🪟) or `which python` (🍎🐧) while the
venv is active.

---

## Part 11 — Day-to-day use

- **stdio clients (Claude Desktop, Claude Code, ChatGPT desktop, Codex):** nothing to start — they
  launch the server automatically when they open. Just keep the **Terminal logged
  in**.
- **ChatGPT web:** keep `tunnel-client` running only when web access is needed.
- **Updating the server:**
  ```
  cd <REPO>
  git pull
  pip install -e .      # venv active
  ```
  Then restart your clients.

You're operational. ✅
