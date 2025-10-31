import scrapy
from scrapy.loader import ItemLoader
from teknokent_scraper.items import CompanyDetailsItem


class OdtuSpider(scrapy.Spider):
    name = "odtu"
    start_urls = ["https://odtuteknokent.com.tr/tr/firmalar/tum-firmalar.php"]

    custom_settings = {
        'FEEDS': {
            'outputs/ODTU/odtu_companies.json': {
                'format': 'json',
                'overwrite': True,
                'indent': 2,
                'ensure_ascii': False,
            },
            'outputs/ODTU/odtu_companies.csv': {
                'format': 'csv',
                'overwrite': True,
            }
        }
    }

    def parse(self, response):
        self.logger.info(f"Parsing ODTU companies from: {response.url}")
        
        # Extract all table rows containing company data
        company_rows = response.css('table.table tbody tr')
        self.logger.info(f"Found {len(company_rows)} company rows")
        
        for row in company_rows:
            # Extract company name from first td
            company_name_td = row.css('td:first-child::text').get()
            # Extract website from second td anchor
            website_link = row.css('td:nth-child(2) a::attr(href)').get()
            website_text = row.css('td:nth-child(2) a::text').get()
            
            if company_name_td and company_name_td.strip():
                loader = ItemLoader(item=CompanyDetailsItem())
                
                # Clean up the company name
                company_name = company_name_td.strip()
                loader.add_value('company_name', company_name)
                
                # Handle website URL
                if website_link and website_link.strip() and website_link != 'http://-':
                    website_url = website_link.strip()
                    # Ensure http:// or https:// prefix
                    if not website_url.startswith(('http://', 'https://')):
                        website_url = 'http://' + website_url
                    loader.add_value('company_website', website_url)
                else:
                    loader.add_value('company_website', '')
                
                # Set default values for missing fields
                loader.add_value('company_location', 'Ankara')
                loader.add_value('company_area', 'ODTU TEKNOKENT')
                loader.add_value('company_contact_mail', '')
                loader.add_value('company_phone', '')
                loader.add_value('company_desc', '')
                
                # Yield the item
                item = loader.load_item()
                self.logger.debug(f"Scraped company: {company_name}")
                yield item

    def closed(self, reason):
        self.logger.info(f'Spider closed: {reason}')
        if hasattr(self, 'crawler') and self.crawler and hasattr(self.crawler, 'stats'):
            stats = self.crawler.stats
            item_count = stats.get_value('item_scraped_count', 0) if stats else 0
            self.logger.info(f'Total companies scraped: {item_count}')
