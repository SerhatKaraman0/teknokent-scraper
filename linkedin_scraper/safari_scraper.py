from selenium import webdriver
from selenium.webdriver.safari.service import Service
import time
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote
import random

class SafariSearchScraper:
    def __init__(self) -> None:
        """
        Safari WebDriver - Built into macOS, no driver installation needed!
        Generally the least detected by Google's anti-bot systems.
        
        NOTE: You need to enable "Allow Remote Automation" in Safari:
        Safari > Develop > Allow Remote Automation
        """
        
        # Safari doesn't need many options - it's naturally stealthy
        self.driver = webdriver.Safari()
        
        # Set window size
        self.driver.set_window_size(1920, 1080)
        
        print("Safari WebDriver initialized - naturally stealthy!")

    def company_info_scraper(self, company_name_list: List[str]) -> Dict[str, List]:
        """
        Scrape using Safari - typically the most reliable for avoiding detection
        """
        all_results = {}
        
        try:
            for i, company_name in enumerate(company_name_list):
                print(f"Searching for: {company_name} ({i+1}/{len(company_name_list)})")
                
                search_query = f"site: linkedin.com/in {company_name} company size"
                search_url = f"https://www.google.com/search?q={quote(search_query)}"
 
                self.driver.get(search_url)
                
                # Random delay
                delay = random.uniform(2, 5)
                print(f"Waiting {delay:.1f} seconds...")
                time.sleep(delay)

                page_html = self.driver.page_source
                soup = BeautifulSoup(page_html, 'html.parser')

                # Safari typically encounters very few CAPTCHAs
                if any([
                    "captcha" in page_html.lower(),
                    "recaptcha" in page_html.lower(),
                    "unusual traffic" in page_html.lower()
                ]):
                    print(f"CAPTCHA detected for {company_name} (rare with Safari). Waiting...")
                    time.sleep(20)
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
                
                # Moderate delay between searches
                if i < len(company_name_list) - 1:
                    delay = random.uniform(5, 10)
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
    
    print("Using Safari WebDriver - most stealthy option on Mac!")
    print("Make sure 'Allow Remote Automation' is enabled in Safari > Develop menu")
    
    try:
        with SafariSearchScraper() as scraper:
            results = scraper.company_info_scraper(company_list)
            
            for company, search_results in results.items():
                print(f"\n{company}: {len(search_results)} results")
                for result in search_results[:3]:  
                    print(f"  - {result['title']}")
                    if result.get('description'):
                        print(f"    {result['description'][:100]}...")
    except Exception as e:
        print(f"Safari WebDriver error: {e}")
        print("Make sure to enable Safari > Develop > Allow Remote Automation")