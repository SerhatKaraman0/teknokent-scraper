# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field


class CompanyDetailsItem(scrapy.Item):
    company_name         = Field()
    company_desc         = Field()
    company_contact_mail = Field()
    company_phone        = Field()
    company_website      = Field()
    company_location     = Field()
    company_area         = Field()

    
