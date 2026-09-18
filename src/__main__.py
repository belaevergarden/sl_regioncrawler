"""
Command-line interface for Second Life Region Crawler.

Author: Isabela Evergarden
"""

import argparse
import sys
import logging
import os
import yaml
from pathlib import Path
from .models import SearchCriteria
from .crawler import RegionCrawler
from . import __version__


def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            return config or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")


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
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to YAML configuration file'
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
    
    # Load config file if provided
    config = {}
    if args.config:
        try:
            config = load_config(args.config)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return 1
    
    # Setup logging
    verbose = args.verbose or config.get('logging', {}).get('verbose', False)
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    # Log config file if loaded
    if args.config:
        logger.info(f"Loaded configuration from: {args.config}")
    
    try:
        # Get config sections
        search_config = config.get('search', {})
        discovery_config = config.get('discovery', {})
        output_config = config.get('output', {})
        database_config = config.get('database', {})
        
        # Create output directory
        output_dir = args.output if args.output != 'output' else output_config.get('directory', 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Build search criteria (command-line args override config file)
        maturity_config = search_config.get('maturity', {})
        
        criteria = SearchCriteria(
            public_only=(args.public_only and not args.include_private) 
                       if not args.include_private 
                       else search_config.get('public_only', True),
            include_general=args.general if args.general 
                          else maturity_config.get('general', True),
            include_moderate=args.moderate if args.moderate 
                           else maturity_config.get('moderate', True),
            include_adult=args.adult if args.adult 
                        else maturity_config.get('adult', False),
            min_x=args.min_x if args.min_x != 950 
                 else discovery_config.get('min_x', 950),
            max_x=args.max_x if args.max_x != 1050 
                 else discovery_config.get('max_x', 1050),
            min_y=args.min_y if args.min_y != 950 
                 else discovery_config.get('min_y', 950),
            max_y=args.max_y if args.max_y != 1050 
                 else discovery_config.get('max_y', 1050),
            require_sandbox=args.sandbox_only or search_config.get('require_sandbox', False),
            require_scripts=args.scripts_only or search_config.get('require_scripts', False),
            exclude_patterns=search_config.get('exclude_patterns', [])
        )
        
        logger.info("Search Criteria:")
        logger.info(f"  Coordinates: ({args.min_x}-{args.max_x}, {args.min_y}-{args.max_y})")
        logger.info(f"  Public only: {criteria.public_only}")
        logger.info(f"  Maturity: G={criteria.include_general}, "
                   f"M={criteria.include_moderate}, A={criteria.include_adult}")
        logger.info(f"  Sandbox only: {criteria.require_sandbox}")
        logger.info(f"  Scripts only: {criteria.require_scripts}")
        
        # Create crawler
        database_path = args.database if args.database != 'regions.db' \
                       else database_config.get('path', 'regions.db')
        
        crawler = RegionCrawler(
            criteria=criteria,
            database_path=database_path,
            output_dir=output_dir
        )
        
        # Get crawl parameters
        step = args.step if args.step != 10 \
              else discovery_config.get('step', 10)
        report_limit = args.report_limit if args.report_limit != 100 \
                      else output_config.get('top_regions', 100)
        save_to_db = (not args.no_save) and database_config.get('save_results', True)
        
        # Run crawl
        regions = crawler.run(
            step=step,
            limit=args.limit,
            save_to_db=save_to_db,
            generate_reports=not args.no_reports,
            report_limit=report_limit
        )
        
        logger.info(f"Crawl complete: {len(regions)} regions")
        
        if not args.no_reports:
            logger.info(f"Reports saved to: {output_dir}/")
        
        if save_to_db:
            logger.info(f"Database: {database_path}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Crawl interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Crawl failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
