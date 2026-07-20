@echo off
REM Bloomberg MCP Server - Local Run Script
REM
REM This script runs the MCP server locally on Windows.
REM Requires: Bloomberg Terminal running, blpapi installed
REM
REM Usage:
REM   run_server.bat          - Run with stdio transport (for Claude Code)
REM   run_server.bat --http   - Run with HTTP transport on port 8080
REM   run_server.bat --sse    - Run with SSE transport on port 8080

setlocal

REM Prefer the repo's virtual environment; fall back to Python on PATH.
set "PYTHON_CMD=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"

REM Set Bloomberg connection (loopback for local Terminal)
set BLOOMBERG_HOST=127.0.0.1
set BLOOMBERG_PORT=8194

REM Run the MCP server
"%PYTHON_CMD%" -m bloomberg_mcp.server %*

endlocal
