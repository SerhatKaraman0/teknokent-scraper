import scrapy
import json
import re
import os
from urllib.parse import urljoin, urlencode
from scrapy.loader import ItemLoader
from ..items import CompanyDetailsItem

class AnkaraTeknokentComprehensiveSpider(scrapy.Spider):
    name = "ankara_teknokent_comprehensive"
    
    # Category mappings with their URLs
    CATEGORIES = {
        'YAZILIM-BILISIM': 'https://firmarehberi.ankarateknokent.com/?type=place&category=yazilim-bilisim&sort=latest',
        'MUHENDISLIK_BIYOTEKNOLOJI': 'https://firmarehberi.ankarateknokent.com/?type=place&category=muhendislik-biyoteknoloji&sort=latest',
        'ZIRAAT_VETERINER': 'https://firmarehberi.ankarateknokent.com/?type=place&category=ziraat-veteriner&sort=latest',
        'SAVUNMA': 'https://firmarehberi.ankarateknokent.com/?type=place&category=savunma&sort=latest',
        'TIP_ECZACILIK': 'https://firmarehberi.ankarateknokent.com/?type=place&category=tip-ve-eczacilik&sort=latest'
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create output directory if it doesn't exist
        self.output_dir = "/Users/user/Desktop/Projects/teknokent-scraper/teknokent_scraper/teknokent_scraper/outputs/ANKARA_UNI"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def start_requests(self):
        """Start requests for each category"""
        for category_name, category_url in self.CATEGORIES.items():
            self.logger.info(f"Starting scraping for category: {category_name}")
            yield scrapy.Request(
                category_url,
                callback=self.parse_category_page,
                meta={
                    'category': category_name,
                    'category_url': category_url,
                    'dont_cache': True
                }
            )
    
    def parse_category_page(self, response):
        """Parse category page and extract nonce for AJAX requests"""
        category = response.meta['category']
        self.logger.info(f"Parsing category page for: {category}")
        
        nonce = None
        
        # Extract nonce from page scripts
        try:
            scripts = response.css('script::text').getall()
        except:
            response_text = response.body.decode('utf-8', errors='ignore')
            script_matches = re.findall(r'<script[^>]*>(.*?)</script>', response_text, re.DOTALL | re.IGNORECASE)
            scripts = script_matches
        
        for script in scripts:
            if 'ajax_nonce' in script or 'security' in script:
                nonce_match = re.search(r'"(?:ajax_nonce|security)":"([^"]+)"', script)
                if nonce_match:
                    nonce = nonce_match.group(1)
                    break
        
        if nonce:
            self.logger.info(f"Found nonce for {category}: {nonce}")
            
            # Extract category slug from URL
            category_slug = None
            if 'category=' in response.url:
                category_slug = response.url.split('category=')[1].split('&')[0]
            
            # Make AJAX request to get listings
            ajax_url = "https://firmarehberi.ankarateknokent.com/"
            
            params = {
                'mylisting-ajax': '1',
                'action': 'get_listings',
                'security': nonce,
                'form_data[page]': '0',
                'form_data[preserve_page]': 'false',
                'form_data[search_keywords]': '',
                'form_data[category]': category_slug if category_slug else '',
                'form_data[sort]': 'latest',
                'listing_type': 'place',
                'listing_wrap': 'col-md-12 grid-item'
            }
            
            url_with_params = f"{ajax_url}?{urlencode(params)}"
            
            yield scrapy.Request(
                url_with_params,
                callback=self.parse_ajax_listings,
                headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Referer': response.url
                },
                meta={
                    'category': category,
                    'nonce': nonce,
                    'page': 0,
                    'category_slug': category_slug
                }
            )
        else:
            self.logger.warning(f"Could not find nonce for category: {category}")
    
    def parse_ajax_listings(self, response):
        """Parse AJAX response containing listings"""
        category = response.meta['category']
        
        self.logger.info(f"AJAX Response for {category} - Status: {response.status}")
        
        try:
            response_text = response.text
        except AttributeError:
            response_text = response.body.decode('utf-8', errors='ignore')
        
        # Try to parse as JSON first
        try:
            data = json.loads(response_text)
            self.logger.info(f"Successfully parsed JSON response for {category}")
            
            # Handle different JSON response structures
            if isinstance(data, dict):
                if 'success' in data and data.get('success'):
                    if 'data' in data:
                        if isinstance(data['data'], dict) and 'html' in data['data']:
                            html_content = data['data']['html']
                            yield from self.parse_html_listings(html_content, category)
                        elif isinstance(data['data'], list):
                            for listing in data['data']:
                                yield from self.parse_listing_json(listing, category)
                elif 'html' in data:
                    yield from self.parse_html_listings(data['html'], category)
                elif 'listings' in data:
                    for listing in data['listings']:
                        yield from self.parse_listing_json(listing, category)
            elif isinstance(data, list):
                for listing in data:
                    yield from self.parse_listing_json(listing, category)
                    
        except json.JSONDecodeError:
            # Not JSON, try to parse as HTML
            if response.text.strip():
                self.logger.info(f"Response for {category} is not JSON, parsing as HTML")
                yield from self.parse_html_listings(response.text, category)
            else:
                self.logger.warning(f"Empty AJAX response for category: {category}")
    
    def parse_html_listings(self, html_content, category):
        """Parse HTML content containing listings"""
        from scrapy import Selector
        
        selector = Selector(text=html_content)
        self.logger.info(f"Parsing HTML content for {category}, length: {len(html_content)}")
        
        companies = selector.css('.col-md-12.grid-item')
        self.logger.info(f"Found {len(companies)} companies in {category}")
        
        if not companies:
            self.logger.warning(f"No companies found for category: {category}")
            return
        
        # Process found companies
        for i, company in enumerate(companies):
            self.logger.info(f"Processing company {i+1}/{len(companies)} in {category}")
            yield from self.extract_company_from_html(company, category)
    
    def parse_listing_json(self, listing_data, category):
        """Parse individual listing from JSON data"""
        
        if not isinstance(listing_data, dict):
            return
        
        loader = ItemLoader(item=CompanyDetailsItem())
        
        # Extract company name
        name_fields = ['title', 'name', 'company_name', 'post_title', 'listing_title']
        for field in name_fields:
            if field in listing_data and listing_data[field]:
                loader.add_value('company_name', listing_data[field])
                break
        
        # Extract description
        desc_fields = ['description', 'excerpt', 'content', 'post_content', 'post_excerpt']
        for field in desc_fields:
            if field in listing_data and listing_data[field]:
                desc = re.sub(r'<[^>]+>', '', str(listing_data[field]))
                loader.add_value('company_desc', desc.strip())
                break
        
        # Extract contact email
        email_fields = ['email', 'contact_email', 'company_email']
        for field in email_fields:
            if field in listing_data and listing_data[field]:
                loader.add_value('company_contact_mail', listing_data[field])
                break
        
        # Extract phone numbers
        phone_fields = ['phone', 'contact_phone', 'company_phone', 'telephone']
        for field in phone_fields:
            if field in listing_data and listing_data[field]:
                loader.add_value('company_phone', listing_data[field])
                break
        
        # Extract location
        location_fields = ['location', 'address', 'company_location', 'geolocation_address']
        for field in location_fields:
            if field in listing_data and listing_data[field]:
                if isinstance(listing_data[field], dict):
                    addr = listing_data[field].get('address', '')
                    if addr:
                        loader.add_value('company_location', addr)
                else:
                    loader.add_value('company_location', listing_data[field])
                break
        
        # Set category
        loader.add_value('company_area', category)
        
        item = loader.load_item()
        if item.get('company_name'):
            yield item
    
    def extract_company_from_html(self, company_selector, category):
        """Extract company data from HTML selector"""
        
        # Extract company name
        company_name = company_selector.css('h4.listing-preview-title::text, h4.case27-primary-text::text').get()
        
        if not company_name or not company_name.strip():
            self.logger.warning("No company name found, skipping")
            return
        
        company_name = company_name.strip()
        self.logger.info(f"Extracted company: {company_name}")
        
        # Extract phone numbers from contact list
        phone_numbers = company_selector.css('.lf-contact li::text').getall()
        phone_list = []
        
        for phone in phone_numbers:
            if phone and phone.strip():
                phone = phone.strip()
                # Clean up phone number and only keep if it contains digits
                if any(char.isdigit() for char in phone):
                    phone_list.append(phone)
        
        # Get the company detail URL for email scraping
        company_url = company_selector.css('a[href*="/firma/"]::attr(href)').get()
        if company_url:
            company_url = urljoin('https://firmarehberi.ankarateknokent.com/', company_url)
            self.logger.info(f"Company detail URL for {company_name}: {company_url}")
            
            # Visit the company detail page to get email addresses
            yield scrapy.Request(
                company_url,
                callback=self.parse_company_detail,
                meta={
                    'company_name': company_name,
                    'company_phone': phone_list,
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
            
            if phone_list:
                loader.add_value('company_phone', '; '.join(phone_list))
            
            # No website available without detail page
            loader.add_value('company_website', '')
            
            yield loader.load_item()
    
    def parse_company_detail(self, response):
        """Parse individual company page to extract email addresses and complete data"""
        
        company_name = response.meta['company_name']
        company_phone = response.meta['company_phone']
        company_url = response.meta['company_url']
        category = response.meta['category']
        
        self.logger.info(f"Scraping details for: {company_name}")
        
        loader = ItemLoader(item=CompanyDetailsItem(), response=response)
        
        # Add basic info
        loader.add_value('company_name', company_name)
        loader.add_value('company_location', 'Ankara')
        loader.add_value('company_area', category)
        
        # Add phone numbers
        if company_phone:
            loader.add_value('company_phone', '; '.join(company_phone))
        
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
