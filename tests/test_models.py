"""
Unit tests for data models.

Author: Isabela Evergarden
"""

import pytest
from uuid import UUID
from sl_regioncrawler.models import (
    Region, AccessLevel, RegionFlags,
    SearchCriteria, CrawlStatistics
)


class TestAccessLevel:
    """Test AccessLevel enum."""
    
    def test_access_level_values(self):
        """Test access level enum values."""
        assert AccessLevel.GENERAL == 13
        assert AccessLevel.MODERATE == 21
        assert AccessLevel.ADULT == 42
    
    def test_access_level_string(self):
        """Test string representation."""
        assert str(AccessLevel.GENERAL) == "General"
        assert str(AccessLevel.MODERATE) == "Moderate"
        assert str(AccessLevel.ADULT) == "Adult"


class TestRegion:
    """Test Region model."""
    
    def test_region_creation(self):
        """Test basic region creation."""
        region = Region(
            x=1000,
            y=1000,
            name="Test Region",
            access=AccessLevel.GENERAL,
            region_flags=0x00020000  # PUBLIC_ALLOWED
        )
        
        assert region.x == 1000
        assert region.y == 1000
        assert region.name == "Test Region"
        assert region.access == AccessLevel.GENERAL
        assert region.region_flags == 0x00020000
    
    def test_region_handle_calculation(self):
        """Test region handle calculation."""
        region = Region(
            x=1000,
            y=2000,
            name="Test",
            access=AccessLevel.GENERAL,
            region_flags=0
        )
        
        expected_handle = (1000 << 32) | 2000
        assert region.handle == expected_handle
    
    def test_region_has_flag(self):
        """Test flag checking."""
        region = Region(
            x=1000,
            y=1000,
            name="Sandbox",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.SANDBOX | RegionFlags.PUBLIC_ALLOWED
        )
        
        assert region.has_flag(RegionFlags.SANDBOX)
        assert region.has_flag(RegionFlags.PUBLIC_ALLOWED)
        assert not region.has_flag(RegionFlags.SKIP_SCRIPTS)
    
    def test_region_is_public(self):
        """Test public access detection."""
        public_region = Region(
            x=1000, y=1000, name="Public",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED
        )
        
        private_region = Region(
            x=1000, y=1000, name="Private",
            access=AccessLevel.GENERAL,
            region_flags=0
        )
        
        assert public_region.is_public()
        assert not private_region.is_public()
    
    def test_region_is_sandbox(self):
        """Test sandbox detection."""
        sandbox = Region(
            x=1000, y=1000, name="Sandbox",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.SANDBOX
        )
        
        regular = Region(
            x=1000, y=1000, name="Regular",
            access=AccessLevel.GENERAL,
            region_flags=0
        )
        
        assert sandbox.is_sandbox()
        assert not regular.is_sandbox()
    
    def test_region_allows_scripts(self):
        """Test script permission detection."""
        scripts_allowed = Region(
            x=1000, y=1000, name="Scripts OK",
            access=AccessLevel.GENERAL,
            region_flags=0
        )
        
        scripts_blocked = Region(
            x=1000, y=1000, name="No Scripts",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.SKIP_SCRIPTS
        )
        
        assert scripts_allowed.allows_scripts()
        assert not scripts_blocked.allows_scripts()
    
    def test_region_to_dict(self):
        """Test dictionary serialization."""
        region = Region(
            x=1000,
            y=1000,
            name="Test Region",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED,
            agents=5
        )
        
        data = region.to_dict()
        
        assert data['x'] == 1000
        assert data['y'] == 1000
        assert data['name'] == "Test Region"
        assert data['access'] == "General"
        assert data['agents'] == 5
        assert data['is_public'] is True
    
    def test_region_from_dict(self):
        """Test dictionary deserialization."""
        data = {
            'x': 1000,
            'y': 1000,
            'name': "Test Region",
            'access_value': 13,
            'region_flags': 0x00020000,
            'agents': 5
        }
        
        region = Region.from_dict(data)
        
        assert region.x == 1000
        assert region.y == 1000
        assert region.name == "Test Region"
        assert region.access == AccessLevel.GENERAL
        assert region.agents == 5


class TestSearchCriteria:
    """Test SearchCriteria model."""
    
    def test_default_criteria(self):
        """Test default search criteria."""
        criteria = SearchCriteria()
        
        assert criteria.public_only is True
        assert criteria.include_general is True
        assert criteria.include_moderate is True
        assert criteria.include_adult is False
    
    def test_criteria_matches_public(self):
        """Test public region matching."""
        criteria = SearchCriteria(public_only=True)
        
        public_region = Region(
            x=1000, y=1000, name="Public",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED
        )
        
        private_region = Region(
            x=1000, y=1000, name="Private",
            access=AccessLevel.GENERAL,
            region_flags=0
        )
        
        assert criteria.matches(public_region)
        assert not criteria.matches(private_region)
    
    def test_criteria_matches_maturity(self):
        """Test maturity rating matching."""
        criteria = SearchCriteria(
            include_general=True,
            include_moderate=False,
            include_adult=False
        )
        
        general_region = Region(
            x=1000, y=1000, name="General",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED
        )
        
        moderate_region = Region(
            x=1000, y=1000, name="Moderate",
            access=AccessLevel.MODERATE,
            region_flags=RegionFlags.PUBLIC_ALLOWED
        )
        
        assert criteria.matches(general_region)
        assert not criteria.matches(moderate_region)
    
    def test_criteria_matches_coordinates(self):
        """Test coordinate range matching."""
        criteria = SearchCriteria(min_x=1000, max_x=1100, min_y=1000, max_y=1100)
        
        inside_region = Region(
            x=1050, y=1050, name="Inside",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED
        )
        
        outside_region = Region(
            x=1200, y=1200, name="Outside",
            access=AccessLevel.GENERAL,
            region_flags=RegionFlags.PUBLIC_ALLOWED
        )
        
        assert criteria.matches(inside_region)
        assert not criteria.matches(outside_region)
    
    def test_criteria_to_dict(self):
        """Test criteria serialization."""
        criteria = SearchCriteria(
            public_only=True,
            include_general=True,
            min_x=1000,
            max_x=1100
        )
        
        data = criteria.to_dict()
        
        assert data['public_only'] is True
        assert data['include_general'] is True
        assert data['min_x'] == 1000
        assert data['max_x'] == 1100


class TestCrawlStatistics:
    """Test CrawlStatistics model."""
    
    def test_statistics_creation(self):
        """Test statistics creation."""
        stats = CrawlStatistics(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            regions_discovered=250,
            regions_matching=80
        )
        
        assert stats.total_requests == 100
        assert stats.successful_requests == 95
        assert stats.failed_requests == 5
        assert stats.regions_discovered == 250
        assert stats.regions_matching == 80
    
    def test_statistics_to_dict(self):
        """Test statistics serialization."""
        stats = CrawlStatistics(
            total_requests=100,
            regions_discovered=250
        )
        
        data = stats.to_dict()
        
        assert data['total_requests'] == 100
        assert data['regions_discovered'] == 250
