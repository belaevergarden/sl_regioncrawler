"""
SQLite persistence for region data.

Author: Isabela Evergarden
"""

import sqlite3
import json
from typing import List, Optional
from datetime import datetime, timezone
from .models import Region
import logging

logger = logging.getLogger(__name__)


class RegionDatabase:
    """SQLite database for storing region data."""

    def __init__(self, db_path: str = "regions.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _create_tables(self):
        """Create database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            name TEXT NOT NULL,
            access INTEGER NOT NULL,
            region_flags INTEGER NOT NULL,
            water_height INTEGER DEFAULT 20,
            agents INTEGER DEFAULT 0,
            map_image_id TEXT,
            handle INTEGER,
            discovered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(x, y)
        );
        
        CREATE INDEX IF NOT EXISTS idx_coordinates ON regions(x, y);
        CREATE INDEX IF NOT EXISTS idx_name ON regions(name);
        CREATE INDEX IF NOT EXISTS idx_access ON regions(access);
        CREATE INDEX IF NOT EXISTS idx_discovered ON regions(discovered_at);
        
        CREATE TABLE IF NOT EXISTS crawl_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            total_requests INTEGER DEFAULT 0,
            successful_requests INTEGER DEFAULT 0,
            failed_requests INTEGER DEFAULT 0,
            regions_discovered INTEGER DEFAULT 0,
            regions_matching INTEGER DEFAULT 0,
            duration_seconds REAL DEFAULT 0.0,
            search_criteria TEXT
        );
        """
        
        try:
            self.connection.executescript(schema)
            self.connection.commit()
            logger.info("Database schema created")
        except sqlite3.Error as e:
            logger.error(f"Schema creation failed: {e}")
            raise

    def save_region(self, region: Region) -> int:
        """
        Save or update a region.
        
        Args:
            region: Region to save
            
        Returns:
            Region ID
        """
        now = datetime.now(timezone.utc).isoformat()
        
        query = """
        INSERT INTO regions (x, y, name, access, region_flags, water_height,
                           agents, map_image_id, handle, discovered_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(x, y) DO UPDATE SET
            name = excluded.name,
            access = excluded.access,
            region_flags = excluded.region_flags,
            water_height = excluded.water_height,
            agents = excluded.agents,
            map_image_id = excluded.map_image_id,
            handle = excluded.handle,
            updated_at = excluded.updated_at
        """
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (
                region.x,
                region.y,
                region.name,
                region.access.value,
                region.region_flags,
                region.water_height,
                region.agents,
                str(region.map_image_id) if region.map_image_id else None,
                region.handle,
                now,
                now
            ))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to save region {region.name}: {e}")
            raise

    def save_regions(self, regions: List[Region]) -> int:
        """
        Save multiple regions.
        
        Args:
            regions: List of regions to save
            
        Returns:
            Number of regions saved
        """
        count = 0
        for region in regions:
            try:
                self.save_region(region)
                count += 1
            except sqlite3.Error:
                continue
        
        logger.info(f"Saved {count}/{len(regions)} regions")
        return count

    def get_region(self, x: int, y: int) -> Optional[Region]:
        """
        Get region by coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Region if found, None otherwise
        """
        query = "SELECT * FROM regions WHERE x = ? AND y = ?"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (x, y))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_region(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Failed to get region ({x}, {y}): {e}")
            return None

    def get_all_regions(self) -> List[Region]:
        """
        Get all regions from database.
        
        Returns:
            List of all regions
        """
        query = "SELECT * FROM regions ORDER BY name"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            regions = [self._row_to_region(row) for row in rows]
            logger.info(f"Retrieved {len(regions)} regions from database")
            return regions
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve regions: {e}")
            return []

    def search_regions(
        self,
        name_pattern: Optional[str] = None,
        min_x: Optional[int] = None,
        max_x: Optional[int] = None,
        min_y: Optional[int] = None,
        max_y: Optional[int] = None,
        access_levels: Optional[List[int]] = None
    ) -> List[Region]:
        """
        Search regions with filters.
        
        Args:
            name_pattern: SQL LIKE pattern for region name
            min_x: Minimum X coordinate
            max_x: Maximum X coordinate
            min_y: Minimum Y coordinate
            max_y: Maximum Y coordinate
            access_levels: List of access level values
            
        Returns:
            List of matching regions
        """
        query = "SELECT * FROM regions WHERE 1=1"
        params = []
        
        if name_pattern:
            query += " AND name LIKE ?"
            params.append(name_pattern)
        
        if min_x is not None:
            query += " AND x >= ?"
            params.append(min_x)
        
        if max_x is not None:
            query += " AND x <= ?"
            params.append(max_x)
        
        if min_y is not None:
            query += " AND y >= ?"
            params.append(min_y)
        
        if max_y is not None:
            query += " AND y <= ?"
            params.append(max_y)
        
        if access_levels:
            placeholders = ','.join('?' * len(access_levels))
            query += f" AND access IN ({placeholders})"
            params.extend(access_levels)
        
        query += " ORDER BY name"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            regions = [self._row_to_region(row) for row in rows]
            logger.info(f"Search found {len(regions)} regions")
            return regions
        except sqlite3.Error as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_statistics(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_regions': 0,
            'public_regions': 0,
            'sandbox_regions': 0,
            'by_access_level': {}
        }
        
        try:
            cursor = self.connection.cursor()
            
            # Total regions
            cursor.execute("SELECT COUNT(*) FROM regions")
            stats['total_regions'] = cursor.fetchone()[0]
            
            # Public regions (has PUBLIC_ALLOWED flag)
            cursor.execute("SELECT COUNT(*) FROM regions WHERE (region_flags & ?) != 0", 
                         (0x00020000,))
            stats['public_regions'] = cursor.fetchone()[0]
            
            # Sandbox regions
            cursor.execute("SELECT COUNT(*) FROM regions WHERE (region_flags & ?) != 0",
                         (0x00000100,))
            stats['sandbox_regions'] = cursor.fetchone()[0]
            
            # By access level
            cursor.execute("SELECT access, COUNT(*) FROM regions GROUP BY access")
            for row in cursor.fetchall():
                access_value, count = row
                from .models import AccessLevel
                try:
                    access_name = str(AccessLevel(access_value))
                except ValueError:
                    access_name = f"Unknown({access_value})"
                stats['by_access_level'][access_name] = count
            
        except sqlite3.Error as e:
            logger.error(f"Failed to get statistics: {e}")
        
        return stats

    def save_crawl_history(self, stats: dict) -> int:
        """
        Save crawl history record.
        
        Args:
            stats: Crawl statistics dictionary
            
        Returns:
            History record ID
        """
        query = """
        INSERT INTO crawl_history (
            started_at, completed_at, total_requests, successful_requests,
            failed_requests, regions_discovered, regions_matching,
            duration_seconds, search_criteria
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (
                stats.get('start_time'),
                stats.get('end_time'),
                stats.get('total_requests', 0),
                stats.get('successful_requests', 0),
                stats.get('failed_requests', 0),
                stats.get('regions_discovered', 0),
                stats.get('regions_matching', 0),
                stats.get('duration_seconds', 0.0),
                json.dumps(stats.get('search_criteria', {}))
            ))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to save crawl history: {e}")
            raise

    def _row_to_region(self, row: sqlite3.Row) -> Region:
        """
        Convert database row to Region object.
        
        Args:
            row: Database row
            
        Returns:
            Region object
        """
        from uuid import UUID
        from .models import AccessLevel
        
        map_image_id = None
        if row['map_image_id']:
            try:
                map_image_id = UUID(row['map_image_id'])
            except ValueError:
                pass
        
        return Region(
            x=row['x'],
            y=row['y'],
            name=row['name'],
            access=AccessLevel(row['access']),
            region_flags=row['region_flags'],
            water_height=row['water_height'],
            agents=row['agents'],
            map_image_id=map_image_id,
            handle=row['handle']
        )

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
