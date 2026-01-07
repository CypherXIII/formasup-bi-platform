#!/usr/bin/env bash
# Test runner script for all submodules

set -e

echo "==============================================================="
echo "  FormaSup BI Platform - Test Runner"
echo "==============================================================="

# Function to run tests for a submodule
run_tests() {
    local module=$1
    local path=$2

    echo ""
    echo "[TEST] Submodule: $module"
    echo "[PATH] $path"

    if [ -d "$path/tests" ]; then
        cd "$path"
        echo "[RUN] Running tests..."
        python -m pytest tests/ -v --tb=short
        echo "[OK] Tests for $module completed"
        cd - > /dev/null
    else
        echo "[WARN] No tests directory found for $module"
    fi
}

# Run migration submodule tests
run_tests "Migration" "migration"

# Run superset submodule tests
run_tests "Superset" "superset"

echo ""
echo "==============================================================="
echo "  Documentation Generation"
echo "==============================================================="
if ! [ -x "$(command -v doxygen)" ]; then
  echo "[WARN] Doxygen is not installed. Skipping documentation generation."
else
  echo "[RUN] Generating Doxygen documentation..."
  doxygen Doxyfile > doxygen.log 2>&1
  echo "[OK] Doxygen documentation generated. See doxygen.log for details."
fi

echo ""
echo "==============================================================="
echo "  Test Summary"
echo "==============================================================="
echo "Submodules tested: Migration, Superset"
echo "Test types: Unit, Integration, Configuration"
echo "Frameworks: pytest, unittest.mock"
echo "Coverage targets: Migration (80%), Superset (85%)"
echo ""
echo "[OK] Test infrastructure setup completed successfully!"