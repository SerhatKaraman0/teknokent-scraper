# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import os
import json
from itemadapter import ItemAdapter


class TeknokentScraperPipeline:
    def open_spider(self, spider):
        """Called when spider is opened"""
        self.items_scraped = 0
        spider.logger.info(f"Starting {spider.name} spider")

    def process_item(self, item, spider):
        """Process each scraped item"""
        adapter = ItemAdapter(item)
        
        # Clean up fields
        for field_name, field_value in adapter.items():
            if field_value:
                if isinstance(field_value, list):
                    # Join list values with semicolon
                    adapter[field_name] = '; '.join([str(v).strip() for v in field_value if str(v).strip()])
                elif isinstance(field_value, str):
                    # Clean up string values
                    adapter[field_name] = field_value.strip()
        
        # Ensure required fields have values
        if not adapter.get('company_name'):
            spider.logger.warning("Item dropped: missing company_name")
            return None
        
        # Set default values for missing fields
        if not adapter.get('company_location'):
            adapter['company_location'] = 'Ankara'
        
        if not adapter.get('company_desc'):
            adapter['company_desc'] = ''
            
        if not adapter.get('company_contact_mail'):
            adapter['company_contact_mail'] = ''
            
        if not adapter.get('company_phone'):
            adapter['company_phone'] = ''
            
        if not adapter.get('company_website'):
            adapter['company_website'] = ''
            
        if not adapter.get('company_area'):
            adapter['company_area'] = ''
        
        self.items_scraped += 1
        spider.logger.info(f"Processed item {self.items_scraped}: {adapter.get('company_name')}")
        
        return item

    def close_spider(self, spider):
        """Called when spider is closed"""
        spider.logger.info(f"Spider {spider.name} finished. Total items scraped: {self.items_scraped}")
