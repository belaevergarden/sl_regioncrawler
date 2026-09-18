"""
Command-line interface for Second Life Region Crawler.

Author: Isabela Evergarden
"""

import argparse
import sys
import logging
import os
from .models import SearchCriteria
from .crawler import RegionCrawler
from . import __version__


def setup_logging(verbose: bool = False):
    """
    Configure logging.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description='Second Life Region Crawler - Discover and analyze SL regions',
        epilog='Author: Isabela Evergarden | '
               'https://github.com/belaevergarden/sl_regioncrawler'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'sl_regioncrawler {__version__}'
    )
    
    # Search area
    search_group = parser.add_argument_group('Search Area')
    search_group.add_argument(
        '--min-x',
        type=int,
        default=950,
        help='Minimum X coordinate (default: 950)'
    )
    search_group.add_argument(
        '--max-x',
        type=int,
        default=1050,
        help='Maximum X coordinate (default: 1050)'
    )
    search_group.add_argument(
        '--min-y',
        type=int,
        default=950,
        help='Minimum Y coordinate (default: 950)'
    )
    search_group.add_argument(
        '--max-y',
        type=int,
        default=1050,
        help='Maximum Y coordinate (default: 1050)'
    )
    
    # Filters
    filter_group = parser.add_argument_group('Filters')
    filter_group.add_argument(
        '--public-only',
        action='store_true',
        default=True,
        help='Only include public regions (default: True)'
    )
    filter_group.add_argument(
        '--include-private',
        action='store_true',
        help='Include private regions'
    )
    filter_group.add_argument(
        '--general',
        action='store_true',
        default=True,
        help='Include General-rated regions (default: True)'
    )
    filter_group.add_argument(
        '--moderate',
        action='store_true',
        default=True,
        help='Include Moderate-rated regions (default: True)'
    )
    filter_group.add_argument(
        '--adult',
        action='store_true',
        help='Include Adult-rated regions (default: False)'
    )
    filter_group.add_argument(
        '--sandbox-only',
        action='store_true',
        help='Only include sandbox regions'
    )
    filter_group.add_argument(
        '--scripts-only',
        action='store_true',
        help='Only include regions that allow scripts'
    )
    
    # Crawl options
    crawl_group = parser.add_argument_group('Crawl Options')
    crawl_group.add_argument(
        '--limit',
        type=int,
        help='Limit number of regions to discover'
    )
    crawl_group.add_argument(
        '--step',
        type=int,
        default=10,
        help='Coordinate step size for requests (default: 10)'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory for reports (default: output)'
    )
    output_group.add_argument(
        '--database',
        type=str,
        default='regions.db',
        help='SQLite database path (default: regions.db)'
    )
    output_group.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save to database'
    )
    output_group.add_argument(
        '--no-reports',
        action='store_true',
        help='Do not generate reports'
    )
    output_group.add_argument(
        '--report-limit',
        type=int,
        default=100,
        help='Maximum regions in report (default: 100)'
    )
    
    # General options
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def main(argv=None):
    """
    Main CLI entry point.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Build search criteria
        criteria = SearchCriteria(
            public_only=args.public_only and not args.include_private,
            include_general=args.general,
            include_moderate=args.moderate,
            include_adult=args.adult,
            min_x=args.min_x,
            max_x=args.max_x,
            min_y=args.min_y,
            max_y=args.max_y,
            require_sandbox=args.sandbox_only,
            require_scripts=args.scripts_only
        )
        
        logger.info("Search Criteria:")
        logger.info(f"  Coordinates: ({args.min_x}-{args.max_x}, {args.min_y}-{args.max_y})")
        logger.info(f"  Public only: {criteria.public_only}")
        logger.info(f"  Maturity: G={criteria.include_general}, "
                   f"M={criteria.include_moderate}, A={criteria.include_adult}")
        logger.info(f"  Sandbox only: {criteria.require_sandbox}")
        logger.info(f"  Scripts only: {criteria.require_scripts}")
        
        # Create crawler
        crawler = RegionCrawler(
            criteria=criteria,
            database_path=args.database,
            output_dir=args.output
        )
        
        # Run crawl
        regions = crawler.run(
            step=args.step,
            limit=args.limit,
            save_to_db=not args.no_save,
            generate_reports=not args.no_reports,
            report_limit=args.report_limit
        )
        
        logger.info(f"Crawl complete: {len(regions)} regions")
        
        if not args.no_reports:
            logger.info(f"Reports saved to: {args.output}/")
        
        if not args.no_save:
            logger.info(f"Database: {args.database}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Crawl interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
