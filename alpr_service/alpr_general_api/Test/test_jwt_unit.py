#!/usr/bin/env python3
"""
4.5.1 Unit Test (3) — Authentication / JWT Logic
Tests create_access_token() and decode_access_token() in Libs/auth.py
without any database or network dependencies.

Run:
    cd alpr_service/alpr_general_api
    pip install pytest python-jose[cryptography] passlib[bcrypt]
    pytest Test/test_jwt_unit.py -v
"""

import sys
import os
import pytest
from datetime import timedelta
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Libs.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
    SECRET_KEY,
    ALGORITHM,
)


# ---------------------------------------------------------------------------
# Tests — JWT Encode / Decode Round-Trip
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    """Tests for JWT token creation."""

    def test_returns_non_empty_string(self):
        token = create_access_token({"user_id": 1, "email": "test@example.com"})
        assert isinstance(token, str) and len(token) > 0

    def test_token_has_three_jwt_segments(self):
        """A valid JWT has exactly 3 base64url segments separated by '.'."""
        token = create_access_token({"user_id": 1, "email": "test@example.com"})
        parts = token.split(".")
        assert len(parts) == 3, f"Expected 3 JWT segments, got {len(parts)}"

    def test_custom_expiry_delta_accepted(self):
        """create_access_token must accept an explicit expires_delta without error."""
        token = create_access_token(
            {"user_id": 42, "email": "a@b.com"},
            expires_delta=timedelta(minutes=30)
        )
        assert isinstance(token, str)


class TestDecodeAccessToken:
    """Tests for JWT token decoding and payload integrity."""

    def test_decode_recovers_user_id(self):
        """Payload user_id must survive encode/decode cycle intact."""
        payload = {"user_id": 7, "email": "user@example.com"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        assert decoded["user_id"] == 7

    def test_decode_recovers_email(self):
        """Payload email must survive encode/decode cycle intact."""
        payload = {"user_id": 7, "email": "user@example.com"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        assert decoded["email"] == "user@example.com"

    def test_decoded_payload_contains_exp_field(self):
        """JWT must include standard 'exp' (expiration) claim after encoding."""
        token = create_access_token({"user_id": 1, "email": "x@x.com"})
        decoded = decode_access_token(token)
        assert "exp" in decoded, "Decoded JWT must have 'exp' claim"

    def test_tampering_with_payload_raises_401(self):
        """Modifying any character in the payload section must invalidate signature."""
        token = create_access_token({"user_id": 1, "email": "x@x.com"})
        header, payload, signature = token.split(".")
        # Flip last character of payload
        tampered_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
        tampered_token = f"{header}.{tampered_payload}.{signature}"

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(tampered_token)
        assert exc_info.value.status_code == 401

    def test_wrong_secret_raises_401(self):
        """Token signed with a different secret must be rejected."""
        from jose import jwt as jose_jwt
        from datetime import datetime

        fake_token = jose_jwt.encode(
            {"user_id": 1, "email": "x@x.com", "exp": datetime.utcnow() + timedelta(hours=1)},
            key="wrong-secret",
            algorithm=ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(fake_token)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        """Token with exp in the past must be rejected with HTTP 401."""
        token = create_access_token(
            {"user_id": 1, "email": "x@x.com"},
            expires_delta=timedelta(seconds=-1)   # already expired
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        assert exc_info.value.status_code == 401, \
            f"Expected 401 for expired token, got {exc_info.value.status_code}"

    def test_completely_invalid_string_raises_401(self):
        """Garbage string must raise HTTP 401."""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("this.is.not.a.jwt")
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Tests — Password Hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    """Verify bcrypt hashing is consistent with verification."""

    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("Secret@123")
        assert hashed != "Secret@123"

    def test_verify_correct_password(self):
        pw = "Correct@Password1"
        assert verify_password(pw, get_password_hash(pw)) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("Correct@Password1")
        assert verify_password("WrongPassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses random salt — same password → different hash each time."""
        pw = "SamePassword@1"
        h1 = get_password_hash(pw)
        h2 = get_password_hash(pw)
        assert h1 != h2, "Hashes of the same password should differ (different salts)"
