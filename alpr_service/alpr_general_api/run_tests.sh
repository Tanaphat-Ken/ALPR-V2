#!/bin/bash
# Script to run all tests with coverage

echo "========================================="
echo "   ALPR General API - Test Runner"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null
then
    echo "${YELLOW}pytest not found. Installing test dependencies...${NC}"
    pip install pytest pytest-asyncio pytest-cov pytest-xdist httpx
fi

echo "${GREEN}Running all tests...${NC}"
echo ""

# Run tests with coverage
pytest -v --cov=. --cov-report=html --cov-report=term-missing --cov-branch

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Coverage report generated in: htmlcov/index.html"
    echo "To view: open htmlcov/index.html"
else
    echo ""
    echo "${YELLOW}✗ Some tests failed. Please check the output above.${NC}"
    exit 1
fi
