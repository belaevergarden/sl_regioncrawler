"""
Unit tests for database persistence.

Author: Isabela Evergarden
"""

import pytest
import os
import tempfile
from sl_regioncrawler.models import Region, AccessLevel, RegionFlags
from sl_regioncrawler.persistence import RegionDatabase


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    yield path
    
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_regions():
    """Create sample regions for testing."""
    return [
        Region(
            x=1000, y=1000,
            name="Test Region 1",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED,
            agents=5
        ),
        Region(
            x=1001, y=1000,
            name="Test Region 2",
            access=AccessLevel.MODERATE,
            region_flags=RegionFlags.SANDBOX,
            agents=10
        ),
        Region(
            x=1002, y=1000,
            name="Test Region 3",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED | RegionFlags.SANDBOX,
            agents=0
        ),
    ]


class TestRegionDatabase:
    """Test RegionDatabase class."""
    
    def test_database_creation(self, temp_db):
        """Test database file is created."""
        db = RegionDatabase(temp_db)
        db.close()
        
        assert os.path.exists(temp_db)
    
    def test_save_region(self, temp_db, sample_regions):
        """Test saving a single region."""
        db = RegionDatabase(temp_db)
        
        region_id = db.save_region(sample_regions[0])
        
        assert region_id > 0
        db.close()
    
    def test_save_multiple_regions(self, temp_db, sample_regions):
        """Test saving multiple regions."""
        db = RegionDatabase(temp_db)
        
        count = db.save_regions(sample_regions)
        
        assert count == len(sample_regions)
        db.close()
    
    def test_get_region(self, temp_db, sample_regions):
        """Test retrieving a region by coordinates."""
        db = RegionDatabase(temp_db)
        db.save_region(sample_regions[0])
        
        retrieved = db.get_region(1000, 1000)
        
        assert retrieved is not None
        assert retrieved.name == "Test Region 1"
        assert retrieved.x == 1000
        assert retrieved.y == 1000
        db.close()
    
    def test_get_nonexistent_region(self, temp_db):
        """Test retrieving non-existent region returns None."""
        db = RegionDatabase(temp_db)
        
        retrieved = db.get_region(9999, 9999)
        
        assert retrieved is None
        db.close()
    
    def test_get_all_regions(self, temp_db, sample_regions):
        """Test retrieving all regions."""
        db = RegionDatabase(temp_db)
        db.save_regions(sample_regions)
        
        all_regions = db.get_all_regions()
        
        assert len(all_regions) == len(sample_regions)
        db.close()
    
    def test_update_existing_region(self, temp_db, sample_regions):
        """Test updating an existing region."""
        db = RegionDatabase(temp_db)
        
        # Save initial region
        db.save_region(sample_regions[0])
        
        # Update with new data
        updated_region = Region(
            x=1000, y=1000,
            name="Updated Region",
            access=AccessLevel.MODERATE,
            region_flags=RegionFlags.SANDBOX,
            agents=20
        )
        db.save_region(updated_region)
        
        # Retrieve and verify
        retrieved = db.get_region(1000, 1000)
        assert retrieved.name == "Updated Region"
        assert retrieved.agents == 20
        db.close()
    
    def test_search_regions_by_name(self, temp_db, sample_regions):
        """Test searching regions by name pattern."""
        db = RegionDatabase(temp_db)
        db.save_regions(sample_regions)
        
        results = db.search_regions(name_pattern="%Region 1%")
        
        assert len(results) == 1
        assert results[0].name == "Test Region 1"
        db.close()
    
    def test_search_regions_by_coordinates(self, temp_db, sample_regions):
        """Test searching regions by coordinate range."""
        db = RegionDatabase(temp_db)
        db.save_regions(sample_regions)
        
        results = db.search_regions(min_x=1001, max_x=1002)
        
        assert len(results) == 2
        assert all(1001 <= r.x <= 1002 for r in results)
        db.close()
    
    def test_search_regions_by_access_level(self, temp_db, sample_regions):
        """Test searching regions by access level."""
        db = RegionDatabase(temp_db)
        db.save_regions(sample_regions)
        
        results = db.search_regions(access_levels=[AccessLevel.GENERAL])
        
        assert len(results) == 2
        assert all(r.access == AccessLevel.GENERAL for r in results)
        db.close()
    
    def test_get_statistics(self, temp_db, sample_regions):
        """Test getting database statistics."""
        db = RegionDatabase(temp_db)
        db.save_regions(sample_regions)
        
        stats = db.get_statistics()
        
        assert stats['total_regions'] == 3
        assert stats['public_regions'] == 2  # Regions with PUBLIC_ALLOWED flag
        assert stats['sandbox_regions'] == 2  # Regions with SANDBOX flag
        db.close()
    
    def test_save_crawl_history(self, temp_db):
        """Test saving crawl history."""
        db = RegionDatabase(temp_db)
        
        stats = {
            'start_time': '2026-09-18T15:00:00',
            'end_time': '2026-09-18T15:05:00',
            'total_requests': 100,
            'successful_requests': 95,
            'failed_requests': 5,
            'regions_discovered': 250,
            'regions_matching': 80,
            'duration_seconds': 300.0,
            'search_criteria': {'public_only': True}
        }
        
        history_id = db.save_crawl_history(stats)
        
        assert history_id > 0
        db.close()
    
    def test_context_manager(self, temp_db, sample_regions):
        """Test database context manager."""
        with RegionDatabase(temp_db) as db:
            db.save_region(sample_regions[0])
        
        # Verify database was properly closed and data saved
        with RegionDatabase(temp_db) as db:
            retrieved = db.get_region(1000, 1000)
            assert retrieved is not None
