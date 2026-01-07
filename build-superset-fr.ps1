#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build Superset avec le francais comme langue par defaut

.DESCRIPTION
    Ce script suit la procedure officielle de Superset:
    1. Copie le fichier de traductions (backup-messages.po)
    2. Build avec BUILD_TRANSLATIONS=true (compile .po -> .mo et .json)
    
    La configuration du francais se fait via superset_config.py:
    - BABEL_DEFAULT_LOCALE = "fr"
    - LANGUAGES = {"fr": {"flag": "fr", "name": "Français"}}

.NOTES
    Auteur: FormaSup Auvergne
    Date: Janvier 2026
#>

[CmdletBinding()]
param(
    [string]$SupersetVersion = "6.0.0",
    [string]$ImageName = "superset-fr-formasup",
    [switch]$NoBuildCache = $false
)

$ErrorActionPreference = "Stop"

Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  Build Superset FormaSup - Francais (procedure officielle)" -ForegroundColor Cyan  
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

$SCRIPT_DIR = $PSScriptRoot
$SUPERSET_SRC = Join-Path $SCRIPT_DIR "superset\apache-superset-src"

# Verifier que le repertoire existe
if (-not (Test-Path $SUPERSET_SRC)) {
    Write-Host "Erreur: Le repertoire $SUPERSET_SRC n'existe pas" -ForegroundColor Red
    Write-Host "Clonez d'abord le repo: git clone --depth 1 --branch 6.0.0 https://github.com/apache/superset.git apache-superset-src" -ForegroundColor Yellow
    exit 1
}

# Etape 1: Reset du code source (propre, sans modifications)
Write-Host "[Etape 1/3] Reinitialisation du code source..." -ForegroundColor Yellow
Push-Location $SUPERSET_SRC
try {
    git fetch --tags 2>&1 | Out-Null
    git reset --hard $SupersetVersion 2>&1 | Out-Null
    git clean -fdx 2>&1 | Out-Null
    Write-Host "   [OK] Code source reinitialise sur le tag $SupersetVersion" -ForegroundColor Green
} catch {
    Write-Host "   [ATTENTION] Impossible de reinitialiser: $_" -ForegroundColor Yellow
} finally {
    Pop-Location
}

# Etape 2: Copier le fichier de traductions enrichi
Write-Host ""
Write-Host "[Etape 2/3] Copie des traductions francaises..." -ForegroundColor Yellow

$backupPo = Join-Path $SCRIPT_DIR "backup-messages.po"
$targetPo = Join-Path $SUPERSET_SRC "superset\translations\fr\LC_MESSAGES\messages.po"

if (Test-Path $backupPo) {
    Copy-Item $backupPo -Destination $targetPo -Force
    $backupSize = (Get-Item $backupPo).Length
    Write-Host "   [OK] messages.po copie ($backupSize octets)" -ForegroundColor Green
} else {
    Write-Host "   [INFO] Pas de backup-messages.po, utilisation des traductions officielles" -ForegroundColor Gray
}

# Etape 3: Build de l'image Docker avec BUILD_TRANSLATIONS=true
Write-Host ""
Write-Host "[Etape 3/3] Construction de l'image Docker..." -ForegroundColor Yellow
Write-Host "   [INFO] BUILD_TRANSLATIONS=true active:" -ForegroundColor Gray
Write-Host "          - npm run build-translation (frontend: .po -> .json)" -ForegroundColor Gray
Write-Host "          - pybabel compile (backend: .po -> .mo)" -ForegroundColor Gray
Write-Host "   [INFO] Cela peut prendre 10-20 minutes..." -ForegroundColor Gray
Write-Host ""

Push-Location $SUPERSET_SRC

$buildArgs = @(
    "build",
    "--build-arg", "BUILD_TRANSLATIONS=true",
    "-t", "${ImageName}:${SupersetVersion}",
    "-t", "${ImageName}:latest",
    "--target", "lean",
    "."
)

if ($NoBuildCache) {
    $buildArgs = @(
        "build", 
        "--no-cache",
        "--build-arg", "BUILD_TRANSLATIONS=true", 
        "-t", "${ImageName}:${SupersetVersion}", 
        "-t", "${ImageName}:latest", 
        "--target", "lean", 
        "."
    )
}

try {
    & docker @buildArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build a echoue avec le code $LASTEXITCODE"
    }
    Write-Host ""
    Write-Host "   [OK] Image construite avec succes" -ForegroundColor Green
} catch {
    Write-Host "   [ERREUR] Build echoue: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "  BUILD TERMINE AVEC SUCCES" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Image creee: ${ImageName}:${SupersetVersion}" -ForegroundColor Cyan
Write-Host "             ${ImageName}:latest" -ForegroundColor Cyan
Write-Host ""
Write-Host "Etapes suivantes:" -ForegroundColor Yellow
Write-Host "   1. docker compose build superset" -ForegroundColor White
Write-Host "   2. docker compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "Configuration du francais via superset_config.py:" -ForegroundColor Gray
Write-Host "   - BABEL_DEFAULT_LOCALE = 'fr'" -ForegroundColor Gray
Write-Host "   - LANGUAGES = {'fr': {'flag': 'fr', 'name': 'Francais'}}" -ForegroundColor Gray
Write-Host ""
