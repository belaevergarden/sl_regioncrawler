# Second Life Region Crawler

**Author:** Isabela Evergarden

Python crawler and analysis tool for discovering, filtering, and evaluating Second Life regions and parcels for configurable rez, scripting, access, land-impact, Auto Return, and activity requirements.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Motivation](#motivation)
- [Current Capabilities](#current-capabilities)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Output](#output)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Technical Documentation](#technical-documentation)
- [License](#license)

---

## Project Overview

`sl_regioncrawler` is a Python-based tool designed to discover and analyze Second Life regions using the Second Life grid network protocol. It helps residents find suitable locations for rezzing objects, running scripts, and other activities without requiring land ownership.

The crawler connects to Second Life grid servers, requests region information via the MapBlock protocol, filters regions based on user-defined criteria, and generates comprehensive reports.

---

## Motivation

Finding suitable free or public locations in Second Life where residents can rez and leave objects (such as spacecraft, vehicles, or temporary builds) without purchasing or renting land is challenging. 

This project addresses that challenge by:

1. **Automating region discovery** across the entire Second Life grid
2. **Filtering regions** based on access permissions, rez rights, and other criteria
3. **Analyzing region characteristics** to identify suitable locations
4. **Generating reports** ranking regions by suitability

---

## Current Capabilities

### ✅ Implemented

- **Region Discovery**: MapBlock protocol implementation for discovering regions on the Second Life grid
- **Region Metadata Collection**: Gathering region information including name, location, access level, and maturity rating
- **Region Filtering**: Configurable filtering based on:
  - Public access vs. private regions
  - Maturity rating (General, Moderate, Adult)
  - Region name patterns
- **SQLite Persistence**: Local database storage for discovered regions
- **Report Generation**: Markdown and JSON reports of top regions
- **CLI Interface**: Command-line tool for running crawls with configuration
- **Test Suite**: Unit and integration tests with fixtures

### 🔍 Under Investigation

- **Automated Parcel Discovery**: Detecting individual parcels within regions
- **Rez Permission Verification**: Testing actual object rezzing capabilities
- **Script Permission Verification**: Detecting script execution restrictions
- **Auto Return Detection**: Identifying regions with automatic object return policies
- **Activity/Traffic Analysis**: Measuring region activity and user traffic
- **Land Impact Limits**: Detecting maximum allowed land impact per parcel

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:

```bash
git clone https://github.com/belaevergarden/sl_regioncrawler.git
cd sl_regioncrawler
```

2. Create and activate a virtual environment:

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

### Basic Crawl

Run the crawler with default configuration:

```bash
python -m src
```

### Custom Configuration

Run with a specific configuration file:

```bash
python -m src --config my_config.yaml
```

### Command-Line Options

```bash
python -m src --help
```

Available options:
- `--config PATH`: Path to configuration file (default: `config.yaml`)
- `--output DIR`: Output directory for reports (default: `output/`)
- `--database PATH`: SQLite database path (default: `regions.db`)
- `--limit N`: Limit number of regions to discover (default: unlimited)
- `--verbose`: Enable verbose logging

### Example Commands

```bash
# Discover first 100 regions
python -m src --limit 100

# Use custom configuration
python -m src --config configs/public_only.yaml

# Enable verbose logging
python -m src --verbose
```

---

## Configuration

Create a `config.yaml` file to customize crawler behavior:

```yaml
# Search criteria
search:
  # Access filters
  public_only: true           # Only discover public-access regions
  
  # Maturity rating filters
  maturity:
    general: true             # Include General-rated regions
    moderate: true            # Include Moderate-rated regions
    adult: false              # Exclude Adult-rated regions
  
  # Region name filters
  exclude_patterns:
    - "^Private"              # Exclude regions starting with "Private"
    - "Staff Only"            # Exclude regions containing "Staff Only"

# Discovery settings
discovery:
  grid_server: "login.agni.lindenlab.com"  # Second Life main grid
  port: 13000                                # MapBlock protocol port
  timeout: 30                                # Request timeout in seconds
  max_retries: 3                             # Maximum connection retries

# Output settings
output:
  format: "markdown"          # Report format: markdown, json, or both
  top_regions: 100            # Number of top regions to include in report
  include_coordinates: true   # Include grid coordinates in reports
  include_metadata: true      # Include full region metadata

# Database settings
database:
  path: "regions.db"          # SQLite database path
  cache_duration: 86400       # Cache validity in seconds (24 hours)
```

### Example Configurations

**Public regions only:**
```yaml
search:
  public_only: true
  maturity:
    general: true
    moderate: true
    adult: false
```

**All-ages safe regions:**
```yaml
search:
  maturity:
    general: true
    moderate: false
    adult: false
```

---

## Output

### Report Files

The crawler generates reports in the `output/` directory:

- **`top_100_regions.md`**: Markdown report of top regions ranked by suitability
- **`regions_report.json`**: JSON export of discovered regions
- **`regions.db`**: SQLite database with full region metadata

### Example Output Structure

```
output/
├── top_100_regions.md          # Main report
├── regions_report.json         # JSON export
└── example_top_100_regions.md  # Committed example output

reports/
├── pytest-results.xml          # Test results (generated during testing)
└── coverage.json               # Code coverage report
```

### Sample Report

```markdown
# Top 100 Second Life Regions

**Generated:** 2026-09-18 15:11:21
**Total Regions Discovered:** 1,247
**Regions Matching Criteria:** 342

## Ranking Criteria
- Public access
- General/Moderate maturity rating
- Active regions only

## Top Regions

### 1. Sandbox Island
- **Location:** (1000, 1000)
- **Access:** Public
- **Maturity:** General
- **Description:** Public sandbox with full rez permissions

### 2. Builder's Haven
- **Location:** (1050, 1020)
- **Access:** Public
- **Maturity:** Moderate
- **Description:** Community building area
```

---

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=sl_regioncrawler --cov-report=html
```

### Generate JUnit XML Report

```bash
pytest --junitxml=reports/pytest-results.xml
```

### Run Specific Test Module

```bash
pytest tests/test_protocol.py
pytest tests/test_filtering.py
pytest tests/test_persistence.py
```

### Test Structure

```
tests/
├── __init__.py
├── test_protocol.py        # MapBlock protocol tests
├── test_models.py          # Data model tests
├── test_filtering.py       # Region filtering tests
├── test_persistence.py     # Database tests
├── test_cli.py             # CLI interface tests
└── fixtures/
    ├── mapblock_reply.bin  # Sample MapBlock responses
    └── regions.json        # Test region data
```

---

## Project Structure

```
sl_regioncrawler/
├── README.md                    # This file
├── LICENSE                      # Project license
├── requirements.txt             # Python dependencies
├── config.yaml.example          # Configuration template
├── .gitignore                   # Git exclusions
│
├── src/                         # Source code
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # CLI entry point
│   ├── models.py                # Data models
│   ├── protocol.py              # MapBlock protocol implementation
│   ├── crawler.py               # Main crawler logic
│   ├── filtering.py             # Region filtering
│   ├── persistence.py           # SQLite database interface
│   └── reports.py               # Report generation
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_filtering.py
│   └── test_persistence.py
│
├── docs/                        # Documentation
│   └── PROTOCOL.md              # Protocol specification
│
├── output/                      # Generated reports (not committed)
│   └── example_top_25_regions.md
│
└── reports/                     # Test reports (not committed)
    └── pytest-results.xml
```

---

## Technical Documentation

### Second Life MapBlock Protocol

The crawler uses the Second Life MapBlock protocol to discover regions:

1. **Connection**: UDP connection to grid server
2. **Request**: MapBlockRequest packet with grid coordinates
3. **Response**: MapBlockReply packet containing region information
4. **Parsing**: Extract region metadata from binary response

See `docs/PROTOCOL.md` for detailed protocol documentation.

### Architecture

```
┌─────────────┐
│     CLI     │  Command-line interface
└──────┬──────┘
       │
┌──────▼──────┐
│   Crawler   │  Main orchestration
└──────┬──────┘
       │
       ├─────► Protocol Client  (MapBlock communication)
       │
       ├─────► Filter Engine    (Region filtering)
       │
       ├─────► Persistence      (SQLite storage)
       │
       └─────► Report Generator (Output formatting)
```

---

## License

MIT License

Copyright (c) 2026 Isabela Evergarden

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

**Author:** Isabela Evergarden  
**Repository:** https://github.com/belaevergarden/sl_regioncrawler  
**Version:** 0.1.0
