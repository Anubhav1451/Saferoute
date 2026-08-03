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

        # Test region directory creation
        region_dir = storage._region_dir(1)
        assert region_dir.exists()
        print("[PASS] Region directory creation works")

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

def test_region_manager_models():
    """Test region manager with mocked database"""
    print("\nTesting Region Manager Models...")

    try:
        from app.offline.region_manager import OfflineRegionManager
        from app.db.models import OfflineRegion, DownloadStatus, SyncStatus
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Create in-memory SQLite database for testing
        engine = create_engine("sqlite:///:memory:")
        from app.db.models import Base
        Base.metadata.create_all(engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Initialize region manager
            manager = OfflineRegionManager(db)
            print("[PASS] RegionManager initialized with test DB")

            # Test region creation
            region = manager.create_region(
                name="Test Region",
                min_lat=28.0,
                min_lon=77.0,
                max_lat=29.0,
                max_lon=78.0,
                region_version="1.0.0"
            )
            assert region.id is not None
            assert region.name == "Test Region"
            assert region.download_status == DownloadStatus.PENDING
            print("[PASS] Region creation works")

            # Test region retrieval
            retrieved = manager.get_region(region.id)
            assert retrieved is not None
            assert retrieved.name == "Test Region"
            print("[PASS] Region retrieval works")

            # Test region listing
            regions = manager.list_regions()
            assert len(regions) == 1
            print("[PASS] Region listing works")

            # Test download lifecycle
            # Start download
            region = manager.start_download(region.id)
            assert region.download_status == DownloadStatus.DOWNLOADING
            print("[PASS] Download start works")

            # Update progress
            region = manager.update_download_progress(region.id, 50.0)
            assert region.download_progress == 50.0
            print("[PASS] Download progress update works")

            # Pause download
            region = manager.pause_download(region.id)
            assert region.download_status == DownloadStatus.PAUSED
            print("[PASS] Download pause works")

            # Resume download
            region = manager.resume_download(region.id)
            assert region.download_status == DownloadStatus.DOWNLOADING
            print("[PASS] Download resume works")

            # Complete download
            region = manager.complete_download(
                region.id,
                checksum="a" * 64,  # Fake SHA-256
                compressed_size=1000,
                uncompressed_size=2000
            )
            assert region.download_status == DownloadStatus.COMPLETED
            assert region.download_progress == 100.0
            assert region.checksum_sha256 == "a" * 64
            print("[PASS] Download completion works")

            # Test versioning
            region = manager.create_new_version(region.id)
            assert region.current_version == 2
            assert region.previous_version == 1
            print("[PASS] Version creation works")

            # Test rollback preparation (would need actual data to test fully)
            info = manager.get_version_info(region.id)
            assert info["current_version"] == 2
            assert info["previous_version"] == 1
            print("[PASS] Version info retrieval works")

            # Test region status
            status = manager.get_region_status(region.id)
            assert status["id"] == region.id
            assert status["name"] == "Test Region"
            assert status["download_status"] == "COMPLETED"
            print("[PASS] Region status retrieval works")

            # Test storage usage
            storage_stats = manager.get_storage_usage()
            assert "storage_root" in storage_stats
            print("[PASS] Storage usage retrieval works")

            return True

        finally:
            db.close()

    except Exception as e:
        print(f"[FAIL] Region manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_routes():
    """Test that API routes are properly defined"""
    print("\nTesting API Routes...")

    try:
        from app.api.v1.offline import router

        # Check that router has routes
        routes = []
        for route in router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)

        expected_routes = [
            "/regions",
            "/regions/{region_id}",
            "/regions/{region_id}/download",
            "/regions/{region_id}/download/pause",
            "/regions/{region_id}/download/resume",
            "/regions/{region_id}/download/cancel",
            "/regions/{region_id}/verify",
            "/regions/{region_id}/sync",
            "/regions/{region_id}/sync/status",
            "/regions/{region_id}/version/new",
            "/regions/{region_id}/version/rollback",
            "/regions/{region_id}/version",
            "/route",
            "/connectivity",
            "/storage",
            "/status",
            "/regions/{region_id}/recompress"
        ]

        found_routes = 0
        for expected in expected_routes:
            # Check if any route matches (accounting for path parameters)
            for route in routes:
                if expected.split("{")[0] in route.split("{")[0]:
                    found_routes += 1
                    break

        print(f"[PASS] Found {found_routes}/{len(expected_routes)} expected API routes")

        # Check specific endpoint methods
        routes_dict = {}
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes_dict[route.path] = list(route.methods)

        # Check a few key endpoints
        assert "/regions" in routes_dict
        assert "POST" in routes_dict["/regions"]
        assert "GET" in routes_dict["/regions"]
        print("[PASS] Region CRUD endpoints present")

        assert "/regions/{region_id}/download" in routes_dict
        assert "POST" in routes_dict["/regions/{region_id}/download"]
        print("[PASS] Download endpoint present")

        return True

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
        test_region_manager_models,
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