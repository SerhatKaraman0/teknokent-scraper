import scrapy
import json
from teknokent_scraper.items import CompanyDetailsItem


class GaziSpider(scrapy.Spider):
    name = "gazi"
    
    start_urls = [
        "https://api.gaziteknopark.com.tr/Unit/GetUnitByPaginationAll"
    ]

    def parse(self, response):
        """Parse the API response containing all company data."""
        try:
            data = json.loads(response.text)
            companies = data.get('data', {}).get('unitUi', [])
            
            self.logger.info(f"Found {len(companies)} companies")
            
            for company_data in companies:
                company = company_data.get('unit', {})
                
                # Create item with company data
                item = CompanyDetailsItem()
                
                # Map API data to existing item fields
                item['company_name'] = company.get('name', '').strip()
                item['company_desc'] = company.get('description1', '').strip() if company.get('description1') else ''
                item['company_contact_mail'] = company.get('eposta', '').strip() if company.get('eposta') and company.get('eposta') != 'Yok' else ''
                item['company_phone'] = company.get('phone', '').strip() if company.get('phone') and company.get('phone') != 'Yok' else ''
                item['company_website'] = company.get('description', '').strip() if company.get('description') else ''
                item['company_location'] = company.get('adress', '').strip() if company.get('adress') else ''
                
                # Map activity area (you might need to create a mapping for this)
                activity_area = company.get('activityArea', '')
                item['company_area'] = str(activity_area) if activity_area else ''
                
                yield item
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Response content: {response.text[:500]}")
        except Exception as e:
            self.logger.error(f"Error processing API response: {e}")
            self.logger.error(f"Response type: {type(data)}")
            if 'data' in locals():
                self.logger.error(f"Data keys: {data.keys() if isinstance(data, dict) else 'not a dict'}")
                if isinstance(data, dict) and 'data' in data:
                    self.logger.error(f"Data.data keys: {data['data'].keys() if isinstance(data['data'], dict) else 'not a dict'}")
                    if 'unitUi' in data['data']:
                        self.logger.error(f"UnitUi length: {len(data['data']['unitUi'])}")
                        if data['data']['unitUi']:
                            self.logger.error(f"First unitUi item type: {type(data['data']['unitUi'][0])}")
                            self.logger.error(f"First unitUi item keys: {data['data']['unitUi'][0].keys() if isinstance(data['data']['unitUi'][0], dict) else 'not a dict'}")
            
    async def start(self):
        """Override to set proper headers for API request."""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                callback=self.parse
            )
