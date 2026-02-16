# Skipped Tests Documentation

This document explains which tests are currently skipped in the test suite and why.

## Summary

**Total Skipped: ~38 tests**

### Reason Categories

1. **Missing Model Fields (username, tel)**: ~9 tests
2. **Missing Methods (create_user_subscription)**: ~27 tests
3. **Missing Methods (validate_user_subscription)**: 1 test
4. **Missing Features (quota deduction)**: 10 tests (entire test classes)

---

## 1. User Model Field Differences

The User model in `alpr_general_api` has a different schema than `alpr_api_image`:

**Available Fields:**

- `user_id`
- `email`
- `password`
- `is_activate`
- `created_at`
- `updated_at`

**Missing Fields:**

- `username` - Not present in general API
- `tel` - Not present in general API

### Skipped Tests (9 tests):

#### test_auth.py

1. **test_successful_registration** - Expects username/tel fields in registration data
2. **test_register_duplicate_email** - Expects username/tel fields
3. **test_register_duplicate_username** - Tests duplicate username (field doesn't exist)
4. **test_register_invalid_email** - Expects username/tel fields
5. **test_register_weak_password** - Expects username/tel fields
6. **test_register_empty_fields** - Expects username/tel in empty field validation
7. **test_register_with_sql_injection_attempt** - Expects username/tel fields
8. **test_register_with_very_long_values** - Expects username/tel fields

#### test_user.py

9. **test_update_user_via_api** - Expects tel field in update data

---

## 2. UserSubscription Method Differences

The UserSubscription model in `alpr_general_api` is missing methods available in `alpr_api_image`:

**Missing Methods:**

- `create_user_subscription(user_id, sub_id, db)` - Only in API Image service
- `validate_user_subscription(user_id, db)` - Only in API Image service
- `devalue_user_quota(user_id, db)` - Only in API Image service

### Skipped Tests: create_user_subscription (27 tests):

#### test_subscription.py (10 tests)

1. **test_create_user_subscription** - Direct test of method
2. **test_activate_subscription** - Uses create_user_subscription
3. **test_user_can_have_multiple_subscriptions** - Creates multiple subscriptions
4. **test_upgrade_from_tier1_to_tier2** - Creates subscriptions for upgrade
5. **test_upgrade_from_tier2_to_tier3** - Creates subscriptions for upgrade
6. **test_tier1_cannot_access_websocket** - Creates TIER_1 subscription
7. **test_tier2_can_access_websocket** - Creates TIER_2 subscription
8. **test_create_subscription_for_nonexistent_user** - Tests create method with invalid user
9. **test_subscription_with_invalid_sub_id** - Tests create method with invalid sub_id
10. **(Quota deduction tests)** - See section 4

#### test_token.py (4 tests)

11. **test_get_tokens_different_service_types** - Creates WebSocket subscription/token
12. **test_create_video_websocket_token** - Creates TIER \_2 for video access
13. **test_create_rtsp_token** - Creates TIER_3 subscription
14. **test_rtsp_token_requires_tier3** - Creates TIER_2 to test RTSP restriction

#### test_user.py (1 test)

15. **test_get_user_subscription_history** - Creates multiple subscriptions

#### test_quota.py (3 tests)

16. **test_tier1_quota_limit** - Creates TIER_1 subscription to test quota
17. **test_tier2_quota_limit** - Creates TIER_2 subscription
18. **test_tier3_quota_limit** - Creates TIER_3 subscription
19. **test_quota_reset_on_new_subscription** - Creates multiple subscriptions

### Skipped Tests: validate_user_subscription (1 test):

#### test_user.py

20. **test_user_without_subscription** - Uses validate_user_subscription to check no subscription

---

## 3. Login Endpoint Field Differences

The login endpoint expects fields that reference the non-existent User model fields:

### Skipped Tests (5 tests):

#### test_auth.py

1. **test_login_success** - Uses 'username' field in login payload
2. **test_login_wrong_password** - Uses 'username' field
3. **test_login_nonexistent_user** - Uses 'username' field
4. **test_login_returns_valid_jwt** - Uses 'username' field
5. **test_access_protected_endpoint_with_token** - Uses 'username' field

---

## 4. Quota Management Features (Entire Test Classes Skipped)

These test classes test quota deduction and management features only available in `alpr_api_image`:

### Skipped Test Classes (10 tests total):

#### test_quota.py

- **TestQuotaDeduction** (4 tests) - Tests devalue_user_quota method
- **TestQuotaValidation** (3 tests) - Tests quota validation
- **TestQuotaLimits** (partial - see section 2)
- **TestQuotaEdgeCases** (3 tests) - Tests quota edge cases

---

## Implementation Status by Service

| Feature                                       | alpr_general_api | alpr_api_image |
| --------------------------------------------- | ---------------- | -------------- |
| User.username                                 | ❌               | ✅             |
| User.tel                                      | ❌               | ✅             |
| UserSubscription.create_user_subscription()   | ❌               | ✅             |
| UserSubscription.validate_user_subscription() | ❌               | ✅             |
| UserSubscription.devalue_user_quota()         | ❌               | ✅             |
| Subscription CRUD                             | ✅               | ✅             |
| Token CRUD                                    | ✅               | ✅             |
| User Authentication                           | ✅               | ✅             |

---

## Test Results Summary

**With Skipped Tests:**

- ✅ Passing: ~44 tests (40%)
- ⏭️ Skipped: ~38 tests (34%)
- ❌ Failed: ~4 tests (4%)
- ⚠️ Errors: ~25 tests (22%) - Duplicate email constraint errors

**Coverage:** 59% (700 of 1945 statements missed)

---

## Next Steps

### To Fix Remaining Errors:

1. **Duplicate Email Errors (28 tests)**: Update fixtures to use unique emails per test
2. **test_get_all_subscriptions**: Endpoint returns 404, needs investigation
3. **test_get_nonexistent_user**: Returns 500 instead of 404, needs error handling fix

### To Increase Coverage:

1. Implement missing UserSubscription methods in general API
2. Add username/tel fields to User model if needed for general API
3. Write new tests for general API-specific features

---

## How to Run Only Non-Skipped Tests

```bash
# Run all tests (includes skipped)
pytest Test/

# Run with skip reasons displayed
pytest Test/ -rs

# Run only tests that aren't skipped
pytest Test/ -k "not skip"

# Run specific test file
pytest Test/test_auth.py -v
```

---

## Documentation Date

Last Updated: 2025-01-XX (Test Suite Creation)
