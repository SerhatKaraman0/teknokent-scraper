from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import time
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote
import random 
import requests
from selenium_recaptcha import Recaptcha_Solver

class SearchResultsScraper:
    def __init__(self) -> None:
        
        self.X, self.y = self._generate_random_numbers()
        
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(f"start-maximized")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-plugins")
        self.options.add_argument("--disable-images")
        self.options.add_argument("--disable-javascript")
        self.options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        stealth(self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    @staticmethod 
    def _generate_random_numbers():
        try:
            first_random_number_url: str = "https://www.random.org/integers?num=1&min=50&max=796&col=5&base=10&format=plain&rnd=new"
            second_random_number_url: str = "https://www.random.org/integers?num=1&min=50&max=200&col=5&base=10&format=plain&rnd=new"
             
            first_num: str = requests.get(first_random_number_url).text
            second_num: str = requests.get(second_random_number_url).text
             
            if first_num and second_num:
                return [first_num, second_num]
            print(f"X: {first_num}, y: {second_num}")

            return [] 
        except Exception as e:
            raise ValueError(f"Can't generate the numbers because of {e}")
        
    def company_info_scraper(self, company_name_list: List[str]) -> Dict[str, List]:
        """
        Scrape company information for multiple companies using the same driver instance.
        Returns a dictionary with company names as keys and search results as values.
        """
        print(f"X: {self.X}, y: {self.y}")
        all_results = {}
        
        try:
            for company_name in company_name_list:
                print(f"Searching for: {company_name}")
                
                encoded_company = quote(company_name)
                search_query = f"site: linkedin.com/in {company_name} company size"
                search_url = f"https://www.google.com/search?q={quote(search_query)}"
 
                self.driver.get(search_url)
                
                time.sleep(5)

                page_html = self.driver.page_source
                soup = BeautifulSoup(page_html, 'html.parser')

                # Check for CAPTCHA with multiple indicators
                captcha_indicators = [
                    "captcha" in page_html.lower(),
                    "recaptcha" in page_html.lower(), 
                    "robot" in page_html.lower(),
                    "unusual traffic" in page_html.lower(),
                    soup.find("div", {"id": "recaptcha"}) is not None,
                    soup.find("iframe", {"title": "reCAPTCHA"}) is not None,
                    soup.find("div", {"class": "g-recaptcha"}) is not None,
                    "g-recaptcha" in page_html.lower(),
                    soup.find("div", {"data-sitekey": True}) is not None
                ]

                if any(captcha_indicators):
                    print(f"CAPTCHA detected for {company_name}! Attempting to solve...")
                    try:
                        solver = Recaptcha_Solver(driver=self.driver)
                        solver.solve_recaptcha()
                        
                        # Wait for CAPTCHA to be solved
                        time.sleep(10)
                        
                        # Reload the page to get fresh content after CAPTCHA solving
                        page_html = self.driver.page_source
                        soup = BeautifulSoup(page_html, 'html.parser')
                        
                        # Check if CAPTCHA is still present
                        if any([
                            "captcha" in page_html.lower(),
                            "recaptcha" in page_html.lower(),
                            "robot" in page_html.lower()
                        ]):
                            print(f"CAPTCHA still present for {company_name}, skipping...")
                            all_results[company_name] = []
                            continue
                        else:
                            print(f"CAPTCHA solved successfully for {company_name}")
                            
                    except Exception as captcha_error:
                        print(f"Failed to solve CAPTCHA for {company_name}: {captcha_error}")
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
                
                time.sleep(10)
                
        except Exception as e:
            print(f"Error during scraping: {e}")
        
        return all_results

    def close_driver(self):
        """Close the driver when done"""
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically closes driver"""
        self.close_driver()


if __name__ == "__main__":
    company_list = ["Rapsodo", "Başarsoft", "Teknasyon", "Cloudflare"]
    
    with SearchResultsScraper() as scraper:
        results = scraper.company_info_scraper(company_list)
        
        for company, search_results in results.items():
            print(f"\n{company}: {len(search_results)} results")
            for result in search_results[:3]:  
                print(f"  - {result['title']}")
                print(f"    {result['description']}")
    