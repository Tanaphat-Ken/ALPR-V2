# Test Quick Reference

## Quick Commands

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest Test/test_auth.py          # Authentication tests
pytest Test/test_token.py         # Token tests
pytest Test/test_quota.py         # Quota tests
pytest Test/test_subscription.py  # Subscription tests
pytest Test/test_user.py          # User tests
```

### Run Specific Test Class

```bash
pytest Test/test_token.py::TestTokenCRUD
pytest Test/test_auth.py::TestUserLogin
pytest Test/test_quota.py::TestQuotaDeduction
```

### Run Specific Test Function

```bash
pytest Test/test_auth.py::TestUserLogin::test_login_success
pytest Test/test_token.py::TestTokenCRUD::test_create_api_token
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
pytest --cov=Models --cov-report=term-missing
```

### Run in Parallel (Fast)

```bash
pytest -n auto          # Use all CPU cores
pytest -n 4             # Use 4 workers
```

### Debugging

```bash
pytest -v               # Verbose output
pytest -vv              # Extra verbose
pytest -x               # Stop at first failure
pytest --pdb            # Drop to debugger on failure
pytest -l               # Show local variables
pytest -s               # Show print statements
```

### Filter Tests

```bash
pytest -k "test_login"              # Run tests matching pattern
pytest -k "not slow"                # Skip slow tests
pytest -m "asyncio"                 # Run async tests only
pytest Test/test_auth.py -v -k "login"  # Login tests only
```

## Test Markers

```python
@pytest.mark.asyncio     # Async test
@pytest.mark.unit        # Unit test
@pytest.mark.integration # Integration test
@pytest.mark.slow        # Slow running test
```

## Coverage Commands

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Terminal coverage report
pytest --cov=. --cov-report=term

# Missing lines report
pytest --cov=. --cov-report=term-missing

# Branch coverage
pytest --cov=. --cov-branch

# Specific module coverage
pytest --cov=Models --cov=Controllers
```

## Test Database Setup

### Create Test Database

```sql
CREATE DATABASE alpr_service_test;
GRANT ALL PRIVILEGES ON DATABASE alpr_service_test TO alpr;
```

### Environment Variables

```bash
export TEST_DB_NAME=alpr_service_test
export DB_USER=alpr
export DB_PASSWORD=P@ssw0rd
export DB_HOST=localhost
export DB_PORT=5432
```

## Common Test Patterns

### Testing API Endpoints

```python
@pytest.mark.asyncio
async def test_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/endpoint", json=data)
    assert response.status_code == 200
```

### Testing Database Operations

```python
@pytest.mark.asyncio
async def test_db_operation(db_session: AsyncSession):
    result = await Model.create(data, db_session)
    assert result is not None
```

### Testing Authentication

```python
@pytest.mark.asyncio
async def test_with_auth(client: AsyncClient, test_user: User):
    login_response = await client.post("/api/v1/auth/login", json=credentials)
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/protected", headers=headers)
```

## Expected Test Results

### Test Count by File

- `test_auth.py`: 50+ tests
- `test_token.py`: 40+ tests
- `test_quota.py`: 30+ tests
- `test_subscription.py`: 30+ tests
- `test_user.py`: 30+ tests

**Total**: 180+ test cases

### Coverage Goals

- Models: 90%+
- Controllers: 85%+
- Overall: 80%+

## Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
sudo service postgresql status

# Create test database
psql -U alpr -c "CREATE DATABASE alpr_service_test;"
```

### Import Errors

```bash
# Install all dependencies
pip install -r requirements.txt
```

### Async Test Errors

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check pytest.ini has asyncio_mode = auto
```

### Permission Errors

```bash
# Grant permissions on test database
psql -U postgres
GRANT ALL PRIVILEGES ON DATABASE alpr_service_test TO alpr;
```

## CI/CD Integration

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
pytest -x -q
```

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v2
```

## Performance Benchmarks

### Expected Execution Times

- Full test suite: ~60 seconds
- Auth tests: ~15 seconds
- Token tests: ~20 seconds
- Quota tests: ~15 seconds
- Subscription tests: ~10 seconds
- User tests: ~12 seconds

### Speed Optimization

```bash
# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"

# Only failed tests
pytest --lf
```
