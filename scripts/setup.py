#!/usr/bin/env python3
"""One-command local setup for Bloomberg MCP.

Run this ON THE MACHINE THAT HAS THE BLOOMBERG TERMINAL:

    python scripts/setup.py

It will:
  1. Check your Python and blpapi installation.
  2. Install this package (pip install -e .) so the `bloomberg-mcp` command exists.
  3. Detect which AI clients you have and write/merge their MCP config
     (Claude Desktop, Claude Code, OpenAI Codex), backing up anything it changes.
  4. Print next steps for ChatGPT (which needs a remote URL, not a local config).

Nothing here talks to the Terminal — it only wires up the clients. Re-running is
safe: existing config is backed up and the "bloomberg" entry is updated in place.

Flags:
  --transport-cmd "..."   Override the launch command (default: auto-detected).
  --dry-run               Show what would change without writing anything.
  --skip-install          Don't run pip install -e . (just write configs).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM = platform.system()  # "Windows" | "Darwin" | "Linux"

BLOOMBERG_ENV = {"BLOOMBERG_HOST": "localhost", "BLOOMBERG_PORT": "8194"}


def info(msg: str) -> None:
    print(f"  {msg}")


def section(msg: str) -> None:
    print(f"\n=== {msg} ===")


def backup(path: Path) -> None:
    """Copy an existing file to <name>.bak-<timestamp> before we modify it."""
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = path.with_suffix(path.suffix + f".bak-{stamp}")
        shutil.copy2(path, dest)
        info(f"backed up existing config -> {dest}")


# --------------------------------------------------------------------------- #
# Step 1 & 2: environment checks + install
# --------------------------------------------------------------------------- #
def check_python() -> None:
    section("Checking Python")
    if sys.version_info < (3, 10):  # noqa: UP036 - runtime guard for older pythons
        sys.exit(f"Python 3.10+ required, found {platform.python_version()}")
    info(f"Python {platform.python_version()} at {sys.executable}")


def check_blpapi() -> None:
    section("Checking Bloomberg SDK (blpapi)")
    try:
        import blpapi  # noqa: F401

        info("blpapi is importable.")
    except ImportError:
        info("blpapi is NOT installed in this interpreter.")
        info("Install it before using the server (it cannot be pip-installed alone):")
        info("  1. export BLPAPI_ROOT=/path/to/blpapi_cpp_3.x.x.x")
        info("  2. pip install blpapi")
        info("Continuing with client setup anyway.")


def install_package(dry_run: bool) -> None:
    section("Installing bloomberg-mcp")
    cmd = [sys.executable, "-m", "pip", "install", "-e", str(REPO_ROOT)]
    if dry_run:
        info("DRY RUN: would run " + " ".join(cmd))
        return
    info(" ".join(cmd))
    subprocess.run(cmd, check=True)


def resolve_launch_command(override: str | None) -> list[str]:
    """Figure out how clients should launch the server."""
    if override:
        return override.split()
    exe = shutil.which("bloomberg-mcp")
    if exe:
        return [exe]
    # Fall back to the current interpreter running the module.
    return [sys.executable, "-m", "bloomberg_mcp.server"]


# --------------------------------------------------------------------------- #
# Step 3: per-client config writers
# --------------------------------------------------------------------------- #
def server_entry(launch: list[str]) -> dict:
    return {
        "command": launch[0],
        "args": launch[1:],
        "env": dict(BLOOMBERG_ENV),
    }


def merge_json_config(path: Path, launch: list[str], dry_run: bool) -> None:
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            info(f"WARNING: {path} is not valid JSON; leaving it untouched.")
            return
    servers = data.setdefault("mcpServers", {})
    servers["bloomberg"] = server_entry(launch)
    if dry_run:
        info(f"DRY RUN: would write bloomberg entry to {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    path.write_text(json.dumps(data, indent=2) + "\n")
    info(f"wrote {path}")


def claude_desktop_path() -> Path | None:
    if SYSTEM == "Windows":
        base = os.environ.get("APPDATA")
        return Path(base) / "Claude" / "claude_desktop_config.json" if base else None
    if SYSTEM == "Darwin":
        return (Path.home()
                / "Library/Application Support/Claude/claude_desktop_config.json")
    return Path.home() / ".config/Claude/claude_desktop_config.json"


def setup_claude_desktop(launch: list[str], dry_run: bool) -> None:
    section("Claude Desktop")
    path = claude_desktop_path()
    if path is None:
        info("Could not determine config path; skipping.")
        return
    # Only configure if Claude Desktop looks installed (its dir exists) or user opts in.
    if not path.parent.exists():
        info(f"No Claude Desktop config dir at {path.parent} — skipping.")
        info("(Install Claude Desktop, then re-run, or copy "
             "mcp-configs/claude-desktop.json manually.)")
        return
    merge_json_config(path, launch, dry_run)
    info("Restart Claude Desktop to load the server.")


def setup_claude_code(launch: list[str], dry_run: bool) -> None:
    section("Claude Code")
    claude_cli = shutil.which("claude")
    if claude_cli:
        cmd = [claude_cli, "mcp", "add", "-s", "user", "bloomberg", "--", *launch]
        if dry_run:
            info("DRY RUN: would run " + " ".join(cmd))
            return
        info(" ".join(cmd))
        # `claude mcp add` errors if the name exists; remove first, ignore failure.
        subprocess.run([claude_cli, "mcp", "remove", "-s", "user", "bloomberg"],
                       capture_output=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            info("registered with Claude Code (user scope).")
        else:
            info(f"claude mcp add failed: {result.stderr.strip()}")
            info("Falling back to a project-scoped .mcp.json.")
            merge_json_config(REPO_ROOT / ".mcp.json", launch, dry_run)
    else:
        info("`claude` CLI not found; writing a project-scoped .mcp.json instead.")
        merge_json_config(REPO_ROOT / ".mcp.json", launch, dry_run)


def setup_codex(launch: list[str], dry_run: bool) -> None:
    section("OpenAI Codex CLI")
    path = Path.home() / ".codex" / "config.toml"
    if not path.parent.exists():
        info("No ~/.codex directory — Codex doesn't look installed. Skipping.")
        info("(Install Codex, then re-run, or copy "
             "mcp-configs/codex-config.toml manually.)")
        return
    existing = path.read_text() if path.exists() else ""
    if "[mcp_servers.bloomberg]" in existing:
        info("A [mcp_servers.bloomberg] block already exists — leaving it.")
        info("Edit it by hand if you need to change the command.")
        return
    args_toml = ", ".join(f'"{a}"' for a in launch[1:])
    block = (
        "\n[mcp_servers.bloomberg]\n"
        f'command = "{launch[0]}"\n'
        f"args = [{args_toml}]\n"
        f'cwd = "{REPO_ROOT}"\n\n'
        "[mcp_servers.bloomberg.env]\n"
        'BLOOMBERG_HOST = "localhost"\n'
        'BLOOMBERG_PORT = "8194"\n'
    )
    if dry_run:
        info(f"DRY RUN: would append a [mcp_servers.bloomberg] block to {path}")
        return
    backup(path)
    with path.open("a") as fh:
        fh.write(block)
    info(f"appended bloomberg block to {path}")


def chatgpt_notes() -> None:
    section("ChatGPT (manual — remote URL only)")
    info("ChatGPT can't launch a local process. To use it:")
    info("  1. Run:  bloomberg-mcp --http --port=8080")
    info("  2. Expose port 8080 over HTTPS with a SECURED tunnel "
         "(ngrok/Cloudflare/Tailscale).")
    info("  3. Add that URL as a custom connector in ChatGPT (Settings -> Connectors).")
    info("  See SETUP.md for the security warning — this exposes live Terminal data.")


# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Local setup for Bloomberg MCP.")
    parser.add_argument("--transport-cmd", default=None,
                        help="Override the launch command clients use.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show changes without writing anything.")
    parser.add_argument("--skip-install", action="store_true",
                        help="Skip 'pip install -e .'.")
    args = parser.parse_args()

    print("Bloomberg MCP — local setup")
    print(f"Repo: {REPO_ROOT}")
    print(f"OS:   {SYSTEM}")
    if args.dry_run:
        print("(dry run — no files will be changed)")

    check_python()
    check_blpapi()
    if not args.skip_install:
        try:
            install_package(args.dry_run)
        except subprocess.CalledProcessError as exc:
            sys.exit(f"pip install failed ({exc}). Fix the error above and re-run.")

    launch = resolve_launch_command(args.transport_cmd)
    section("Launch command clients will use")
    info(" ".join(launch))

    setup_claude_desktop(launch, args.dry_run)
    setup_claude_code(launch, args.dry_run)
    setup_codex(launch, args.dry_run)
    chatgpt_notes()

    section("Done")
    info("Verify in any connected client: \"Use the bloomberg tools to get "
         "PX_LAST for AAPL US Equity.\"")
    info("If it fails to connect, make sure the Terminal is running and logged in.")


if __name__ == "__main__":
    main()
