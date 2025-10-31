import scrapy
import json
import re
from teknokent_scraper.items import CompanyDetailsItem


class ItuTeknokentSpider(scrapy.Spider):
    name = "itu"
    allowed_domains = ["ariteknokent.com.tr"]
    
    start_urls = [
        "https://www.ariteknokent.com.tr/tr/teknoloji-firmalari/teknokentli-firmalar"
    ]

    def __init__(self):
        self.company_ids = set()
        self.pages_processed = 0
        self.total_pages = 0

    def parse(self, response):
        """Parse pagination pages to collect all company IDs."""
        # Extract company row IDs from current page
        row_ids = response.css('.card::attr(data-row-id)').getall()
        
        for row_id in row_ids:
            if row_id:
                self.company_ids.add(row_id)
        
        self.logger.info(f"Found {len(row_ids)} companies on current page. Total collected: {len(self.company_ids)}")
        
        # Get pagination info on first page
        if self.total_pages == 0:
            pagination_links = response.css('.pagination li a::attr(href)').getall()
            page_numbers = []
            for link in pagination_links:
                match = re.search(r'page=(\d+)', link)
                if match:
                    page_numbers.append(int(match.group(1)))
            
            if page_numbers:
                self.total_pages = max(page_numbers)
                self.logger.info(f"Total pages found: {self.total_pages}")
        
        # Follow pagination links
        next_page_link = response.css('.pagination li a[rel="next"]::attr(href)').get()
        if next_page_link:
            yield response.follow(next_page_link, callback=self.parse)
        else:
            # No more pages, start fetching company details
            self.logger.info(f"Pagination complete. Found {len(self.company_ids)} unique companies. Starting detail fetch...")
            for company_id in self.company_ids:
                yield scrapy.Request(
                    url=f"https://www.ariteknokent.com.tr/tr/getCompanyInformations?rowID={company_id}",
                    callback=self.parse_company_details,
                    meta={'company_id': company_id}
                )

    def parse_company_details(self, response):
        """Parse individual company details from the AJAX API."""
        company_id = response.meta['company_id']
        
        try:
            data = json.loads(response.text)
            
            if not data or 'company' not in data:
                self.logger.warning(f"No company data found for ID {company_id}")
                return
            
            company = data.get('company', {})
            sector = data.get('sector', {})
            about = data.get('about', {})
            building = data.get('building', {})
            
            # Create item with company data
            item = CompanyDetailsItem()
            
            # Map API data to existing item fields
            item['company_name'] = company.get('title', '').strip()
            
            # Get Turkish description from about content
            about_content = about.get('content_tr', '') if about else ''
            # Clean HTML tags from description
            if about_content:
                about_content = re.sub(r'<[^>]+>', '', about_content)
                about_content = re.sub(r'\s+', ' ', about_content).strip()
            item['company_desc'] = about_content
            
            # Contact information
            item['company_contact_mail'] = building.get('email', '').strip() if building else ''
            item['company_phone'] = company.get('phone', '').strip() if company.get('phone') else (building.get('phone', '').strip() if building else '')
            item['company_website'] = company.get('website', '').strip()
            
            # Location information
            location_parts = []
            if company.get('city'):
                location_parts.append(company.get('city'))
            if building and building.get('address'):
                location_parts.append(building.get('address'))
            item['company_location'] = ', '.join(location_parts)
            
            # Activity area (sector)
            sector_name = sector.get('title_tr', '') if sector else ''
            if not sector_name and company.get('keywords'):
                sector_name = company.get('keywords')
            item['company_area'] = sector_name
            
            self.logger.info(f"Extracted company: {item['company_name']}")
            yield item
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response for company ID {company_id}: {e}")
            self.logger.error(f"Response content: {response.text[:200]}")
        except Exception as e:
            self.logger.error(f"Error processing company ID {company_id}: {e}")

    def closed(self, reason):
        """Called when spider is closed."""
        self.logger.info(f"Spider closed. Reason: {reason}")
        self.logger.info(f"Total unique companies found: {len(self.company_ids)}")
