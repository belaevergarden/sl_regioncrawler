"""
Data models for Second Life Region Crawler.

Author: Isabela Evergarden
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import IntEnum
from uuid import UUID


class AccessLevel(IntEnum):
    """Region access/maturity levels."""
    UNKNOWN = 0
    GENERAL = 13    # PG rating
    MODERATE = 21   # Mature rating
    ADULT = 42      # Adult rating

    def __str__(self) -> str:
        names = {
            0: "Unknown",
            13: "General",
            21: "Moderate",
            42: "Adult"
        }
        return names.get(self.value, f"Unknown({self.value})")


class RegionFlags(IntEnum):
    """Second Life region flags."""
    ALLOW_DAMAGE = 0x00000001
    ALLOW_LANDMARK = 0x00000002
    ALLOW_SET_HOME = 0x00000004
    RESET_HOME_ON_TELEPORT = 0x00000008
    SUN_FIXED = 0x00000010
    TAX_FREE = 0x00000020
    BLOCK_TERRAFORM = 0x00000040
    BLOCK_LAND_RESELL = 0x00000080
    SANDBOX = 0x00000100
    ALLOW_ENV_OVERRIDE = 0x00000200
    SKIP_COLLISIONS = 0x00001000
    SKIP_SCRIPTS = 0x00002000
    SKIP_PHYSICS = 0x00004000
    EXTERNALLY_VISIBLE = 0x00008000
    MAINLAND_VISIBLE = 0x00010000
    PUBLIC_ALLOWED = 0x00020000
    BLOCK_DWELL = 0x00040000
    NO_FLY = 0x00080000
    ALLOW_DIRECT_TELEPORT = 0x00100000
    ESTATE_SKIP_SCRIPTS = 0x00200000
    RESTRICT_PUSH_OBJECT = 0x00400000
    DENY_ANONYMOUS = 0x00800000
    ALLOW_PARCEL_CHANGES = 0x01000000
    BLOCK_FLY_OVER = 0x02000000
    ALLOW_VOICE = 0x04000000
    BLOCK_PARCEL_SEARCH = 0x08000000
    DENY_AGE_UNVERIFIED = 0x10000000


@dataclass
class Region:
    """
    Represents a Second Life region.
    
    Attributes:
        x: Region X coordinate on the grid
        y: Region Y coordinate on the grid
        name: Region name
        access: Access/maturity level
        region_flags: Binary flags indicating region properties
        water_height: Water height in meters
        agents: Current number of agents in the region
        map_image_id: UUID of the region's map tile texture
        handle: Unique region handle (calculated from coordinates)
    """
    x: int
    y: int
    name: str
    access: AccessLevel
    region_flags: int
    water_height: int = 20
    agents: int = 0
    map_image_id: Optional[UUID] = None
    handle: Optional[int] = None

    def __post_init__(self):
        """Calculate region handle after initialization."""
        if self.handle is None:
            self.handle = self.calculate_handle()
        
        # Ensure access is AccessLevel enum
        if isinstance(self.access, int):
            try:
                self.access = AccessLevel(self.access)
            except ValueError:
                self.access = AccessLevel.UNKNOWN

    def calculate_handle(self) -> int:
        """
        Calculate unique region handle from coordinates.
        
        Returns:
            64-bit region handle
        """
        return (self.x << 32) | self.y

    def has_flag(self, flag: RegionFlags) -> bool:
        """
        Check if region has a specific flag set.
        
        Args:
            flag: RegionFlags value to check
            
        Returns:
            True if flag is set, False otherwise
        """
        return bool(self.region_flags & flag)

    def get_flags(self) -> List[str]:
        """
        Get list of flag names set for this region.
        
        Returns:
            List of flag names
        """
        flags = []
        for flag in RegionFlags:
            if self.has_flag(flag):
                flags.append(flag.name)
        return flags

    def is_public(self) -> bool:
        """
        Check if region allows public access.
        
        Returns:
            True if public access is allowed
        """
        return self.has_flag(RegionFlags.PUBLIC_ALLOWED)

    def is_sandbox(self) -> bool:
        """
        Check if region is a sandbox.
        
        Returns:
            True if region has sandbox flag
        """
        return self.has_flag(RegionFlags.SANDBOX)

    def allows_scripts(self) -> bool:
        """
        Check if region allows scripts.
        
        Returns:
            True if scripts are allowed (no skip scripts flag)
        """
        return not (self.has_flag(RegionFlags.SKIP_SCRIPTS) or 
                   self.has_flag(RegionFlags.ESTATE_SKIP_SCRIPTS))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert region to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'x': self.x,
            'y': self.y,
            'name': self.name,
            'access': str(self.access),
            'access_value': self.access.value,
            'region_flags': self.region_flags,
            'flags': self.get_flags(),
            'water_height': self.water_height,
            'agents': self.agents,
            'map_image_id': str(self.map_image_id) if self.map_image_id else None,
            'handle': self.handle,
            'is_public': self.is_public(),
            'is_sandbox': self.is_sandbox(),
            'allows_scripts': self.allows_scripts()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Region':
        """
        Create region from dictionary.
        
        Args:
            data: Dictionary with region data
            
        Returns:
            Region instance
        """
        # Convert map_image_id string to UUID if present
        map_image_id = data.get('map_image_id')
        if map_image_id and isinstance(map_image_id, str):
            try:
                map_image_id = UUID(map_image_id)
            except ValueError:
                map_image_id = None
        
        return cls(
            x=data['x'],
            y=data['y'],
            name=data['name'],
            access=data.get('access_value', data.get('access', 0)),
            region_flags=data.get('region_flags', 0),
            water_height=data.get('water_height', 20),
            agents=data.get('agents', 0),
            map_image_id=map_image_id,
            handle=data.get('handle')
        )

    def __str__(self) -> str:
        return f"Region({self.name} at ({self.x}, {self.y}), {self.access})"

    def __repr__(self) -> str:
        return (f"Region(x={self.x}, y={self.y}, name='{self.name}', "
                f"access={self.access}, region_flags=0x{self.region_flags:08X})")


@dataclass
class SearchCriteria:
    """
    Configuration for region search and filtering.
    
    Attributes:
        public_only: Only include public-access regions
        include_general: Include General-rated regions
        include_moderate: Include Moderate-rated regions
        include_adult: Include Adult-rated regions
        exclude_patterns: List of regex patterns for region names to exclude
        min_x: Minimum X coordinate
        max_x: Maximum X coordinate
        min_y: Minimum Y coordinate
        max_y: Maximum Y coordinate
        require_sandbox: Only include sandbox regions
        require_scripts: Only include regions that allow scripts
    """
    public_only: bool = True
    include_general: bool = True
    include_moderate: bool = True
    include_adult: bool = False
    exclude_patterns: List[str] = field(default_factory=list)
    min_x: int = 900
    max_x: int = 1200
    min_y: int = 900
    max_y: int = 1200
    require_sandbox: bool = False
    require_scripts: bool = False

    def matches(self, region: Region) -> bool:
        """
        Check if a region matches the search criteria.
        
        Args:
            region: Region to check
            
        Returns:
            True if region matches all criteria
        """
        # Check public access
        if self.public_only and not region.is_public():
            return False

        # Check maturity rating
        if region.access == AccessLevel.GENERAL and not self.include_general:
            return False
        if region.access == AccessLevel.MODERATE and not self.include_moderate:
            return False
        if region.access == AccessLevel.ADULT and not self.include_adult:
            return False

        # Check coordinate bounds
        if not (self.min_x <= region.x <= self.max_x):
            return False
        if not (self.min_y <= region.y <= self.max_y):
            return False

        # Check sandbox requirement
        if self.require_sandbox and not region.is_sandbox():
            return False

        # Check script requirement
        if self.require_scripts and not region.allows_scripts():
            return False

        # Check exclusion patterns
        import re
        for pattern in self.exclude_patterns:
            if re.search(pattern, region.name, re.IGNORECASE):
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert criteria to dictionary."""
        return {
            'public_only': self.public_only,
            'include_general': self.include_general,
            'include_moderate': self.include_moderate,
            'include_adult': self.include_adult,
            'exclude_patterns': self.exclude_patterns,
            'min_x': self.min_x,
            'max_x': self.max_x,
            'min_y': self.min_y,
            'max_y': self.max_y,
            'require_sandbox': self.require_sandbox,
            'require_scripts': self.require_scripts
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchCriteria':
        """Create criteria from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class CrawlStatistics:
    """
    Statistics for a crawl operation.
    
    Attributes:
        total_requests: Total MapBlock requests sent
        successful_requests: Successful requests
        failed_requests: Failed requests
        regions_discovered: Total regions discovered
        regions_matching: Regions matching search criteria
        start_time: Crawl start timestamp
        end_time: Crawl end timestamp
        duration_seconds: Total duration in seconds
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    regions_discovered: int = 0
    regions_matching: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'regions_discovered': self.regions_discovered,
            'regions_matching': self.regions_matching,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': self.duration_seconds
        }
