# Bloomberg MCP Server - PowerShell Run Script
#
# This script runs the MCP server locally on Windows.
# Requires: Bloomberg Terminal running, blpapi installed
#
# Usage:
#   .\run_server.ps1            - Run with stdio transport (for Claude Code)
#   .\run_server.ps1 --http     - Run with HTTP transport on port 8080
#   .\run_server.ps1 --sse      - Run with SSE transport on port 8080

param(
    [switch]$http,
    [switch]$sse,
    [int]$port = 8080
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pythonPath = if (Test-Path -LiteralPath $venvPython) {
    $venvPython
} else {
    (Get-Command python -ErrorAction Stop).Source
}

# Set Bloomberg connection (loopback for local Terminal)
$env:BLOOMBERG_HOST = "127.0.0.1"
$env:BLOOMBERG_PORT = "8194"

# Build arguments
$serverArgs = @()
if ($http) {
    $serverArgs += "--http"
    $serverArgs += "--port=$port"
} elseif ($sse) {
    $serverArgs += "--sse"
    $serverArgs += "--port=$port"
}

# Run the MCP server
Write-Host "Starting Bloomberg MCP Server..."
Write-Host "Bloomberg Host: $env:BLOOMBERG_HOST"
Write-Host "Bloomberg Port: $env:BLOOMBERG_PORT"

if ($serverArgs.Count -gt 0) {
    Write-Host "Transport: HTTP/SSE on port $port"
    & $pythonPath -m bloomberg_mcp.server @serverArgs
} else {
    Write-Host "Transport: stdio"
    & $pythonPath -m bloomberg_mcp.server
}
