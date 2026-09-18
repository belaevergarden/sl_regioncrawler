"""
Main crawler orchestration logic.

Author: Isabela Evergarden
"""

import time
from typing import List, Optional
from datetime import datetime, timezone
from .models import Region, SearchCriteria, CrawlStatistics
from .protocol import MapBlockClient, scan_grid
from .filtering import RegionFilter, deduplicate_regions
from .persistence import RegionDatabase
from .reports import ReportGenerator, print_summary
import logging

logger = logging.getLogger(__name__)


class RegionCrawler:
    """
    Main crawler for discovering and analyzing Second Life regions.
    """

    def __init__(
        self,
        criteria: SearchCriteria,
        database_path: str = "regions.db",
        output_dir: str = "output"
    ):
        """
        Initialize crawler.
        
        Args:
            criteria: Search criteria for filtering
            database_path: Path to SQLite database
            output_dir: Output directory for reports
        """
        self.criteria = criteria
        self.database_path = database_path
        self.output_dir = output_dir
        
        self.client = MapBlockClient()
        self.filter = RegionFilter(criteria)
        self.statistics = CrawlStatistics()

    def crawl(
        self,
        step: int = 10,
        limit: Optional[int] = None
    ) -> List[Region]:
        """
        Execute region crawl.
        
        Args:
            step: Coordinate step size for MapBlock requests
            limit: Optional limit on number of regions to discover
            
        Returns:
            List of discovered regions matching criteria
        """
        logger.info("Starting region crawl")
        
        # Record start time
        self.statistics.start_time = datetime.now(timezone.utc).isoformat()
        start_timestamp = time.time()
        
        # Discover regions
        logger.info(f"Scanning grid: ({self.criteria.min_x}-{self.criteria.max_x}, "
                   f"{self.criteria.min_y}-{self.criteria.max_y})")
        
        all_regions = []
        request_count = 0
        
        for x in range(self.criteria.min_x, self.criteria.max_x, step):
            for y in range(self.criteria.min_y, self.criteria.max_y, step):
                # Check limit
                if limit and len(all_regions) >= limit:
                    logger.info(f"Reached region limit: {limit}")
                    break
                
                request_count += 1
                self.statistics.total_requests += 1
                
                try:
                    regions = self.client.request_mapblock(
                        x,
                        min(x + step, self.criteria.max_x),
                        y,
                        min(y + step, self.criteria.max_y)
                    )
                    
                    all_regions.extend(regions)
                    self.statistics.successful_requests += 1
                    
                    if request_count % 10 == 0:
                        logger.info(f"Progress: {request_count} requests, "
                                  f"{len(all_regions)} regions discovered")
                    
                except Exception as e:
                    logger.warning(f"Request failed for ({x}, {y}): {e}")
                    self.statistics.failed_requests += 1
                    continue
            
            if limit and len(all_regions) >= limit:
                break
        
        # Remove duplicates
        all_regions = deduplicate_regions(all_regions)
        self.statistics.regions_discovered = len(all_regions)
        
        logger.info(f"Discovered {len(all_regions)} unique regions")
        
        # Filter regions
        matching_regions = self.filter.filter_regions(all_regions)
        self.statistics.regions_matching = len(matching_regions)
        
        logger.info(f"{len(matching_regions)} regions match criteria")
        
        # Rank regions
        ranked_regions = self.filter.rank_regions(matching_regions)
        
        # Record end time
        self.statistics.end_time = datetime.now(timezone.utc).isoformat()
        self.statistics.duration_seconds = time.time() - start_timestamp
        
        logger.info(f"Crawl complete in {self.statistics.duration_seconds:.2f}s")
        
        return ranked_regions

    def save_to_database(self, regions: List[Region]) -> int:
        """
        Save regions to database.
        
        Args:
            regions: List of regions to save
            
        Returns:
            Number of regions saved
        """
        logger.info("Saving regions to database")
        
        with RegionDatabase(self.database_path) as db:
            count = db.save_regions(regions)
            
            # Save crawl history
            stats_dict = self.statistics.to_dict()
            stats_dict['search_criteria'] = self.criteria.to_dict()
            db.save_crawl_history(stats_dict)
        
        logger.info(f"Saved {count} regions to database")
        return count

    def generate_reports(
        self,
        regions: List[Region],
        limit: int = 100
    ) -> dict:
        """
        Generate reports for discovered regions.
        
        Args:
            regions: List of regions (should be pre-ranked)
            limit: Maximum number of regions in report
            
        Returns:
            Dictionary of generated report paths
        """
        logger.info("Generating reports")
        
        generator = ReportGenerator(self.output_dir)
        
        reports = {}
        reports['markdown'] = generator.generate_markdown_report(
            regions, self.statistics, limit=limit
        )
        reports['json'] = generator.generate_json_report(
            regions, self.statistics
        )
        reports['csv'] = generator.generate_csv_report(regions)
        
        logger.info(f"Generated {len(reports)} reports")
        return reports

    def run(
        self,
        step: int = 10,
        limit: Optional[int] = None,
        save_to_db: bool = True,
        generate_reports: bool = True,
        report_limit: int = 100
    ) -> List[Region]:
        """
        Run complete crawl workflow.
        
        Args:
            step: Coordinate step size
            limit: Optional limit on regions to discover
            save_to_db: Whether to save to database
            generate_reports: Whether to generate reports
            report_limit: Maximum regions in reports
            
        Returns:
            List of ranked regions
        """
        logger.info("=" * 60)
        logger.info("Second Life Region Crawler")
        logger.info("Author: Isabela Evergarden")
        logger.info("=" * 60)
        
        # Execute crawl
        regions = self.crawl(step=step, limit=limit)
        
        # Save to database
        if save_to_db and regions:
            self.save_to_database(regions)
        
        # Generate reports
        if generate_reports and regions:
            self.generate_reports(regions, limit=report_limit)
        
        # Print summary
        print_summary(regions, self.statistics)
        
        return regions


def quick_crawl(
    min_x: int = 950,
    max_x: int = 1050,
    min_y: int = 950,
    max_y: int = 1050,
    public_only: bool = True
) -> List[Region]:
    """
    Quick crawl with default settings.
    
    Args:
        min_x: Minimum X coordinate
        max_x: Maximum X coordinate
        min_y: Minimum Y coordinate
        max_y: Maximum Y coordinate
        public_only: Only include public regions
        
    Returns:
        List of ranked regions
    """
    criteria = SearchCriteria(
        public_only=public_only,
        min_x=min_x,
        max_x=max_x,
        min_y=min_y,
        max_y=max_y
    )
    
    crawler = RegionCrawler(criteria)
    return crawler.run()
