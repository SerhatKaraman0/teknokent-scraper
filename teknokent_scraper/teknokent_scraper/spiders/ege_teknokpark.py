import scrapy
from teknokent_scraper.items import CompanyDetailsItem
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose


class EgeTeknoKentSpider(scrapy.Spider):
    name = "ege_teknopark"
    allowed_domains = ["egeteknopark.com.tr"]
    start_urls = [
        "https://egeteknopark.com.tr/kuluckalik-firmalar/",  # Incubator companies (34)
        "https://egeteknopark.com.tr/ege-teknopark/"         # Main company list (120)
    ]
    
    custom_settings = {
        'FEEDS': {
            'outputs/EGE_TEKNOKENT/ege_teknopark_companies.json': {
                'format': 'json',
                'overwrite': True,
                'indent': 2,
            },
            'outputs/EGE_TEKNOKENT/ege_teknopark_companies.csv': {
                'format': 'csv',
                'overwrite': True,
            }
        },
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        },
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }

    def start_requests(self):
        """Override start_requests to add custom headers for both URLs"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="91", " Not;A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url, 
                headers=headers, 
                callback=self.parse,
                meta={'dont_cache': True}
            )
    
    def parse(self, response):
        """Parse company tables on both Ege Teknopark pages"""
        
        # Determine which page we're on and which table to target
        if 'kuluckalik-firmalar' in response.url:
            # Incubator companies page - table with id="tablepress-1"
            company_table = response.css('table#tablepress-1')
            page_type = "Kuluçkalık (Incubator)"
        elif 'ege-teknopark' in response.url:
            # Main companies page - table with id="tablepress-2" 
            company_table = response.css('table#tablepress-2')
            page_type = "Ana Firma Listesi (Main)"
        else:
            self.logger.warning(f"Unknown page URL: {response.url}")
            return
        
        if not company_table:
            self.logger.warning(f"No company table found on {response.url}")
            return
            
        # Extract all company rows from tbody (skip header row)
        company_rows = company_table.css('tbody tr')
        
        self.logger.info(f"Found {len(company_rows)} company rows on {page_type} page")
        
        for row in company_rows:
            # Extract company name from the first column
            company_name_cell = row.css('td.column-1')
            
            if company_name_cell:
                loader = ItemLoader(item=CompanyDetailsItem(), selector=company_name_cell)
                
                # Extract company name and clean it
                loader.add_css('company_name', '::text')
                loader.default_item_class = CompanyDetailsItem
                loader.default_output_processor = TakeFirst()
                loader.default_input_processor = MapCompose(str.strip)
                
                # No website information is available in these tables
                # Set website to None/empty
                loader.add_value('company_website', '')
                
                item = loader.load_item()
                
                # Log the extracted company
                self.logger.info(f"Extracted company from {page_type}: {item.get('company_name', 'N/A')}")
                
                yield item
        
        # Log completion for this page
        self.logger.info(f"Finished parsing {page_type} companies from {response.url}")
