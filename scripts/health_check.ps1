[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$checks = [System.Collections.Generic.List[object]]::new()

function Add-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail
    )
    $checks.Add([pscustomobject]@{
        Check = $Name
        Status = if ($Passed) { "PASS" } else { "FAIL" }
        Detail = $Detail
    })
}

Add-Check "Virtual environment" (Test-Path -LiteralPath $pythonPath) $pythonPath

if (Test-Path -LiteralPath $pythonPath) {
    try {
        $importResult = & $pythonPath -c "import blpapi, bloomberg_mcp; print('blpapi and bloomberg_mcp import successfully')"
        Add-Check "Python imports" ($LASTEXITCODE -eq 0) ($importResult -join " ")
    } catch {
        Add-Check "Python imports" $false $_.Exception.Message
    }
}

$bbcomm = Get-Process bbcomm -ErrorAction SilentlyContinue | Select-Object -First 1
Add-Check "Bloomberg bbcomm" ($null -ne $bbcomm) $(if ($bbcomm) { "PID $($bbcomm.Id)" } else { "Not running" })

$listener = Get-NetTCPConnection -LocalPort 8194 -State Listen -ErrorAction SilentlyContinue |
    Where-Object LocalAddress -in @("127.0.0.1", "::1") |
    Select-Object -First 1
Add-Check "Bloomberg API port" ($null -ne $listener) $(if ($listener) { "$($listener.LocalAddress):8194 listening" } else { "No loopback listener" })

try {
    $servers = & codex mcp list --json | ConvertFrom-Json
    $bloomberg = $servers | Where-Object name -eq "bloomberg" | Select-Object -First 1
    $expected = [System.IO.Path]::GetFullPath($pythonPath)
    $actual = if ($bloomberg) { [System.IO.Path]::GetFullPath($bloomberg.transport.command) } else { "" }
    $configOk = $bloomberg.enabled -and ($actual -eq $expected)
    Add-Check "Shared Codex config" $configOk $(if ($bloomberg) { "$actual; enabled=$($bloomberg.enabled)" } else { "bloomberg entry missing" })
} catch {
    Add-Check "Shared Codex config" $false $_.Exception.Message
}

if ((Test-Path -LiteralPath $pythonPath) -and $listener) {
    try {
        $probe = @'
import asyncio
import json
from bloomberg_mcp.server import ReferenceDataInput, bloomberg_get_reference_data

params = ReferenceDataInput(
    securities=["AAPL US Equity"],
    fields=["PX_LAST"],
    response_format="json",
)
result = asyncio.run(bloomberg_get_reference_data(params))
payload = json.loads(result)
value = payload[0]["fields"]["PX_LAST"]
print(f"AAPL US Equity PX_LAST={value}")
'@
        $liveResult = & $pythonPath -c $probe
        Add-Check "Live Bloomberg request" ($LASTEXITCODE -eq 0) ($liveResult -join " ")
    } catch {
        Add-Check "Live Bloomberg request" $false $_.Exception.Message
    }
} else {
    Add-Check "Live Bloomberg request" $false "Skipped because Python or port 8194 is unavailable"
}

$checks | Format-Table -AutoSize
if ($checks.Status -contains "FAIL") {
    exit 1
}
