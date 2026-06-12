import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.cache import redis_client, cache_get, cache_set, cache_delete, UpstashRESTClient
import time

def test_redis_connection():
    print("==================================================")
    print("  RUNNING UPSTASH REDIS REST FALLBACK INTEGRATION  ")
    print("==================================================")
    
    print("Checking active redis_client type...")
    if redis_client is None:
        print("redis_client is None. Falling back to InMemoryCache.")
        print("FAIL: Redis caching is not active. Make sure REDIS_URL in backend/.env is correct and reachable via REST.")
        sys.exit(1)
    
    print(f"Active redis_client type: {type(redis_client)}")
    
    # Assert it is using UpstashRESTClient if TCP failed
    if isinstance(redis_client, UpstashRESTClient):
        print("Successfully verified: redis_client is using UpstashRESTClient (HTTPS REST fallback)!")
    else:
        print("redis_client is using standard TCP Redis client (TCP succeeded).")

    # Perform SET test
    test_key = "integration_test_key"
    test_val = "rest_fallback_success_123"
    
    print(f"Setting key '{test_key}' to '{test_val}'...")
    cache_set(test_key, test_val, ttl=10)
    
    # Perform GET test
    print(f"Getting key '{test_key}'...")
    retrieved_val = cache_get(test_key)
    print(f"Retrieved value: '{retrieved_val}'")
    assert retrieved_val == test_val, f"Value mismatch! Expected '{test_val}', got '{retrieved_val}'"
    print("  [PASS] Key write & read verification successful.")
    
    # Test delete
    print(f"Deleting key '{test_key}'...")
    cache_delete(test_key)
    deleted_val = cache_get(test_key)
    print(f"Value after delete: '{deleted_val}'")
    assert deleted_val is None, "Key was not deleted!"
    print("  [PASS] Key delete verification successful.")
    
    print("==================================================")
    print("         ALL INTEGRATION TESTS PASSED!           ")
    print("==================================================")

if __name__ == "__main__":
    test_redis_connection()
