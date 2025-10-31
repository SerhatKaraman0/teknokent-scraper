# Teknokent Scraper

A comprehensive web scraping project for extracting company information from various Turkish technology parks (teknoparks/teknokents).

## Overview This project uses Scrapy to gather detailed company data from multiple teknokent websites across Turkey.

## Supported Teknokents

| Teknokent | Spider Name | Status | Companies |
|-----------|-------------|---------|----------|
| Ankara University | `ankarauni_teknokent_spider` | Active | ~234 |
| Bilkent Cyberpark | `bilkent_teknokent_spider` | Active | ~345 |
| Ege Teknokent | `ege_teknokent_spider` | Active | ~154 |
| Gazi Teknokent | `gazi_teknokent_spider` | Active | ~135 |
| Hacettepe Teknokent | `hacettepe_teknokent_spider` | Active | ~319 |
| ITU ARI Teknokent | `itu_teknokent_spider` | Active | ~327 |
| Izmir Teknokent | `izmir_teknokent_spider` | Active | ~147 |
| ODTU Teknokent | `odtu_teknokent_spider` | Active | ~420 |

## Prerequisites

- Python 3.8+
- uv (Python package manager)
- Make (for using Makefile commands)
- jq (for JSON processing and statistics)

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/SerhatKaraman0/teknokent-scraper.git
cd teknokent-scraper
```

2. **Install dependencies using uv:**
```bash
uv sync
```

## Quick Start

### Prerequisites

- Python 3.8+
- uv (Python package manager)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd teknokent-scraper

# Install dependencies using uv
uv install
```

## Usage

### Individual Spiders

**JSON Output (Default):**
```bash
# Run specific teknokent scrapers
make ankara     # Ankara University Teknokent
make bilkent    # Bilkent Cyberpark
make ege        # Ege Teknokent
make gazi       # Gazi Teknokent
make hacettepe  # Hacettepe Teknokent
make itu        # ITU ARI Teknokent
make izmir      # Izmir Teknokent
make odtu       # ODTU Teknokent
```

**CSV Output:**
```bash
# Run with CSV output format
make ankara-csv
make bilkent-csv
make ege-csv
make gazi-csv
make hacettepe-csv
make itu-csv
make izmir-csv
make odtu-csv
```

### Batch Operations

```bash
# Run all spiders
make all            # JSON output for all
make all-csv        # CSV output for all
make all-formats    # Both JSON and CSV for all
```

### Utility Commands

```bash
# View scraping statistics
make stats

# Clean all output files
make clean

# Create output directories
make create-dirs

# Show all available commands
make help
```

## Output Structure

### Manual Scrapy Commands

If you prefer to run Scrapy directly:

```bash
cd teknokent_scraper

# Run individual spider
uv run scrapy crawl gazi -o companies.json

# Run with specific output location
uv run scrapy crawl itu -o /path/to/output/companies_itu.json
```

## Output Structure

All scraped data is organized in the following directory structure:

```
teknokent_scraper/teknokent_scraper/outputs/
├── ANKARA_UNI/
│   ├── companies_ankara.json
│   └── companies_ankara.csv
├── BILKENT_CYBERPARK/
│   ├── companies_bilkent.json
│   └── companies_bilkent.csv
├── EGE_TEKNOKENT/
│   ├── companies_ege.json
│   └── companies_ege.csv
├── GAZI_TEKNOKENT/
│   ├── companies_gazi.json
│   └── companies_gazi.csv
├── HACETTEPE/
│   ├── companies_hacettepe.json
│   └── companies_hacettepe.csv
├── ITU_TEKNOKENT/
│   ├── companies_itu.json
│   └── companies_itu.csv
├── IZMIR_TEKNOKENT/
│   ├── companies_izmir.json
│   └── companies_izmir.csv
└── ODTU/
    ├── companies_odtu.json
    └── companies_odtu.csv
```

## Data Schema

Each company record contains the following fields:

```json
{
  "company_name": "Company Name",
  "company_desc": "Detailed company description",
  "company_contact_mail": "contact@company.com",
  "company_phone": "+90 XXX XXX XXXX",
  "company_website": "https://www.company.com",
  "company_location": "City, Address",
  "company_area": "Technology Sector/Area"
}
```

## Advanced Usage

### Custom Output Locations

```bash
# Save to specific location
cd teknokent_scraper
uv run scrapy crawl gazi -o /custom/path/gazi_companies.json

# Save as different formats
uv run scrapy crawl itu -o companies.csv -t csv
uv run scrapy crawl bilkent -o companies.jsonlines -t jsonlines
```

### Spider-Specific Settings

Each spider is optimized for its target website:
- **gazi**: Uses API endpoint for efficient data extraction
- **itu**: Hybrid approach with pagination + API calls
- **bilkent**: Direct HTML parsing with modal handling
- **ankara**: Comprehensive pagination scraping
- **hacettepe**: Company profile URL extraction
- **ege**: Simple list-based extraction
- **izmir**: Table-based data parsing
- **odtu**: Multi-page navigation

### Filtering and Customization

You can modify the spiders to filter specific companies or add custom fields by editing the spider files in:
```
teknokent_scraper/teknokent_scraper/spiders/
```

## 📊 Statistics and Monitoring

Check scraping results with the built-in statistics:

```bash
make stats
```

Example output:
```
Spider Output Statistics:
=====================================

GAZI_TEKNOKENT - companies_gazi.json: 135 companies (96K)
ITU_TEKNOKENT - companies_itu.json: 327 companies (196K)
BILKENT_CYBERPARK - companies_bilkent.json: 345 companies (84K)
...
```

## 🔧 Configuration

### Scrapy Settings

Main settings can be found in:
```
teknokent_scraper/teknokent_scraper/settings.py
```

Key configurations:
- **ROBOTSTXT_OBEY**: Respects robots.txt
- **DOWNLOAD_DELAY**: Polite crawling delay
- **USER_AGENT**: Identifies the scraper
- **FEEDS**: Output format configuration

### Spider-Specific Settings

Each spider has customizable parameters:
- Request delays
- Retry attempts  
- Custom headers
- Output field mappings

## Best Practices

### Ethical Scraping
- Respects robots.txt files
- Implements polite delays between requests
- Uses appropriate User-Agent strings
- Avoids overwhelming target servers

### Data Quality
- Comprehensive error handling
- Data validation and cleaning
- Duplicate detection and removal
- Consistent data formatting

### Performance
- Concurrent request processing
- Efficient memory usage
- Progress monitoring and logging
- Graceful failure recovery

## 🔍 Troubleshooting

### Common Issues

**1. Spider not found:**
```bash
# Make sure you're in the correct directory
cd teknokent_scraper
```

**2. Network timeouts:**
```bash
# Increase timeout in spider settings
DOWNLOAD_TIMEOUT = 30
```

**3. Rate limiting:**
```bash
# Increase delay between requests
DOWNLOAD_DELAY = 2
```

### Debugging

Enable debug logging:
```bash
uv run scrapy crawl gazi -L DEBUG
```

Check specific spider logs:
```bash
uv run scrapy crawl gazi -L INFO -o output.json
```

### Adding New Teknokents

To add a new teknokent spider:

1. **Create spider file:**
```bash
cd teknokent_scraper/teknokent_scraper/spiders/
# Create new_teknokent_spider.py
```

2. **Update Makefile:**
Add commands for the new spider in the Makefile

3. **Create output directory:**
```bash
mkdir -p outputs/NEW_TEKNOKENT
```

4. **Test the spider:**
```bash
make new-teknokent
```
