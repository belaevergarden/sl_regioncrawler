"""
Unit tests for region filtering.

Author: Isabela Evergarden
"""

import pytest
from sl_regioncrawler.models import Region, AccessLevel, RegionFlags, SearchCriteria
from sl_regioncrawler.filtering import (
    RegionFilter, deduplicate_regions, filter_by_predicate,
    get_public_sandboxes, get_script_enabled_regions, get_active_regions
)


class TestRegionFilter:
    """Test RegionFilter class."""
    
    def test_filter_public_regions(self):
        """Test filtering for public regions."""
        criteria = SearchCriteria(public_only=True)
        filter_obj = RegionFilter(criteria)
        
        regions = [
            Region(x=1000, y=1000, name="Public1", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
            Region(x=1001, y=1000, name="Private1", access=AccessLevel.GENERAL,
                  region_flags=0),
            Region(x=1002, y=1000, name="Public2", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
        ]
        
        filtered = filter_obj.filter_regions(regions)
        
        assert len(filtered) == 2
        assert all(r.is_public() for r in filtered)
    
    def test_filter_by_maturity(self):
        """Test filtering by maturity rating."""
        criteria = SearchCriteria(
            include_general=True,
            include_moderate=False,
            include_adult=False
        )
        filter_obj = RegionFilter(criteria)
        
        regions = [
            Region(x=1000, y=1000, name="General", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
            Region(x=1001, y=1000, name="Moderate", access=AccessLevel.MODERATE,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
            Region(x=1002, y=1000, name="Adult", access=AccessLevel.ADULT,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
        ]
        
        filtered = filter_obj.filter_regions(regions)
        
        assert len(filtered) == 1
        assert filtered[0].access == AccessLevel.GENERAL
    
    def test_ranking_public_higher(self):
        """Test that public regions rank higher."""
        criteria = SearchCriteria()
        filter_obj = RegionFilter(criteria)
        
        regions = [
            Region(x=1000, y=1000, name="Private", access=AccessLevel.GENERAL,
                  region_flags=0),
            Region(x=1001, y=1000, name="Public", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
        ]
        
        ranked = filter_obj.rank_regions(regions)
        
        # Public region should be first
        assert ranked[0].name == "Public"
    
    def test_ranking_sandbox_higher(self):
        """Test that sandbox regions rank higher."""
        criteria = SearchCriteria()
        filter_obj = RegionFilter(criteria)
        
        regions = [
            Region(x=1000, y=1000, name="Regular", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
            Region(x=1001, y=1000, name="Sandbox", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED | RegionFlags.SANDBOX),
        ]
        
        ranked = filter_obj.rank_regions(regions)
        
        # Sandbox should be first
        assert ranked[0].name == "Sandbox"
    
    def test_ranking_with_agents(self):
        """Test ranking considers agent count."""
        criteria = SearchCriteria()
        filter_obj = RegionFilter(criteria)
        
        regions = [
            Region(x=1000, y=1000, name="Empty", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED, agents=0),
            Region(x=1001, y=1000, name="Active", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED, agents=10),
        ]
        
        ranked = filter_obj.rank_regions(regions)
        
        # Active region should be first
        assert ranked[0].name == "Active"
    
    def test_get_top_regions(self):
        """Test getting top N regions."""
        criteria = SearchCriteria()
        filter_obj = RegionFilter(criteria)
        
        regions = [
            Region(x=i, y=1000, name=f"Region{i}", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED)
            for i in range(150)
        ]
        
        top_100 = filter_obj.get_top_regions(regions, limit=100)
        
        assert len(top_100) == 100


class TestDeduplication:
    """Test region deduplication."""
    
    def test_deduplicate_removes_duplicates(self):
        """Test that duplicates are removed."""
        regions = [
            Region(x=1000, y=1000, name="Region1", access=AccessLevel.GENERAL,
                  region_flags=0),
            Region(x=1000, y=1000, name="Region1 Duplicate", access=AccessLevel.GENERAL,
                  region_flags=0),
            Region(x=1001, y=1000, name="Region2", access=AccessLevel.GENERAL,
                  region_flags=0),
        ]
        
        unique = deduplicate_regions(regions)
        
        assert len(unique) == 2
    
    def test_deduplicate_preserves_first(self):
        """Test that first occurrence is preserved."""
        regions = [
            Region(x=1000, y=1000, name="First", access=AccessLevel.GENERAL,
                  region_flags=0),
            Region(x=1000, y=1000, name="Second", access=AccessLevel.GENERAL,
                  region_flags=0),
        ]
        
        unique = deduplicate_regions(regions)
        
        assert len(unique) == 1
        assert unique[0].name == "First"


class TestPredicateFiltering:
    """Test predicate-based filtering."""
    
    def test_filter_by_predicate(self):
        """Test custom predicate filtering."""
        regions = [
            Region(x=1000, y=1000, name="Region1", access=AccessLevel.GENERAL,
                  region_flags=0, agents=5),
            Region(x=1001, y=1000, name="Region2", access=AccessLevel.GENERAL,
                  region_flags=0, agents=0),
            Region(x=1002, y=1000, name="Region3", access=AccessLevel.GENERAL,
                  region_flags=0, agents=10),
        ]
        
        # Filter for regions with more than 3 agents
        filtered = filter_by_predicate(regions, lambda r: r.agents > 3)
        
        assert len(filtered) == 2
        assert all(r.agents > 3 for r in filtered)


class TestHelperFunctions:
    """Test helper filtering functions."""
    
    def test_get_public_sandboxes(self):
        """Test getting public sandbox regions."""
        regions = [
            Region(x=1000, y=1000, name="Public Sandbox", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED | RegionFlags.SANDBOX),
            Region(x=1001, y=1000, name="Private Sandbox", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.SANDBOX),
            Region(x=1002, y=1000, name="Public Regular", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.PUBLIC_ALLOWED),
        ]
        
        sandboxes = get_public_sandboxes(regions)
        
        assert len(sandboxes) == 1
        assert sandboxes[0].name == "Public Sandbox"
    
    def test_get_script_enabled_regions(self):
        """Test getting script-enabled regions."""
        regions = [
            Region(x=1000, y=1000, name="Scripts OK", access=AccessLevel.GENERAL,
                  region_flags=0),
            Region(x=1001, y=1000, name="No Scripts", access=AccessLevel.GENERAL,
                  region_flags=RegionFlags.SKIP_SCRIPTS),
        ]
        
        script_enabled = get_script_enabled_regions(regions)
        
        assert len(script_enabled) == 1
        assert script_enabled[0].name == "Scripts OK"
    
    def test_get_active_regions(self):
        """Test getting active regions."""
        regions = [
            Region(x=1000, y=1000, name="Active1", access=AccessLevel.GENERAL,
                  region_flags=0, agents=5),
            Region(x=1001, y=1000, name="Empty", access=AccessLevel.GENERAL,
                  region_flags=0, agents=0),
            Region(x=1002, y=1000, name="Active2", access=AccessLevel.GENERAL,
                  region_flags=0, agents=10),
        ]
        
        active = get_active_regions(regions, min_agents=1)
        
        assert len(active) == 2
        assert all(r.agents >= 1 for r in active)
