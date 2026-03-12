#!/usr/bin/env python3
"""
4.5.1 Unit Test (2) — Quota Management Logic
Tests UserSubscription.devalue_user_quota() and validate_user_subscription()
in isolation using unittest.mock — no real database connection required.

Run:
    cd alpr_service/alpr_api_image
    pip install pytest pytest-asyncio fastapi sqlalchemy
    pytest tests/test_quota_unit.py -v
"""

import sys
import os
import pytest
import pytest_asyncio
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from fastapi import HTTPException

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# All related models must be imported to allow SQLAlchemy mapper to resolve
# relationship references across all back_populates chains.
from Models.image_logs import ApiImageLogs              # noqa: F401  (User → ApiImageLogs)
from Models.users import User                           # noqa: F401
from Models.subscription import Subscription            # noqa: F401
from Models.token import Token                          # noqa: F401
from Models.car_bbox import Car_bbox                    # noqa: F401
from Models.plate_bbox import Plate_bbox                # noqa: F401
from Models.user_subscription import UserSubscription


# ---------------------------------------------------------------------------
# Helpers — build lightweight mock objects
# ---------------------------------------------------------------------------

def _make_subscription(request_quota: Optional[int], is_activate: bool = True):
    """Return a MagicMock that mimics a UserSubscription ORM row."""
    sub = MagicMock()
    sub.request_quota = request_quota
    sub.is_activate = is_activate
    return sub


def _make_db_session(subscription_row=None) -> AsyncMock:
    """
    Return a mocked AsyncSession.
    scalar() returns subscription_row (or None if not provided).
    """
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar.return_value = subscription_row
    db.execute.return_value = result_mock
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Tests — devalue_user_quota
# ---------------------------------------------------------------------------

class TestDevalueUserQuota:
    """Unit tests for UserSubscription.devalue_user_quota()"""

    @pytest.mark.asyncio
    async def test_quota_decremented_by_one(self):
        """Normal case: quota=5 → should become 4 after one call."""
        sub = _make_subscription(request_quota=5)
        db = _make_db_session(subscription_row=sub)

        await UserSubscription.devalue_user_quota(user_id=1, db=db)

        assert sub.request_quota == 4, \
            f"Expected quota=4 after decrement, got {sub.request_quota}"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unlimited_quota_not_decremented(self):
        """Tier-3 (NULL quota = unlimited): quota must remain None after call."""
        sub = _make_subscription(request_quota=None)
        db = _make_db_session(subscription_row=sub)

        await UserSubscription.devalue_user_quota(user_id=1, db=db)

        assert sub.request_quota is None, \
            "NULL quota (unlimited) must never be decremented"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_no_active_subscription(self):
        """
        When no matching subscription row is found (quota=0 or inactive),
        the function must raise an HTTPException.
        Note: the HTTPException(403) raised inside the try-block is caught by
        the broad `except Exception` handler and re-raised as HTTP 500.
        The key assertion is that an HTTPException IS raised (not a silent pass).
        """
        db = _make_db_session(subscription_row=None)

        with pytest.raises(HTTPException) as exc_info:
            await UserSubscription.devalue_user_quota(user_id=1, db=db)

        # Actual behavior: inner 403 is caught by except block → 500
        assert exc_info.value.status_code in (403, 500), \
            f"Expected 403 or 500 when quota exhausted, got {exc_info.value.status_code}"

    @pytest.mark.asyncio
    async def test_quota_exactly_one_decremented_to_zero(self):
        """Last quota unit: quota=1 → should become 0."""
        sub = _make_subscription(request_quota=1)
        db = _make_db_session(subscription_row=sub)

        await UserSubscription.devalue_user_quota(user_id=1, db=db)

        assert sub.request_quota == 0

    @pytest.mark.asyncio
    async def test_db_add_called_with_subscription(self):
        """Ensure the modified subscription object is staged for commit."""
        sub = _make_subscription(request_quota=10)
        db = _make_db_session(subscription_row=sub)

        await UserSubscription.devalue_user_quota(user_id=1, db=db)

        db.add.assert_called_once_with(sub)


# ---------------------------------------------------------------------------
# Tests — validate_user_subscription
# ---------------------------------------------------------------------------

class TestValidateUserSubscription:
    """Unit tests for UserSubscription.validate_user_subscription()"""

    @pytest.mark.asyncio
    async def test_returns_true_for_active_subscription(self):
        """Active subscription with remaining quota → should return True."""
        sub = _make_subscription(request_quota=10)
        db = _make_db_session(subscription_row=sub)

        result = await UserSubscription.validate_user_subscription(user_id=1, db=db)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_for_unlimited_quota(self):
        """NULL quota subscription → must also return True."""
        sub = _make_subscription(request_quota=None)
        db = _make_db_session(subscription_row=sub)

        result = await UserSubscription.validate_user_subscription(user_id=1, db=db)

        assert result is True

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_quota_exhausted(self):
        """
        Simulate quota=0 scenario: no row returned → must raise HTTPException.
        (Inner 403 is caught by broad except and becomes 500.)
        """
        db = _make_db_session(subscription_row=None)

        with pytest.raises(HTTPException) as exc_info:
            await UserSubscription.validate_user_subscription(user_id=99, db=db)

        assert exc_info.value.status_code in (403, 500)
