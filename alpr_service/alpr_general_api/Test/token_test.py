import pytest
import requests

# Replace with your actual base URL if different
BASE_URL = "http://localhost:8000"


def test_get_tokens():
    response = requests.get(f"{BASE_URL}/api/v1/tokens",
                            params={"user_id": "1", "service_type": "test"})
    assert response.status_code == 200
    # Add assertions based on your expected output
    # e.g., assert response.json() == expected_data


def test_create_token():
    token_data = {
        "user_id": "1",
        "service_type": "test",
        "token_name": "test_token",
        "expire_time": None,  # Or some specific datetime if not None
    }
    response = requests.post(f"{BASE_URL}/api/v1/tokens", json=token_data)
    assert response.status_code == 200
    # Add assertions based on your expected output
    # e.g., assert response.json()["token_name"] == "test_token"
