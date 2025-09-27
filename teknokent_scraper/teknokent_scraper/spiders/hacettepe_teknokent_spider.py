import scrapy
import json
import re
import os
from urllib.parse import urljoin, urlencode
from scrapy.loader import ItemLoader
from ..items import CompanyDetailsItem


class HacettepeSpider(scrapy.Spider):
    name = "hacettepe"

    start_urls = []

    CATEGORIES = {
        'YAZILIM-BILISIM': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/bilgisayar_ve_iletisim_teknolojileri-16',
        'ELEKTRONIK': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/elektronik-17',
        'ENERJI': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/enerji-19',
        'GIDA-HAYVANCILIK': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/gida_sanayi-20',
        'INSAAT-MUHENDISLIK': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/insaat_muhendislik_mimarlik-21',
        'KIMYA-KOZMETIK-TEMIZLIK': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/kimya_kozmetik_temizlik-22',
        'MADENCILIK': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/madencilik-23',
        'OTOMOTIV-MAKINE': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/otomotiv_makine-25',
        'SAGLIK-MEDIKAL': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/saglik_ilac_medikal-26',
        'SAVUNMA': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/savunma_sanayi_havacilik-27',
        'TELEKOMUNIKASYON': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/telekomunikasyon-28',
        'YAZILIM': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/yazilim-29',
        'DIGER': 'https://www.hacettepeteknokent.com.tr/tr/firma_rehberi/diger-30'
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.output_dir = "/Users/user/Desktop/Projects/teknokent-scraper/teknokent_scraper/teknokent_scraper/outputs/HACETTEPE"
        os.makedirs(self.output_dir, exist_ok = True)

    def start_requests(self):
        for cat_name, cat_url in self.CATEGORIES.items():
            self.logger.info(f"Starting scraping for category: {cat_name}")
            yield scrapy.Request(
                cat_url,
                callback=self.parse_category_page,
                meta={
                    'category': cat_name,
                    'category_url': cat_url,
                    'dont_cache': True
                }
            )

    def parse_category_page(self, response):
        """Parse category page directly - no AJAX needed"""
        category = response.meta['category']
        self.logger.info(f"Parsing category page for: {category}")
        
        # Extract companies directly from the page
        companies = response.css('.firma')
        self.logger.info(f"Found {len(companies)} companies in {category}")
        
        if not companies:
            self.logger.warning(f"No companies found for category: {category}")
            return
        
        # Process found companies
        for i, company in enumerate(companies):
            self.logger.info(f"Processing company {i+1}/{len(companies)} in {category}")
            yield from self.extract_company_from_html(company, category)
    
    def extract_company_from_html(self, company_selector, category):
        """Extract company data from HTML selector"""
        
        # Extract company name from .firma_adi a
        company_name_element = company_selector.css('.firma_adi a::text').get()
        
        if not company_name_element or not company_name_element.strip():
            self.logger.warning("No company name found, skipping")
            return
        
        company_name = company_name_element.strip()
        self.logger.info(f"Extracted company: {company_name}")
        
        # Get the company detail URL
        company_url = company_selector.css('.firma_adi a::attr(href)').get()
        if company_url:
            # Make sure URL is absolute
            if not company_url.startswith('http'):
                company_url = urljoin('https://www.hacettepeteknokent.com.tr', company_url)
            
            self.logger.info(f"Company detail URL for {company_name}: {company_url}")
            
            # Visit the company detail page to get email addresses and other details
            yield scrapy.Request(
                company_url,
                callback=self.parse_company_detail,
                meta={
                    'company_name': company_name,
                    'company_url': company_url,
                    'category': category
                }
            )
        else:
            # If no detail URL, create item with available data
            loader = ItemLoader(item=CompanyDetailsItem())
            loader.add_value('company_name', company_name)
            loader.add_value('company_location', 'Ankara')
            loader.add_value('company_area', category)
            loader.add_value('company_website', '')
            loader.add_value('company_contact_mail', '')
            loader.add_value('company_phone', '')
            
            yield loader.load_item()
    
    def parse_company_detail(self, response):
        """Parse individual company page to extract email addresses and complete data"""
        
        company_name = response.meta['company_name']
        company_url = response.meta['company_url']
        category = response.meta['category']
        
        self.logger.info(f"Scraping details for: {company_name}")
        
        loader = ItemLoader(item=CompanyDetailsItem(), response=response)
        
        # Add basic info
        loader.add_value('company_name', company_name)
        loader.add_value('company_location', 'Ankara')
        loader.add_value('company_area', category)
        
        # Extract phone numbers from the detail page
        phone_selectors = [
            '.contact-info .phone::text',
            '.company-phone::text',
            '[class*="phone"]::text',
            '[class*="telefon"]::text',
            'a[href^="tel:"]::text'
        ]
        
        phone_list = []
        for selector in phone_selectors:
            phones = response.css(selector).getall()
            for phone in phones:
                if phone and phone.strip():
                    phone = phone.strip()
                    # Clean up phone number and only keep if it contains digits
                    if any(char.isdigit() for char in phone):
                        phone_list.append(phone)
        
        # Also look for phone patterns in text content
        all_text = ' '.join(response.css('::text').getall())
        phone_patterns = [
            r'(?:\+90\s?)?(?:\(0?\d{3}\)|\d{3})[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            r'0\d{3}\s?\d{3}\s?\d{2}\s?\d{2}',
            r'\d{3}[\s\-]?\d{3}[\s\-]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, all_text)
            for phone in phone_matches:
                if phone and phone.strip() and phone not in phone_list:
                    phone_list.append(phone.strip())
        
        # Add phone numbers to the item
        if phone_list:
            loader.add_value('company_phone', '; '.join(phone_list))
        
        # Extract company website URLs
        websites_found = set()
        
        # Strategy 1: Look for website links in common sections
        website_selectors = [
            'a[href*="http"]:not([href*="ankarateknokent.com"]):not([href*="mailto:"]):not([href*="tel:"]):not([href*="facebook.com"]):not([href*="twitter.com"]):not([href*="instagram.com"]):not([href*="linkedin.com"]):not([href*="youtube.com"])::attr(href)',
            '.website a::attr(href)',
            '.company-website a::attr(href)',
            '.listing-website a::attr(href)',
            '[class*="website"] a::attr(href)',
            '[class*="url"] a::attr(href)',
            '.contact-info a[href^="http"]::attr(href)',
            '.company-info a[href^="http"]::attr(href)'
        ]
        
        for selector in website_selectors:
            urls = response.css(selector).getall()
            for url in urls:
                if url and self.is_valid_website_url(url):
                    websites_found.add(url)
        
        # Strategy 2: Look for website patterns in text content
        all_text = ' '.join(response.css('::text').getall())
        # Match common website patterns
        website_patterns = [
            r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?',
            r'www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?'
        ]
        
        for pattern in website_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                if not match.startswith('http'):
                    match = 'https://' + match
                if self.is_valid_website_url(match):
                    websites_found.add(match)
        
        # Strategy 3: Look in data attributes
        data_urls = response.css('[data-url], [data-website], [data-link]').re(r'data-(?:url|website|link)="([^"]*)"')
        for url in data_urls:
            if url and self.is_valid_website_url(url):
                websites_found.add(url)
        
        # Add websites to the item
        if websites_found:
            # Sort and clean websites
            clean_websites = []
            for website in sorted(websites_found):
                # Clean up the URL
                website = website.strip()
                if website and website not in clean_websites:
                    clean_websites.append(website)
            
            if clean_websites:
                loader.add_value('company_website', '; '.join(clean_websites))
                self.logger.info(f"Found {len(clean_websites)} websites for {company_name}: {', '.join(clean_websites)}")
        
        # Extract email addresses with multiple strategies
        emails_found = set()
        
        # Strategy 1: Check mailto links
        mailto_links = response.css('a[href^="mailto:"]::attr(href)').getall()
        for mailto in mailto_links:
            if mailto.startswith('mailto:'):
                email = mailto.replace('mailto:', '').strip()
                if self.is_valid_email(email):
                    emails_found.add(email)
        
        # Strategy 2: Search for email patterns in all text content
        all_text = ' '.join(response.css('::text').getall())
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, all_text)
        
        for email in email_matches:
            if self.is_valid_email(email):
                emails_found.add(email)
        
        # Strategy 3: Look for encoded emails (common anti-spam technique)
        encoded_emails = re.findall(r'[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Z|a-z]{2,}', all_text)
        for encoded in encoded_emails:
            email = encoded.replace('[at]', '@').replace('[dot]', '.').replace(' ', '')
            if self.is_valid_email(email):
                emails_found.add(email)
        
        # Strategy 4: Look in contact sections specifically
        contact_sections = response.css('.contact-info, .contact-details, .company-contact, .listing-contact')
        for section in contact_sections:
            section_text = ' '.join(section.css('::text').getall())
            section_emails = re.findall(email_pattern, section_text)
            for email in section_emails:
                if self.is_valid_email(email):
                    emails_found.add(email)
        
        # Strategy 5: Look for emails in data attributes
        data_emails = response.css('[data-email]::attr(data-email)').getall()
        for email in data_emails:
            if self.is_valid_email(email):
                emails_found.add(email)
        
        # Strategy 6: Look in script tags for JavaScript-encoded emails
        scripts = response.css('script::text').getall()
        for script in scripts:
            script_emails = re.findall(email_pattern, script)
            for email in script_emails:
                if self.is_valid_email(email):
                    emails_found.add(email)
        
        # Strategy 7: Look for obfuscated emails with unicode or HTML entities
        html_entities = response.css('*::text').re(r'[A-Za-z0-9._%+-]+&#64;[A-Za-z0-9.-]+&#46;[A-Z|a-z]{2,}')
        for entity in html_entities:
            email = entity.replace('&#64;', '@').replace('&#46;', '.')
            if self.is_valid_email(email):
                emails_found.add(email)
        
        # Add emails to the item
        if emails_found:
            loader.add_value('company_contact_mail', '; '.join(sorted(emails_found)))
            self.logger.info(f"Found {len(emails_found)} emails for {company_name}: {', '.join(emails_found)}")
        else:
            self.logger.warning(f"No emails found for {company_name}")
        
        # Extract company description if available
        desc_selectors = [
            '.listing-content p::text',
            '.company-description::text',
            '.listing-description::text',
            '.about-company::text',
            '[class*="description"] p::text'
        ]
        
        for selector in desc_selectors:
            descriptions = response.css(selector).getall()
            if descriptions:
                clean_desc = ' '.join([desc.strip() for desc in descriptions if desc.strip()])
                if clean_desc:
                    loader.add_value('company_desc', clean_desc)
                    break
        
        yield loader.load_item()
    
    def is_valid_email(self, email):
        """Validate email address"""
        if not email or '@' not in email:
            return False
        
        # Basic email validation
        if email.count('@') != 1:
            return False
        
        local, domain = email.split('@')
        
        # Check for valid domain
        if '.' not in domain or len(domain.split('.')) < 2:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            'example.com',
            'test.com',
            'domain.com',
            'email.com',
            'noemail',
            'no-reply',
            'noreply'
        ]
        
        for pattern in invalid_patterns:
            if pattern in email.lower():
                return False
        
        return True
    
    def is_valid_website_url(self, url):
        """Validate website URL"""
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        
        # Check for minimum URL structure
        if len(url) < 4:
            return False
        
        # Skip social media and other non-business websites
        skip_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 'http://www.schema.org', 
            'youtube.com', 'tiktok.com', 'pinterest.com', 'whatsapp.com',
            'telegram.org', 'discord.com', 'reddit.com', 'github.com',
            'ankarateknokent.com', 'google.com', 'maps.google.com',
            'goo.gl', 'bit.ly', 't.co', 'ow.ly', 'tinyurl.com'
        ]
        
        for domain in skip_domains:
            if domain in url.lower():
                return False
        
        # Check for valid URL patterns
        url_patterns = [
            r'^https?://',  # starts with http:// or https://
            r'^www\.',      # starts with www.
            r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'  # has domain.tld pattern
        ]
        
        has_valid_pattern = False
        for pattern in url_patterns:
            if re.search(pattern, url):
                has_valid_pattern = True
                break
        
        if not has_valid_pattern:
            return False
        
        # Ensure it has a valid domain extension
        if not re.search(r'\.[a-zA-Z]{2,}', url):
            return False
        
        return True

    def closed(self, reason):
        """Called when spider is closed"""
        self.logger.info(f"Spider closed: {reason}")
        self.logger.info(f"Output saved to: {self.output_dir}")
