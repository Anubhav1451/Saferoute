import sys

sys.path.insert(0, '.')

from app.core.config import Settings


def test_validation():
    # Test 1: DEBUG=False, API_KEY_REQUIRED=False should raise ValueError
    try:
        settings = Settings(DEBUG=False, API_KEY_REQUIRED=False)
        print("ERROR: Expected validation error for API_KEY_REQUIRED=False in non-debug")
        return False
    except ValueError as e:
        if "API_KEY_REQUIRED must be set to True" in str(e):
            print("PASS: API_KEY_REQUIRED validation works")
        else:
            print(f"FAIL: Unexpected error: {e}")
            return False

    # Test 2: DEBUG=True, API_KEY_REQUIRED=False should be okay
    try:
        settings = Settings(DEBUG=True, API_KEY_REQUIRED=False)
        print("PASS: DEBUG=True allows API_KEY_REQUIRED=False")
    except Exception as e:
        print(f"FAIL: DEBUG=True should allow API_KEY_REQUIRED=False: {e}")
        return False

    # Test 3: DEBUG=False, RATE_LIMIT_ENABLED=False should raise (with API_KEY_REQUIRED=True to avoid interference)
    try:
        settings = Settings(DEBUG=False, API_KEY_REQUIRED=True, RATE_LIMIT_ENABLED=False)
        print("ERROR: Expected validation error for RATE_LIMIT_ENABLED=False in non-debug")
        return False
    except ValueError as e:
        if "RATE_LIMIT_ENABLED must be set to True" in str(e):
            print("PASS: RATE_LIMIT_ENABLED validation works")
        else:
            print(f"FAIL: Unexpected error: {e}")
            return False

    # Test 4: DEBUG=True, RATE_LIMIT_ENABLED=False should be okay
    try:
        settings = Settings(DEBUG=True, RATE_LIMIT_ENABLED=False)
        print("PASS: DEBUG=True allows RATE_LIMIT_ENABLED=False")
    except Exception as e:
        print(f"FAIL: DEBUG=True should allow RATE_LIMIT_ENABLED=False: {e}")
        return False

    # Test 5: DEBUG=False, DATABASE_URL starting with sqlite should raise (with API_KEY_REQUIRED=True and RATE_LIMIT_ENABLED=True)
    try:
        settings = Settings(DEBUG=False, API_KEY_REQUIRED=True, RATE_LIMIT_ENABLED=True, DATABASE_URL="sqlite:///./test.db")
        print("ERROR: Expected validation error for SQLite in non-debug")
        return False
    except ValueError as e:
        if "SQLite database is not allowed in production" in str(e):
            print("PASS: DATABASE_URL validation works")
        else:
            print(f"FAIL: Unexpected error: {e}")
            return False

    # Test 6: DEBUG=True, DATABASE_url sqlite should be okay
    try:
        settings = Settings(DEBUG=True, DATABASE_URL="sqlite:///./test.db")
        print("PASS: DEBUG=True allows SQLite")
    except Exception as e:
        print(f"FAIL: DEBUG=True should allow SQLite: {e}")
        return False

    # Test 7: Valid production settings
    try:
        settings = Settings(
            DEBUG=False,
            API_KEY_REQUIRED=True,
            API_KEYS=["key1", "key2"],
            RATE_LIMIT_ENABLED=True,
            RATE_LIMIT_REQUESTS_PER_MINUTE=60,
            REQUEST_SIZE_LIMIT_ENABLED=True,
            REQUEST_TIMEOUT_ENABLED=True,
            DATABASE_URL="postgresql://user:pass@localhost/db",
            SECRET_KEY="some-secret-key"
        )
        print("PASS: Valid production settings accepted")
    except Exception as e:
        print(f"FAIL: Valid production settings rejected: {e}")
        return False

    return True

if __name__ == "__main__":
    if test_validation():
        print("\nAll validation tests passed!")
        sys.exit(0)
    else:
        print("\nSome validation tests failed!")
        sys.exit(1)