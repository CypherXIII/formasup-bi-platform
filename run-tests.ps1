# Test runner script for all submodules (Windows)
# Executes tests for FormaSup BI Platform submodules

Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  FormaSup BI Platform - Test Runner" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan

# Function to run tests for a submodule
function Invoke-Tests {
    param(
        [string]$ModuleName,
        [string]$Path
    )

    Write-Host ""
    Write-Host "[TEST] Submodule: $ModuleName" -ForegroundColor Yellow
    Write-Host "[PATH] $Path" -ForegroundColor Gray

    if (Test-Path "$Path\tests") {
        Push-Location $Path
        Write-Host "[RUN] Running tests..." -ForegroundColor Green
        try {
            & python -m pytest tests/ -v --tb=short
            Write-Host "[OK] Tests for $ModuleName completed" -ForegroundColor Green
        }
        catch {
            Write-Host "[FAIL] Error running tests for $ModuleName" -ForegroundColor Red
        }
        Pop-Location
    }
    else {
        Write-Host "[WARN] No tests directory found for $ModuleName" -ForegroundColor Yellow
    }
}

# Run migration submodule tests
Invoke-Tests -ModuleName "Migration" -Path "migration"

# Run superset submodule tests
Invoke-Tests -ModuleName "Superset" -Path "superset"

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  Documentation Generation" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
$doxygen_exists = Get-Command doxygen -ErrorAction SilentlyContinue
if (-not $doxygen_exists) {
    Write-Host "[WARN] Doxygen is not installed. Skipping documentation generation." -ForegroundColor Yellow
}
else {
    Write-Host "[RUN] Generating Doxygen documentation..." -ForegroundColor Green
    & doxygen Doxyfile > doxygen.log 2>&1
    Write-Host "[OK] Doxygen documentation generated. See doxygen.log for details." -ForegroundColor Green
}


Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  Test Summary" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "Submodules tested: Migration, Superset" -ForegroundColor White
Write-Host "Test types: Unit, Integration, Configuration" -ForegroundColor White
Write-Host "Frameworks: pytest, unittest.mock" -ForegroundColor White
Write-Host "Coverage targets: Migration (80%), Superset (85%)" -ForegroundColor White
Write-Host ""
Write-Host "[OK] Test infrastructure setup completed successfully!" -ForegroundColor Green