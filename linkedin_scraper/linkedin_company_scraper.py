"""
LinkedIn Company Scraper using the original scrape-linkedin library
Fixed to work with Selenium 3.x and timeout issues
"""

import os
import pandas as pd
import shutil
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager

# Clean up any existing tmp_data directory to avoid conflicts
if os.path.exists('tmp_data'):
    print("Cleaning up existing tmp_data directory...")
    shutil.rmtree('tmp_data')

# Set up environment for the library
print("Setting up ChromeDriver...")
driver_path = ChromeDriverManager().install()
driver_dir = os.path.dirname(driver_path)
os.environ['PATH'] = driver_dir + os.pathsep + os.environ.get('PATH', '')

# Fix timeout compatibility issues
print("Applying compatibility patches...")
import urllib3
from urllib3.util.timeout import Timeout

original_timeout_init = Timeout.__init__

def patched_timeout_init(self, total=None, connect=None, read=None):
    if hasattr(connect, '__class__') and connect.__class__.__name__ == 'object':
        connect = None
    if hasattr(read, '__class__') and read.__class__.__name__ == 'object':
        read = None
    if hasattr(total, '__class__') and total.__class__.__name__ == 'object':
        total = None
    return original_timeout_init(self, total=total, connect=connect, read=read)

Timeout.__init__ = patched_timeout_init

# Now import the scrape_linkedin library
from scrape_linkedin import CompanyScraper

load_dotenv()

def main():
    linkedin_cookie = os.getenv("LINKEDIN_SESSION_COOKIE")
    
    if not linkedin_cookie:
        print("❌ LINKEDIN_SESSION_COOKIE not found in .env file")
        print("Please get a fresh LinkedIn session cookie (li_at value)")
        return

    # LIST YOUR COMPANIES HERE
    companies = ['basarsoft', 'roboflow', 'udemy', 'microsoft']
    
    company_data = []

    try:
        print("Initializing LinkedIn scraper...")
        # Use the sequential approach that was working
        with CompanyScraper(cookie=linkedin_cookie, timeout=60) as scraper:
            print("✓ Scraper initialized successfully")
            
            # Get each company's overview
            for i, name in enumerate(companies):
                try:
                    print(f"Scraping {i+1}/{len(companies)}: {name}...")
                    result = scraper.scrape(company=name)
                    
                    if result and result.overview:
                        overview = dict(result.overview)
                        overview['company_name'] = name
                        company_data.append(overview)
                        print(f"✓ Successfully scraped {name}")
                        print(f"  Found data: {list(overview.keys())}")
                    else:
                        print(f"✗ No data found for {name}")
                        company_data.append({'company_name': name, 'error': 'No data found'})
                        
                except Exception as e:
                    print(f"✗ Failed to scrape {name}: {e}")
                    company_data.append({'company_name': name, 'error': str(e)})

        # Turn into dataframe for easy csv output
        if company_data:
            df = pd.DataFrame(company_data)
            output_file = 'linkedin_scraper/out.csv'
            df.to_csv(output_file, index=False)
            print(f"✓ Data saved to {output_file} with {len(company_data)} entries")
            print(f"✓ Columns: {list(df.columns)}")
            
            # Also save as JSON
            import json
            json_file = 'linkedin_scraper/companies.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(company_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Also saved as JSON: {json_file}")
        else:
            print("✗ No data was collected")

    except Exception as e:
        print(f"✗ Error during scraping: {e}")
        print("\nTroubleshooting steps:")
        print("1. Get a fresh LinkedIn session cookie (li_at value)")
        print("   - Log into LinkedIn in your browser")
        print("   - Open Developer Tools (F12)")
        print("   - Go to Application > Cookies > https://www.linkedin.com")
        print("   - Find the 'li_at' cookie and copy its value")
        print("   - Update your .env file with the new value")
        print("2. Make sure Chrome browser is installed")
        print("3. Try with different company names")
        print("4. Check your internet connection")

if __name__ == "__main__":
    main()