from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote
import random 
import requests

class FirefoxSearchScraper:
    def __init__(self) -> None:
        
        self.options = Options()
        
        # Firefox stealth options
        self.options.add_argument("--width=1920")
        self.options.add_argument("--height=1080")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        
        # User agent for Firefox
        self.options.set_preference("general.useragent.override", 
                                  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0")
        
        # Disable images and CSS for faster loading
        self.options.set_preference("permissions.default.image", 2)
        self.options.set_preference("permissions.default.stylesheet", 2)
        
        # Disable automation indicators
        self.options.set_preference("dom.webdriver.enabled", False)
        self.options.set_preference("useAutomationExtension", False)
        
        # Additional privacy settings
        self.options.set_preference("privacy.trackingprotection.enabled", True)
        self.options.set_preference("geo.enabled", False)
        self.options.set_preference("media.navigator.enabled", False)

        # Automatically download and install GeckoDriver
        service = Service(GeckoDriverManager().install())
        self.driver = webdriver.Firefox(service=service, options=self.options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def company_info_scraper(self, company_name_list: List[str]) -> Dict[str, List]:
        """
        Scrape company information using Firefox - generally more reliable than Chrome
        """
        all_results = {}
        
        try:
            for i, company_name in enumerate(company_name_list):
                print(f"Searching for: {company_name} ({i+1}/{len(company_name_list)})")
                
                search_query = f"site: linkedin.com/in {company_name} company size"
                search_url = f"https://www.google.com/search?q={quote(search_query)}"
 
                self.driver.get(search_url)
                
                # Random delay to appear more human
                delay = random.uniform(3, 6)
                print(f"Waiting {delay:.1f} seconds...")
                time.sleep(delay)

                page_html = self.driver.page_source
                soup = BeautifulSoup(page_html, 'html.parser')

                # Check for CAPTCHA - Firefox typically encounters fewer CAPTCHAs
                captcha_indicators = [
                    "captcha" in page_html.lower(),
                    "recaptcha" in page_html.lower(), 
                    "robot" in page_html.lower(),
                    "unusual traffic" in page_html.lower(),
                    soup.find("div", {"id": "recaptcha"}) is not None,
                ]

                if any(captcha_indicators):
                    print(f"CAPTCHA detected for {company_name}! Waiting and retrying...")
                    time.sleep(30)  # Wait longer before retrying
                    
                    # Retry once
                    self.driver.get(search_url)
                    time.sleep(5)
                    page_html = self.driver.page_source
                    soup = BeautifulSoup(page_html, 'html.parser')
                    
                    # If still CAPTCHA, skip this company
                    if any([
                        "captcha" in page_html.lower(),
                        "recaptcha" in page_html.lower(),
                        "robot" in page_html.lower()
                    ]):
                        print(f"CAPTCHA still present for {company_name}, skipping...")
                        all_results[company_name] = []
                        continue

                search_container = soup.find("div", {"class": "dURPMd"})
                if not search_container:
                    print(f"No search results found for {company_name}")
                    all_results[company_name] = []
                    continue

                allData = search_container.find_all("div", {"class": "Ww4FFb"})
                company_results = []

                for data in allData:
                    result_obj = {}
                    
                    try:
                        title_element = data.find("h3")
                        result_obj["title"] = title_element.text if title_element else None
                    except:
                        result_obj["title"] = None

                    try:
                        link_element = data.find("a")
                        result_obj["link"] = link_element.get('href') if link_element else None
                    except:
                        result_obj["link"] = None

                    try:
                        desc_element = data.find("div", {"class": "VwiC3b"})
                        result_obj["description"] = desc_element.text if desc_element else None
                    except:
                        result_obj["description"] = None

                    if result_obj["title"] or result_obj["link"]:
                        company_results.append(result_obj)

                all_results[company_name] = company_results
                print(f"Found {len(company_results)} results for {company_name}")
                
                # Longer delay between searches
                if i < len(company_name_list) - 1:
                    delay = random.uniform(8, 15)
                    print(f"Waiting {delay:.1f} seconds before next search...")
                    time.sleep(delay)
                
        except Exception as e:
            print(f"Error during scraping: {e}")
        
        return all_results

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()


if __name__ == "__main__":
    company_list = ["Microsoft", "Google", "Apple", "Amazon"]
    
    print("Using Firefox for better stealth...")
    with FirefoxSearchScraper() as scraper:
        results = scraper.company_info_scraper(company_list)
        
        for company, search_results in results.items():
            print(f"\n{company}: {len(search_results)} results")
            for result in search_results[:3]:  
                print(f"  - {result['title']}")
                if result.get('description'):
                    print(f"    {result['description'][:100]}...")