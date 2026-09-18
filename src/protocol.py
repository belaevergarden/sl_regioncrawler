"""
Second Life MapBlock Protocol Client.

Author: Isabela Evergarden

Note: This is a simplified implementation for demonstration.
Real Second Life protocol requires full message template parsing.
"""

import socket
import struct
import random
from typing import List, Optional, Tuple
from uuid import UUID
from .models import Region, AccessLevel
import logging

logger = logging.getLogger(__name__)

# Null UUID for anonymous requests
NULL_UUID = UUID('00000000-0000-0000-0000-000000000000')


class ProtocolError(Exception):
    """Raised when protocol communication fails."""
    pass


class MapBlockClient:
    """
    Client for Second Life MapBlock protocol.
    
    Attributes:
        server: Grid server hostname
        port: UDP port number
        timeout: Request timeout in seconds
        max_retries: Maximum connection retry attempts
    """

    def __init__(
        self,
        server: str = "login.agni.lindenlab.com",
        port: int = 13000,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize MapBlock client.
        
        Args:
            server: Grid server hostname
            port: UDP port number
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.server = server
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self._sequence_number = 0

    def request_mapblock(
        self,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int
    ) -> List[Region]:
        """
        Request MapBlock data for a coordinate range.
        
        Args:
            min_x: Minimum X coordinate
            max_x: Maximum X coordinate
            min_y: Minimum Y coordinate
            max_y: Maximum Y coordinate
            
        Returns:
            List of discovered regions
            
        Raises:
            ProtocolError: If request fails after all retries
        """
        logger.debug(f"Requesting MapBlock ({min_x}-{max_x}, {min_y}-{max_y})")

        for attempt in range(self.max_retries):
            try:
                return self._send_request(min_x, max_x, min_y, max_y)
            except socket.timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise ProtocolError("Max retries exceeded")
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt == self.max_retries - 1:
                    raise ProtocolError(f"Request failed: {e}")

        return []

    def _send_request(
        self,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int
    ) -> List[Region]:
        """
        Send MapBlock request and parse response.
        
        Note: This is a mock implementation that generates sample data.
        A real implementation would send actual UDP packets to SL grid servers.
        
        Args:
            min_x: Minimum X coordinate
            max_x: Maximum X coordinate
            min_y: Minimum Y coordinate
            max_y: Maximum Y coordinate
            
        Returns:
            List of regions
        """
        # Mock implementation: Generate sample regions
        # In production, this would build and send actual UDP packets
        
        logger.info(f"Mock request for range ({min_x}-{max_x}, {min_y}-{max_y})")
        
        regions = self._generate_mock_regions(min_x, max_x, min_y, max_y)
        
        logger.info(f"Discovered {len(regions)} regions")
        return regions

    def _generate_mock_regions(
        self,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int
    ) -> List[Region]:
        """
        Generate mock region data for testing.
        
        In production, this would parse actual MapBlockReply packets.
        
        Args:
            min_x: Minimum X coordinate
            max_x: Maximum X coordinate
            min_y: Minimum Y coordinate
            max_y: Maximum Y coordinate
            
        Returns:
            List of mock regions
        """
        regions = []
        
        # Sample region names
        region_names = [
            "Sandbox Island",
            "Builder's Haven",
            "Public Plaza",
            "Creator's Workshop",
            "Free Build Zone",
            "Community Center",
            "Welcome Area",
            "Open Sim Space",
            "Maker's District",
            "Innovation Hub",
            "Test Region",
            "Development Zone",
            "Prototype Lab",
            "Experimental Area",
            "Beta Region",
            "Private Estate",
            "Members Only",
            "Restricted Zone",
            "Adult Playground",
            "Mature Content Area"
        ]
        
        # Generate 2-5 random regions in the coordinate range
        num_regions = random.randint(2, 5)
        
        for i in range(num_regions):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            name = random.choice(region_names)
            
            # Random access level
            access_values = [
                AccessLevel.GENERAL,
                AccessLevel.GENERAL,
                AccessLevel.MODERATE,
                AccessLevel.ADULT
            ]
            access = random.choice(access_values)
            
            # Random flags
            flags = 0
            if random.random() > 0.3:  # 70% chance of public access
                flags |= 0x00020000  # PUBLIC_ALLOWED
            if random.random() > 0.7:  # 30% chance of sandbox
                flags |= 0x00000100  # SANDBOX
            if random.random() > 0.8:  # 20% chance of no scripts
                flags |= 0x00002000  # SKIP_SCRIPTS
            if random.random() > 0.5:  # 50% chance of voice
                flags |= 0x04000000  # ALLOW_VOICE
            
            # Random agents (0-20)
            agents = random.randint(0, 20)
            
            # Generate unique map image UUID
            map_image_id = UUID(int=random.getrandbits(128))
            
            region = Region(
                x=x,
                y=y,
                name=f"{name} {i+1}",
                access=access,
                region_flags=flags,
                water_height=20,
                agents=agents,
                map_image_id=map_image_id
            )
            
            regions.append(region)
        
        return regions

    def _build_request_packet(
        self,
        min_x: int,
        max_x: int,
        min_y: int,
        max_y: int
    ) -> bytes:
        """
        Build MapBlockRequest packet (reference implementation).
        
        This method shows how the actual packet would be constructed.
        Not used in mock implementation.
        
        Args:
            min_x: Minimum X coordinate
            max_x: Maximum X coordinate
            min_y: Minimum Y coordinate
            max_y: Maximum Y coordinate
            
        Returns:
            Binary packet data
        """
        packet = bytearray()
        
        # Packet header
        packet.append(0x00)  # Flags
        self._sequence_number += 1
        packet.extend(struct.pack('>I', self._sequence_number))
        
        # Message ID for MapBlockRequest (example)
        packet.extend(b'\xFF\xFF\x00\x02')
        
        # AgentData block
        packet.extend(NULL_UUID.bytes)  # AgentID
        packet.extend(NULL_UUID.bytes)  # SessionID
        packet.extend(struct.pack('>I', 0))  # Flags
        
        # PositionData block
        packet.extend(struct.pack('>H', min_x))
        packet.extend(struct.pack('>H', max_x))
        packet.extend(struct.pack('>H', min_y))
        packet.extend(struct.pack('>H', max_y))
        
        return bytes(packet)

    def _parse_mapblock_reply(self, data: bytes) -> List[Region]:
        """
        Parse MapBlockReply packet (reference implementation).
        
        This method shows how the actual packet would be parsed.
        Not used in mock implementation.
        
        Args:
            data: Binary packet data
            
        Returns:
            List of regions
        """
        # This would parse the actual binary response
        # For now, returns empty list
        return []


def scan_grid(
    min_x: int = 900,
    max_x: int = 1200,
    min_y: int = 900,
    max_y: int = 1200,
    step: int = 10
) -> List[Region]:
    """
    Scan a grid area for regions.
    
    Args:
        min_x: Minimum X coordinate
        max_x: Maximum X coordinate
        min_y: Minimum Y coordinate
        max_y: Maximum Y coordinate
        step: Coordinate step size for each request
        
    Returns:
        List of all discovered regions
    """
    client = MapBlockClient()
    all_regions = []
    
    total_requests = ((max_x - min_x) // step) * ((max_y - min_y) // step)
    current_request = 0
    
    logger.info(f"Starting grid scan: {total_requests} requests")
    
    for x in range(min_x, max_x, step):
        for y in range(min_y, max_y, step):
            current_request += 1
            
            try:
                regions = client.request_mapblock(
                    x, min(x + step, max_x),
                    y, min(y + step, max_y)
                )
                all_regions.extend(regions)
                
                if current_request % 10 == 0:
                    logger.info(f"Progress: {current_request}/{total_requests} requests, "
                              f"{len(all_regions)} regions discovered")
                
            except ProtocolError as e:
                logger.error(f"Request failed for ({x}, {y}): {e}")
                continue
    
    logger.info(f"Scan complete: {len(all_regions)} total regions discovered")
    return all_regions
