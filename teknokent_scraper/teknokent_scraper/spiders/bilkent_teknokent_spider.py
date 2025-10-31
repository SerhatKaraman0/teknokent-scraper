import scrapy
from urllib.parse import urljoin
from scrapy.loader import ItemLoader
from teknokent_scraper.items import CompanyDetailsItem


class BilkentSpider(scrapy.Spider):
    name = "bilkent"
    allowed_domains = ['cyberpark.com.tr']
    
    # Generate URLs for all 18 pages
    start_urls = [f'https://www.cyberpark.com.tr/firma-arsiv/{page}' for page in range(1, 19)]
    
    custom_settings = {
        'FEEDS': {
            'outputs/BILKENT_CYBERPARK/companies_bilkent.json': {
                'format': 'json',
                'overwrite': True,
            },
            'outputs/BILKENT_CYBERPARK/companies_bilkent.csv': {
                'format': 'csv',
                'overwrite': True,
            },
        },
        'USER_AGENT': 'teknokent-scraper/1.0',
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }

    def parse(self, response):
        """Parse company listing page"""
        self.logger.info(f"Parsing page: {response.url}")
        
        # Extract all company elements
        company_elements = response.css('div.e-bulletin-image-box')
        
        for element in company_elements:
            # Extract company name from the title
            company_name = element.css('h3.title::text').get()
            if company_name:
                company_name = company_name.strip()
                
            # Extract company website from the href attribute  
            company_website = element.css('a::attr(href)').get()
            if company_website and company_website != '#':
                if not company_website.startswith('http'):
                    company_website = 'http://' + company_website
            else:
                company_website = ''
                
            # Extract company description
            description_element = element.css('div[style*="padding:10px"] p::text').get()
            company_desc = description_element.strip() if description_element else ''
            
            # Extract image URL
            image_url = element.css('img::attr(src)').get()
            if image_url:
                image_url = urljoin(response.url, image_url)
            
            # Create the company item
            if company_name:
                loader = ItemLoader(item=CompanyDetailsItem())
                loader.add_value('company_name', company_name)
                loader.add_value('company_area', 'TEKNOLOJİ')  # Default area for Cyberpark
                loader.add_value('company_location', 'Ankara')
                loader.add_value('company_website', company_website)
                loader.add_value('company_desc', company_desc)
                loader.add_value('company_contact_mail', '')  # No email on listing page
                loader.add_value('company_phone', '')  # No phone on listing page
                
                item = loader.load_item()
                
                self.logger.info(f"Found company: {company_name}")
                yield item
                
        # Log summary for this page
        total_companies = len(company_elements)
        self.logger.info(f"Page {response.url} processed: {total_companies} companies found")
