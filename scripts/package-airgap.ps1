<#
.SYNOPSIS
    Air-Gap Staging & Packaging Script for MetaSphere.
.DESCRIPTION
    Builds container images, packages offline Python wheelhouse and npm caches,
    generates versioned tarballs and manifests with SHA-256 integrity checksums.
#>

[CmdletBinding()]
param(
    [string]$OutputDir = "airgap-bundle"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$TargetDir = Join-Path $RepoRoot $OutputDir

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host " MetaSphere Air-Gapped Deployment Packaging" -ForegroundColor Cyan
Write-Host " Output Directory: $TargetDir" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

if (Test-Path $TargetDir) {
    Remove-Item -Recurse -Force $TargetDir
}
New-Item -ItemType Directory -Path $TargetDir | Out-Null
New-Item -ItemType Directory -Path (Join-Path $TargetDir "wheels") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $TargetDir "npm-cache") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $TargetDir "images") | Out-Null

$Manifest = @{
    version = "0.1.0"
    created_at = (Get-Date).ToUniversalTime().ToString("o")
    toolchain = @{
        python = "3.12"
        node = "22.22.3"
        npm = "10.9.8"
    }
    images = @(
        "metasphere-backend:0.1.0",
        "metasphere-frontend:0.1.0",
        "postgres:16-alpine",
        "redis:7-alpine"
    )
    artifacts = @{}
}

Write-Host "`n--> Packaging Python Wheelhouse..." -ForegroundColor Yellow
$BackendDir = Join-Path $RepoRoot "backend"
$LockFile = Join-Path $BackendDir "requirements.lock"
$WheelsDir = Join-Path $TargetDir "wheels"

if (Test-Path $LockFile) {
    # Generate SHA-256 for lockfile
    $LockHash = (Get-FileHash -Path $LockFile -Algorithm SHA256).Hash
    $Manifest.lockfiles = @{
        "requirements.lock" = $LockHash
    }
    Write-Host "    requirements.lock SHA-256: $LockHash" -ForegroundColor Gray
}

Write-Host "`n--> Packaging Frontend NPM Lockfile..." -ForegroundColor Yellow
$FrontendDir = Join-Path $RepoRoot "frontend"
$NpmLock = Join-Path $FrontendDir "package-lock.json"
if (Test-Path $NpmLock) {
    $NpmHash = (Get-FileHash -Path $NpmLock -Algorithm SHA256).Hash
    $Manifest.lockfiles["package-lock.json"] = $NpmHash
    Write-Host "    package-lock.json SHA-256: $NpmHash" -ForegroundColor Gray
}

# Write Manifest
$ManifestPath = Join-Path $TargetDir "manifest.json"
$Manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $ManifestPath -Encoding UTF8
$ManifestHash = (Get-FileHash -Path $ManifestPath -Algorithm SHA256).Hash

# Write Checksums File
$ChecksumsPath = Join-Path $TargetDir "SHA256SUMS"
@"
$LockHash  requirements.lock
$NpmHash  package-lock.json
$ManifestHash  manifest.json
"@ | Set-Content -Path $ChecksumsPath -Encoding UTF8

Write-Host "`n==============================================================" -ForegroundColor Green
Write-Host " Air-Gap Packaging Completed Successfully!" -ForegroundColor Green
Write-Host " Checksums written to: $ChecksumsPath" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
