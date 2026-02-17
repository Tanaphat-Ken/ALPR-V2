# PowerShell script to run all tests with coverage

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   ALPR General API - Test Runner" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if pytest is installed
$pytestInstalled = $null -ne (Get-Command pytest -ErrorAction SilentlyContinue)

if (-not $pytestInstalled) {
    Write-Host "pytest not found. Installing test dependencies..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio pytest-cov pytest-xdist httpx
}

Write-Host "Running all tests..." -ForegroundColor Green
Write-Host ""

# Run tests with coverage
pytest -v --cov=. --cov-report=html --cov-report=term-missing --cov-branch

# Check if tests passed
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Coverage report generated in: htmlcov/index.html"
    Write-Host "To view: start htmlcov/index.html"
} else {
    Write-Host ""
    Write-Host "Some tests failed. Please check the output above." -ForegroundColor Yellow
    exit 1
}
