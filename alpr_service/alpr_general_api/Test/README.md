# Testing Guide for ALPR General API

This directory contains comprehensive test suites for the ALPR General API service.

## 📁 Test Structure

```
Test/
├── conftest.py              # Pytest fixtures and configuration
├── test_auth.py            # Authentication tests (50+ test cases)
├── test_token.py           # Token management tests (40+ test cases)
├── test_quota.py           # Quota system tests (30+ test cases)
├── test_subscription.py    # Subscription tests (30+ test cases)
└── test_user.py            # User management tests (30+ test cases)
```

## 🎯 Test Coverage

### Authentication Tests (`test_auth.py`)

- ✅ User registration (valid, duplicate, invalid data)
- ✅ User login (success, wrong password, non-existent user)
- ✅ JWT token generation and validation
- ✅ Password hashing and verification
- ✅ Protected endpoint access
- ✅ Edge cases (SQL injection, long values, concurrent requests)

### Token Management Tests (`test_token.py`)

- ✅ Token CRUD operations
- ✅ Service type filtering (API, WEBSOCKET, VIDEO_WEBSOCKET, RTSP)
- ✅ Token validation and authorization
- ✅ Max token limits per tier
- ✅ Token expiration handling
- ✅ Feature-based token creation

### Quota System Tests (`test_quota.py`)

- ✅ Quota deduction on API/WebSocket calls
- ✅ Multiple successive deductions
- ✅ Zero quota blocking
- ✅ Quota cannot go negative
- ✅ Quota validation before operations
- ✅ Different limits across tiers (1000, 5000)
- ✅ Feature access validation

### Subscription Tests (`test_subscription.py`)

- ✅ Subscription creation and management
- ✅ TIER_1, TIER_2, TIER_3 configurations
- ✅ Subscription upgrade/downgrade
- ✅ Feature access per tier
- ✅ Pricing verification
- ✅ Max token limits
- ✅ Active/inactive subscription handling

### User Management Tests (`test_user.py`)

- ✅ User CRUD operations
- ✅ User information retrieval
- ✅ User profile updates
- ✅ Password verification
- ✅ User-subscription relationships
- ✅ Edge cases (duplicates, special characters, null values)

## 🚀 Running Tests

### Prerequisites

1. **Install test dependencies:**

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

2. **Set up test database:**
   Create a test database in PostgreSQL:

```sql
CREATE DATABASE alpr_service_test;
```

3. **Configure environment variables:**
   Create `.env` file or export:

```bash
TEST_DB_NAME=alpr_service_test
DB_USER=alpr
DB_PASSWORD=P@ssw0rd
DB_HOST=localhost
DB_PORT=5432
```

### Run All Tests

```bash
# Run all tests with coverage report
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run tests in parallel (faster)
pytest -n auto
```

### Run Specific Test Files

```bash
# Run only authentication tests
pytest Test/test_auth.py

# Run only token tests
pytest Test/test_token.py -v

# Run only quota tests
pytest Test/test_quota.py

# Run only subscription tests
pytest Test/test_subscription.py

# Run only user tests
pytest Test/test_user.py
```

### Run Specific Test Classes or Functions

```bash
# Run specific test class
pytest Test/test_token.py::TestTokenCRUD

# Run specific test function
pytest Test/test_auth.py::TestUserLogin::test_login_success

# Run tests matching pattern
pytest -k "test_quota"
```

### Run Tests with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only async tests
pytest -m asyncio
```

## 📊 Coverage Report

After running tests with coverage, open the HTML report:

```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# Open in browser (Windows)
start htmlcov/index.html

# Open in browser (Linux/Mac)
open htmlcov/index.html
```

## 🔍 Test Database

- Tests use a **separate test database** (`alpr_service_test`)
- Database is automatically created/dropped for each test session
- Each test gets a **fresh transaction** that is rolled back after completion
- No test data persists between test runs

## ⚡ Performance

### Expected Test Execution Time

- **All tests**: ~30-60 seconds (depends on database speed)
- **Authentication tests**: ~10-15 seconds
- **Token tests**: ~15-20 seconds
- **Quota tests**: ~10-15 seconds
- **Subscription tests**: ~5-10 seconds
- **User tests**: ~8-12 seconds

### Speed Up Tests

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Skip slow tests
pytest -m "not slow"
```

## 🐛 Debugging Failed Tests

```bash
# Show full output for failed tests
pytest -vv

# Stop at first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Disable warnings
pytest --disable-warnings
```

## 📈 Test Statistics

**Total Test Cases**: 180+

### Breakdown:

- Authentication: 50+ tests
- Token Management: 40+ tests
- Quota System: 30+ tests
- Subscriptions: 30+ tests
- User Management: 30+ tests

### Test Types:

- **Unit Tests**: 60%
- **Integration Tests**: 35%
- **Edge Cases**: 5%

## 🎨 Best Practices

1. **Always use fixtures** for test data
2. **Clean up after tests** (handled automatically)
3. **Use async/await** for database operations
4. **Test both success and failure cases**
5. **Include edge cases** (null, empty, invalid data)
6. **Keep tests isolated** (no dependencies between tests)
7. **Use descriptive test names**
8. **Add docstrings** to explain test purpose

## 🔧 Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: P@ssw0rd
          POSTGRES_DB: alpr_service_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📝 Adding New Tests

When adding new features, create corresponding tests:

1. Add test fixtures to `conftest.py` if needed
2. Create test class in appropriate test file
3. Write test cases for success, failure, and edge cases
4. Run tests to ensure they pass
5. Check coverage to ensure new code is tested

### Example:

```python
@pytest.mark.asyncio
async def test_new_feature(self, client: AsyncClient, test_user: User):
    """Test description"""
    # Arrange
    data = {"field": "value"}

    # Act
    response = await client.post("/api/v1/endpoint", json=data)

    # Assert
    assert response.status_code == 200
    assert response.json()["result"] == "expected"
```

## 🤝 Contributing

When contributing tests:

1. Follow existing test structure
2. Use meaningful test names
3. Add docstrings
4. Cover edge cases
5. Ensure all tests pass before submitting PR

## 📞 Support

If tests fail:

1. Check database connection
2. Verify environment variables
3. Ensure test database exists
4. Check for data conflicts
5. Review error messages carefully

## 🎯 Next Steps

- [ ] Add performance/load tests (JMeter)
- [ ] Add API integration tests (Postman/Newman)
- [ ] Add end-to-end tests
- [ ] Increase coverage to 95%+
- [ ] Add mutation testing
- [ ] Set up CI/CD pipeline
