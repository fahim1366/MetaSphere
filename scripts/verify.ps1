<#
.SYNOPSIS
    Root automated verification script for MetaSphere Enterprise Data Catalog.
.DESCRIPTION
    Runs deterministic offline quality gates (linting, type-checking, formatting, and unit tests).
    Optionally runs integration tests and benchmarks when flag is specified.
.PARAMETER RunIntegration
    Run container-dependent integration tests (requires PostgreSQL and Redis up).
.PARAMETER RunBenchmark
    Run latency benchmark tests.
#>

[CmdletBinding()]
param(
    [switch]$RunIntegration,
    [switch]$RunBenchmark
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host " MetaSphere Automated Quality Gates & Verification" -ForegroundColor Cyan
Write-Host " Root: $RepoRoot" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

function Run-Step {
    param(
        [string]$Name,
        [string]$WorkDir,
        [string]$Executable,
        [string[]]$Arguments
    )

    Write-Host "`n--> [$Name] in $WorkDir" -ForegroundColor Yellow
    Write-Host "    $Executable $($Arguments -join ' ')" -ForegroundColor Gray

    Push-Location $WorkDir
    try {
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) {
            Write-Host "FAILED: $Name exited with code $LASTEXITCODE" -ForegroundColor Red
            Pop-Location
            exit $LASTEXITCODE
        }
        Write-Host "PASSED: $Name" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
}

# Resolve backend virtualenv tools
$VenvBin = Join-Path $BackendDir ".venv\Scripts"
$Ruff = Join-Path $VenvBin "ruff.exe"
$Mypy = Join-Path $VenvBin "mypy.exe"
$Pytest = Join-Path $VenvBin "pytest.exe"

# 1. Backend Linting
Run-Step -Name "Backend Ruff Lint" -WorkDir $BackendDir -Executable $Ruff -Arguments @("check", ".")

# 2. Backend Format Check
Run-Step -Name "Backend Ruff Format Check" -WorkDir $BackendDir -Executable $Ruff -Arguments @("format", "--check", ".")

# 3. Backend Static Type Analysis
Run-Step -Name "Backend Mypy Type Analysis" -WorkDir $BackendDir -Executable $Mypy -Arguments @("app")

# 4. Backend Unit Tests
Run-Step -Name "Backend Pytest Unit Tests" -WorkDir $BackendDir -Executable $Pytest -Arguments @("tests/unit", "-m", "unit")

# 5. Frontend ESLint
Run-Step -Name "Frontend ESLint" -WorkDir $FrontendDir -Executable "npm.cmd" -Arguments @("run", "lint")

# 6. Frontend Vitest Unit Tests
Run-Step -Name "Frontend Vitest Unit Tests" -WorkDir $FrontendDir -Executable "npm.cmd" -Arguments @("run", "test")

# 7. Frontend Production Build
Run-Step -Name "Frontend Production Build" -WorkDir $FrontendDir -Executable "npm.cmd" -Arguments @("run", "build")

# Optional Integration Tests
if ($RunIntegration) {
    Write-Host "`n[Integration Testing Mode Enabled]" -ForegroundColor Magenta
    Run-Step -Name "Backend Integration Tests" -WorkDir $BackendDir -Executable $Pytest -Arguments @("tests/integration", "-m", "integration")
}

# Optional Latency Benchmarks
if ($RunBenchmark) {
    Write-Host "`n[Benchmark Mode Enabled]" -ForegroundColor Magenta
    Run-Step -Name "Backend Readiness Latency Benchmark" -WorkDir $BackendDir -Executable $Pytest -Arguments @("tests/integration/test_health_bench.py", "-m", "benchmark", "-s")
}

Write-Host "`n==============================================================" -ForegroundColor Green
Write-Host " All MetaSphere Quality Gates Succeeded! (100% PASS)" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
exit 0
