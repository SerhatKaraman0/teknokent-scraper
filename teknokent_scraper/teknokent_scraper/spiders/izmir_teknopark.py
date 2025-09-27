import scrapy
from scrapy.loader import ItemLoader
from teknokent_scraper.items import CompanyDetailsItem
import re


class IzmirTeknoparkSpider(scrapy.Spider):
    name = "izmir_teknopark"
    allowed_domains = ["teknoparkizmir.com.tr"]
    
    custom_settings = {
        'FEEDS': {
            'outputs/IZMIR_TEKNOKENT/izmir_teknopark_companies.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 4,
                'overwrite': True,
            },
            'outputs/IZMIR_TEKNOKENT/izmir_teknopark_companies.csv': {
                'format': 'csv',
                'encoding': 'utf8',
                'store_empty': False,
                'overwrite': True,
            }
        }
    }
    
    def start_requests(self):
        """Generate requests with proper headers to avoid blocking"""
        url = "https://teknoparkizmir.com.tr/tr/firmalar-liste/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.logger.info(f"Starting requests to: {url}")
        yield scrapy.Request(url=url, headers=headers, callback=self.parse)
    
    def parse(self, response):
        """Parse the companies page and extract company information"""
        self.logger.info(f"Parsing response from: {response.url}")
        
        # Find all company containers
        companies = response.css('div.firmaListe.holder')
        self.logger.info(f"Found {len(companies)} company containers")
        
        if not companies:
            self.logger.warning("No companies found! Checking page structure...")
            # Let's log the page structure for debugging
            self.logger.warning(f"Page title: {response.css('title::text').get()}")
            self.logger.warning(f"Page contains firmaListe class: {'firmaListe' in response.text}")
        
        for i, company in enumerate(companies, 1):
            # Use ItemLoader for clean data extraction
            loader = ItemLoader(item=CompanyDetailsItem(), selector=company)
            
            # Extract company name
            company_name = company.css('h3.title.line::text').get()
            if company_name:
                company_name = company_name.strip()
                loader.add_value('company_name', company_name)
                self.logger.info(f"Extracted company {i}: {company_name}")
            else:
                self.logger.warning(f"No company name found for company {i}")
                continue
            
            # Extract address
            address = company.css('div.firmaAdres::text').get()
            if address:
                address = address.strip()
                # Remove the map marker icon text
                address = re.sub(r'^\s*', '', address)
                loader.add_value('company_location', address)
            
            # Extract phone number
            phone = company.css('div.tel a::text').get()
            if phone:
                phone = phone.strip()
                loader.add_value('company_phone', phone)
            
            # Extract website
            website = company.css('div.web a::text').get()
            if website:
                website = website.strip()
                # Clean up website URL
                if website.startswith(' '):
                    website = website.strip()
                loader.add_value('company_website', website)
            
            # Extract email
            email = company.css('div.eposta a::text').get()
            if email:
                email = email.strip()
                loader.add_value('company_contact_mail', email)
            
            # Extract expertise areas (company area/specialization)
            expertise_text = company.css('div.ilanEtiketler span:last-child::text').get()
            if expertise_text:
                expertise_text = expertise_text.strip()
                loader.add_value('company_area', expertise_text)
            
            # Load and yield the item
            item = loader.load_item()
            self.logger.info(f"Processed item {i}: {item.get('company_name', 'Unknown')}")
            yield item
        
        self.logger.info(f"Finished parsing. Total companies processed: {len(companies)}")
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info(f"Spider {self.name} finished. Reason: {reason}")
        if hasattr(self, 'crawler') and hasattr(self.crawler, 'stats') and self.crawler.stats:
            stats = self.crawler.stats
            item_count = stats.get_value('item_scraped_count', 0) if stats else 0
            self.logger.info(f"Spider {self.name} finished. Total items scraped: {item_count}")
