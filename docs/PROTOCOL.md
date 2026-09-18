# Second Life MapBlock Protocol Documentation

**Author:** Isabela Evergarden

This document describes the Second Life MapBlock protocol used for region discovery.

---

## Overview

The MapBlock protocol is part of the Second Life viewer-server communication system. It allows clients to discover regions on the grid by requesting information about map blocks (sections of the virtual world grid).

### Key Concepts

- **Grid Coordinates**: The Second Life world is divided into a grid where each region occupies one or more grid squares
- **MapBlock**: A collection of regions within a specific coordinate range
- **Region Handle**: A unique identifier for each region based on its grid coordinates

---

## Protocol Specification

### Transport Layer

- **Protocol**: UDP (User Datagram Protocol)
- **Server**: Second Life grid server (e.g., `login.agni.lindenlab.com`)
- **Port**: Typically 13000 (varies by grid)
- **Encoding**: Binary packet format with message templates

### Packet Structure

Second Life packets follow a standard structure:

```
[Flags (1 byte)]
[Sequence Number (4 bytes)]
[Extra Header (variable)]
[Message ID (1-4 bytes)]
[Message Data (variable)]
```

---

## MapBlockRequest

Request information about regions in a specific coordinate range.

### Packet Format

```
MapBlockRequest {
    AgentData {
        AgentID:    UUID    # Agent requesting the information
        SessionID:  UUID    # Current session identifier
        Flags:      U32     # Request flags
    }
    PositionData {
        MinX:       U16     # Minimum X coordinate
        MaxX:       U16     # Maximum X coordinate
        MinY:       U16     # Minimum Y coordinate  
        MaxY:       U16     # Maximum Y coordinate
    }
}
```

### Field Descriptions

- **AgentID**: UUID of the requesting agent (can be null for anonymous requests)
- **SessionID**: Session UUID (can be null for anonymous requests)
- **Flags**: Control flags (typically 0x00000000)
- **MinX/MaxX**: X coordinate range (0-65535)
- **MinY/MaxY**: Y coordinate range (0-65535)

### Example Request

```python
request = {
    'AgentID': '00000000-0000-0000-0000-000000000000',
    'SessionID': '00000000-0000-0000-0000-000000000000',
    'Flags': 0,
    'MinX': 1000,
    'MaxX': 1010,
    'MinY': 1000,
    'MaxY': 1010
}
```

---

## MapBlockReply

Response containing information about discovered regions.

### Packet Format

```
MapBlockReply {
    AgentData {
        AgentID:    UUID    # Agent ID from request
        Flags:      U32     # Response flags
    }
    Data [Variable] {
        X:          U16     # Region X coordinate
        Y:          U16     # Region Y coordinate
        Name:       String  # Region name
        Access:     U8      # Access level
        RegionFlags: U32    # Region flags
        WaterHeight: U8     # Water height
        Agents:     U8      # Number of agents in region
        MapImageID: UUID    # Map tile texture UUID
    }
}
```

### Field Descriptions

#### Access Levels

```python
ACCESS_LEVEL = {
    0: 'Unknown',
    13: 'PG (General)',      # General audience
    21: 'Mature (Moderate)',  # Moderate content
    42: 'Adult'               # Adult content
}
```

#### Region Flags

```python
REGION_FLAGS = {
    0x00000001: 'AllowDamage',
    0x00000002: 'AllowLandmark',
    0x00000004: 'AllowSetHome',
    0x00000008: 'ResetHomeOnTeleport',
    0x00000010: 'SunFixed',
    0x00000020: 'TaxFree',
    0x00000040: 'BlockTerraform',
    0x00000080: 'BlockLandResell',
    0x00000100: 'Sandbox',
    0x00000200: 'AllowEnvOverride',
    0x00001000: 'SkipCollisions',
    0x00002000: 'SkipScripts',
    0x00004000: 'SkipPhysics',
    0x00008000: 'ExternallyVisible',
    0x00010000: 'MainlandVisible',
    0x00020000: 'PublicAllowed',
    0x00040000: 'BlockDwell',
    0x00080000: 'NoFly',
    0x00100000: 'AllowDirectTeleport',
    0x00200000: 'EstateSkipScripts',
    0x00400000: 'RestrictPushObject',
    0x00800000: 'DenyAnonymous',
    0x01000000: 'AllowParcelChanges',
    0x02000000: 'BlockFlyOver',
    0x04000000: 'AllowVoice',
    0x08000000: 'BlockParcelSearch',
    0x10000000: 'DenyAgeUnverified',
}
```

### Example Response

```python
response = {
    'AgentID': '00000000-0000-0000-0000-000000000000',
    'Flags': 0,
    'Data': [
        {
            'X': 1000,
            'Y': 1000,
            'Name': 'Sandbox Island',
            'Access': 13,  # PG/General
            'RegionFlags': 0x00000100,  # Sandbox flag
            'WaterHeight': 20,
            'Agents': 5,
            'MapImageID': '3c115e51-04f4-523c-9fa6-98aff1034730'
        }
    ]
}
```

---

## Implementation Notes

### Anonymous Requests

Region discovery can be performed without authentication by using null UUIDs:

```python
NULL_UUID = '00000000-0000-0000-0000-000000000000'
```

### Coordinate Ranges

The Second Life main grid (Agni) typically uses coordinates in the range:

- **X**: 0 to 65535 (theoretical max)
- **Y**: 0 to 65535 (theoretical max)
- **Active regions**: Typically 500-2000 range

### Rate Limiting

Grid servers may implement rate limiting:

- Limit: ~10 requests per second recommended
- Timeout: 30 seconds per request
- Retries: Maximum 3 attempts with exponential backoff

### Error Handling

Common errors:

1. **Timeout**: No response within timeout period
2. **Empty Response**: No regions found in coordinate range
3. **Connection Refused**: Server unavailable or port blocked
4. **Malformed Packet**: Invalid binary data

---

## Region Discovery Strategy

### Full Grid Scan

To discover all regions on the grid:

```python
# Scan in blocks of 10x10 coordinates
for x in range(0, 2000, 10):
    for y in range(0, 2000, 10):
        request_mapblock(x, x+10, y, y+10)
        sleep(0.1)  # Rate limiting
```

### Targeted Scan

Focus on known active areas:

```python
# Main grid active regions typically in this range
ACTIVE_RANGES = [
    (900, 1100, 900, 1100),    # Central area
    (1000, 1200, 1000, 1200),  # Popular region cluster
]

for min_x, max_x, min_y, max_y in ACTIVE_RANGES:
    request_mapblock(min_x, max_x, min_y, max_y)
```

---

## Security Considerations

### Privacy

- MapBlock requests are **public** and do not require authentication
- Region information is publicly available
- Avatar locations are not disclosed (only region agent counts)

### Data Validation

Always validate received data:

1. Check coordinate bounds (0-65535)
2. Validate UTF-8 encoding for region names
3. Verify UUID format for MapImageID
4. Sanitize region names before display

---

## Example Implementation

### Python Example

```python
import socket
import struct
from uuid import UUID

NULL_UUID = UUID('00000000-0000-0000-0000-000000000000')

def request_mapblock(server, port, min_x, max_x, min_y, max_y):
    """Request MapBlock data from Second Life grid server."""
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(30)
    
    # Build MapBlockRequest packet
    packet = bytearray()
    
    # Packet header
    packet.append(0x00)  # Flags
    packet.extend(struct.pack('>I', 1))  # Sequence number
    
    # Message ID for MapBlockRequest
    packet.extend(b'\xFF\xFF\x00\x02')
    
    # AgentData
    packet.extend(NULL_UUID.bytes)  # AgentID
    packet.extend(NULL_UUID.bytes)  # SessionID
    packet.extend(struct.pack('>I', 0))  # Flags
    
    # PositionData
    packet.extend(struct.pack('>H', min_x))
    packet.extend(struct.pack('>H', max_x))
    packet.extend(struct.pack('>H', min_y))
    packet.extend(struct.pack('>H', max_y))
    
    # Send request
    sock.sendto(bytes(packet), (server, port))
    
    # Receive response
    try:
        data, addr = sock.recvfrom(4096)
        return parse_mapblock_reply(data)
    except socket.timeout:
        return None
    finally:
        sock.close()

def parse_mapblock_reply(data):
    """Parse MapBlockReply packet."""
    # Implementation details...
    pass
```

---

## References

- [Second Life Protocol Documentation](https://wiki.secondlife.com/wiki/Protocol)
- [Message Template](https://wiki.secondlife.com/wiki/Message_Template)
- [libsecondlife Documentation](https://github.com/openmetaversefoundation/libopenmetaverse)

---

**Author:** Isabela Evergarden  
**Last Updated:** 2026-09-18  
**Version:** 1.0
