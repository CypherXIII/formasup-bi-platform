#!/usr/bin/env pwsh
# Build Superset with French translations
# Author: FormaSup Auvergne

param(
    [string]$SupersetVersion = "6.0.0",
    [string]$ImageName = "superset-fr-formasup",
    [switch]$NoBuildCache = $false
)

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = $PSScriptRoot
$SUPERSET_DIR = Split-Path $SCRIPT_DIR -Parent
$SUPERSET_SRC = Join-Path $SUPERSET_DIR "apache-superset-src"

if (-not (Test-Path $SUPERSET_SRC)) {
    Write-Host "Error: $SUPERSET_SRC not found" -ForegroundColor Red
    exit 1
}

# Copy translations
$backupPo = Join-Path $SUPERSET_DIR "locales\backup-messages.po"
$targetPo = Join-Path $SUPERSET_SRC "superset\translations\fr\LC_MESSAGES\messages.po"

if (Test-Path $backupPo) {
    Copy-Item $backupPo -Destination $targetPo -Force
    Write-Host "[OK] French translations copied" -ForegroundColor Green
}

# Build Docker image
Write-Host "Building Docker image (this may take 10-20 minutes)..." -ForegroundColor Cyan

Push-Location $SUPERSET_SRC

$buildArgs = @("build", "--build-arg", "BUILD_TRANSLATIONS=true", "-t", "${ImageName}:${SupersetVersion}", "-t", "${ImageName}:latest", "--target", "lean", ".")

if ($NoBuildCache) {
    $buildArgs = @("build", "--no-cache", "--build-arg", "BUILD_TRANSLATIONS=true", "-t", "${ImageName}:${SupersetVersion}", "-t", "${ImageName}:latest", "--target", "lean", ".")
}

try {
    & docker @buildArgs
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
    Write-Host "[OK] Image ${ImageName}:${SupersetVersion} built" -ForegroundColor Green
} finally {
    Pop-Location
}
