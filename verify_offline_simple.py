#!/usr/bin/env python3
"""
Offline Navigation Engine Verification Script
Tests core functionality of the RC8.5 Offline Navigation Engine
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, 'backend')

def test_imports():
    """Test that all offline modules can be imported"""
    print("Testing imports...")

    try:
        from app.offline.region_manager import OfflineRegionManager
        print("[PASS] RegionManager imported")
    except Exception as e:
        print(f"[FAIL] RegionManager import failed: {e}")
        return False

    try:
        from app.offline.storage import OfflineStorageHandler
        print("[PASS] StorageHandler imported")
    except Exception as e:
        print(f"[FAIL] StorageHandler import failed: {e}")
        return False

    try:
        from app.offline.sync_engine import OfflineSyncEngine
        print("[PASS] SyncEngine imported")
    except Exception as e:
        print(f"[FAIL] SyncEngine import failed: {e}")
        return False

    try:
        from app.offline.routing import OfflineRoutingService
        print("[PASS] OfflineRoutingService imported")
    except Exception as e:
        print(f"[FAIL] OfflineRoutingService import failed: {e}")
        return False

    try:
        from app.api.v1.offline import router
        print("[PASS] Offline API router imported")
    except Exception as e:
        print(f"[FAIL] Offline API router import failed: {e}")
        return False

    try:
        from app.tasks.offline_tasks import download_region, sync_region, verify_region_integrity
        print("[PASS] Offline Celery tasks imported")
    except Exception as e:
        print(f"[FAIL] Offline Celery tasks import failed: {e}")
        return False

    try:
        from app.schemas.realtime import EventType
        print("[PASS] Realtime event schemas imported")
        # Check that offline events exist
        assert hasattr(EventType, 'OFFLINE_DOWNLOAD_STARTED')
        assert hasattr(EventType, 'OFFLINE_SYNC_COMPLETED')
        assert hasattr(EventType, 'OFFLINE_VERIFICATION_COMPLETED')
        print("[PASS] Offline event types present")
    except Exception as e:
        print(f"[FAIL] Realtime event schemas import failed: {e}")
        return False

    try:
        from app.utils.cache import get_cache
        print("[PASS] Cache utility imported")
    except Exception as e:
        print(f"[FAIL] Cache utility import failed: {e}")
        return False

    return True

def test_storage_handler():
    """Test storage handler basic functionality"""
    print("\nTesting Storage Handler...")

    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    try:
        from app.offline.storage import OfflineStorageHandler

        # Initialize storage handler
        storage = OfflineStorageHandler(storage_root=temp_dir)
        print("[PASS] StorageHandler initialized")

        # Test data file path generation
        data_file = storage._data_file(1, "graph", 1)
        expected_name = "graph_v1.json.gz" if storage.compression_enabled else "graph_v1.json"
        assert data_file.name == expected_name
        print("[PASS] Data file path generation works")

        # Test checksum file path
        checksum_file = storage._checksum_file(1)
        assert checksum_file.name == "checksums.sha256"
        print("[PASS] Checksum file path generation works")

        # Test data saving and loading
        test_data = {"nodes": [{"id": 1, "lat": 0.0, "lon": 0.0}], "edges": []}
        result = storage.save_region_data(1, "graph", test_data, version=1)
        assert result["duplicate"] == False
        assert "path" in result
        print("[PASS] Data saving works")

        # Verify region directory was created
        region_dir = storage._region_dir(1)
        assert region_dir.exists()
        print("[PASS] Region directory created on save")

        # Test data loading
        loaded_data = storage.load_region_data(1, "graph", version=1)
        assert loaded_data is not None
        assert len(loaded_data.get("nodes", [])) == 1
        print("[PASS] Data loading works")

        # Test duplicate detection
        result2 = storage.save_region_data(1, "graph", test_data, version=1)
        assert result2["duplicate"] == True
        print("[PASS] Duplicate detection works")

        # Test checksum computation
        checksum = storage.compute_checksum(1)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 length
        print("[PASS] Checksum computation works")

        # Test checksum saving and verification
        checksums = storage.save_checksums(1)
        assert isinstance(checksums, dict)
        verification = storage.verify_checksums(1)
        assert "verified" in verification
        print("[PASS] Checksum save/verify works")

        # Test region size calculation
        size = storage.get_region_size(1)
        assert isinstance(size, int)
        assert size >= 0
        print("[PASS] Region size calculation works")

        # Test storage stats
        stats = storage.get_storage_stats()
        assert "total_bytes" in stats
        assert "region_count" in stats
        print("[PASS] Storage stats work")

        return True

    except Exception as e:
        print(f"[FAIL] Storage handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_api_routes():
    """Test that API routes are properly defined"""
    print("\nTesting API Routes...")

    try:
        from app.api.v1.offline import router

        # Collect all methods for each path
        routes_dict = {}
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                path = route.path
                methods = list(route.methods)
                if path not in routes_dict:
                    routes_dict[path] = []
                routes_dict[path].extend(methods)
                # Remove duplicates while preserving order
                seen = set()
                unique_methods = []
                for method in routes_dict[path]:
                    if method not in seen:
                        seen.add(method)
                        unique_methods.append(method)
                routes_dict[path] = unique_methods

        expected_routes = {
            "/offline/regions": ["POST", "GET"],
            "/offline/regions/{region_id}": ["GET", "DELETE"],
            "/offline/regions/{region_id}/download": ["POST"],
            "/offline/regions/{region_id}/download/pause": ["POST"],
            "/offline/regions/{region_id}/download/resume": ["POST"],
            "/offline/regions/{region_id}/download/cancel": ["POST"],
            "/offline/regions/{region_id}/verify": ["POST"],
            "/offline/regions/{region_id}/sync": ["POST"],
            "/offline/regions/{region_id}/sync/status": ["GET"],
            "/offline/regions/{region_id}/version/new": ["POST"],
            "/offline/regions/{region_id}/version/rollback": ["POST"],
            "/offline/regions/{region_id}/version": ["GET"],
            "/offline/route": ["POST"],
            "/offline/connectivity": ["GET"],
            "/offline/storage": ["GET"],
            "/offline/status": ["GET"],
            "/offline/regions/{region_id}/recompress": ["POST"]
        }

        passed = 0
        total = len(expected_routes)

        for route_path, expected_methods in expected_routes.items():
            if route_path in routes_dict:
                actual_methods = routes_dict[route_path]
                # Check that all expected methods are present (order doesn't matter)
                if all(method in actual_methods for method in expected_methods):
                    passed += 1
                else:
                    print(f"  [FAIL] {route_path}: Expected {expected_methods}, got {actual_methods}")
            else:
                print(f"  [FAIL] {route_path}: Route not found")

        print(f"[PASS] Found {passed}/{total} expected API routes with correct methods")
        return passed == total

    except Exception as e:
        print(f"[FAIL] API routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("OFFLINE NAVIGATION ENGINE VERIFICATION (RC8.5)")
    print("=" * 60)

    tests = [
        test_imports,
        test_storage_handler,
        test_api_routes
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"RESULTS: {passed}/{total} test groups passed")
    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED - Offline Navigation Engine is ready!")
        return 0
    else:
        print("[FAILURE] SOME TESTS FAILED - Please review implementation")
        return 1

if __name__ == "__main__":
    sys.exit(main())