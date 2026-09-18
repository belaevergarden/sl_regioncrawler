"""
Region filtering and ranking logic.

Author: Isabela Evergarden
"""

from typing import List, Callable
from .models import Region, SearchCriteria
import logging

logger = logging.getLogger(__name__)


class RegionFilter:
    """Filter and rank regions based on criteria."""

    def __init__(self, criteria: SearchCriteria):
        """
        Initialize region filter.
        
        Args:
            criteria: Search criteria for filtering
        """
        self.criteria = criteria

    def filter_regions(self, regions: List[Region]) -> List[Region]:
        """
        Filter regions based on search criteria.
        
        Args:
            regions: List of regions to filter
            
        Returns:
            List of regions matching criteria
        """
        logger.info(f"Filtering {len(regions)} regions")
        
        matching = [r for r in regions if self.criteria.matches(r)]
        
        logger.info(f"{len(matching)} regions match criteria")
        return matching

    def rank_regions(self, regions: List[Region]) -> List[Region]:
        """
        Rank regions by suitability score.
        
        Scoring factors:
        - Public access: +100
        - Sandbox: +50
        - Allows scripts: +30
        - Active (has agents): +10 per agent
        - General rating: +20
        - Moderate rating: +10
        
        Args:
            regions: List of regions to rank
            
        Returns:
            Sorted list of regions (highest score first)
        """
        logger.info(f"Ranking {len(regions)} regions")
        
        scored_regions = [(r, self._calculate_score(r)) for r in regions]
        scored_regions.sort(key=lambda x: x[1], reverse=True)
        
        ranked = [r for r, score in scored_regions]
        
        logger.debug(f"Top region: {ranked[0].name if ranked else 'None'}")
        return ranked

    def _calculate_score(self, region: Region) -> float:
        """
        Calculate suitability score for a region.
        
        Args:
            region: Region to score
            
        Returns:
            Suitability score
        """
        score = 0.0
        
        # Public access is highly desirable
        if region.is_public():
            score += 100
        
        # Sandbox regions allow rezzing
        if region.is_sandbox():
            score += 50
        
        # Script support is important
        if region.allows_scripts():
            score += 30
        
        # Active regions are better
        score += region.agents * 10
        
        # Rating preferences
        from .models import AccessLevel
        if region.access == AccessLevel.GENERAL:
            score += 20
        elif region.access == AccessLevel.MODERATE:
            score += 10
        
        return score

    def get_top_regions(
        self,
        regions: List[Region],
        limit: int = 100
    ) -> List[Region]:
        """
        Get top N regions after filtering and ranking.
        
        Args:
            regions: List of regions to process
            limit: Maximum number of regions to return
            
        Returns:
            Top N regions
        """
        filtered = self.filter_regions(regions)
        ranked = self.rank_regions(filtered)
        return ranked[:limit]


def deduplicate_regions(regions: List[Region]) -> List[Region]:
    """
    Remove duplicate regions (same coordinates).
    
    Args:
        regions: List of regions
        
    Returns:
        List with duplicates removed
    """
    seen = set()
    unique = []
    
    for region in regions:
        key = (region.x, region.y)
        if key not in seen:
            seen.add(key)
            unique.append(region)
        else:
            logger.debug(f"Duplicate region: {region.name} at ({region.x}, {region.y})")
    
    if len(unique) < len(regions):
        logger.info(f"Removed {len(regions) - len(unique)} duplicate regions")
    
    return unique


def filter_by_predicate(
    regions: List[Region],
    predicate: Callable[[Region], bool]
) -> List[Region]:
    """
    Filter regions using a custom predicate function.
    
    Args:
        regions: List of regions to filter
        predicate: Function that returns True for regions to keep
        
    Returns:
        Filtered list of regions
    """
    return [r for r in regions if predicate(r)]


def get_public_sandboxes(regions: List[Region]) -> List[Region]:
    """
    Get public sandbox regions.
    
    Args:
        regions: List of regions
        
    Returns:
        Public sandbox regions
    """
    return filter_by_predicate(
        regions,
        lambda r: r.is_public() and r.is_sandbox()
    )


def get_script_enabled_regions(regions: List[Region]) -> List[Region]:
    """
    Get regions that allow scripts.
    
    Args:
        regions: List of regions
        
    Returns:
        Script-enabled regions
    """
    return filter_by_predicate(regions, lambda r: r.allows_scripts())


def get_active_regions(
    regions: List[Region],
    min_agents: int = 1
) -> List[Region]:
    """
    Get active regions with minimum number of agents.
    
    Args:
        regions: List of regions
        min_agents: Minimum number of agents required
        
    Returns:
        Active regions
    """
    return filter_by_predicate(regions, lambda r: r.agents >= min_agents)
