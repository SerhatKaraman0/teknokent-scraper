import pytest
import csv
import json
import sys
import os
import re
from html import unescape

# Add the parent directory to the path to import the email_automation module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from email_automation.email_parser import LinkedInEmailParser


def test_examine_real_email_structure():
    """Examine the actual structure of real LinkedIn job emails"""
    csv.field_size_limit(10000000)
    
    try:
        with open('/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/SERHATKEDU_MAIL_OUTPUTS.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            count = 0
            for row in reader:
                sender = row.get('EMAIL_SENDER', '')
                if 'jobs-listings' in sender and count < 1:  # Examine first job listing email
                    print(f"=== REAL EMAIL {count + 1} STRUCTURE ===")
                    print(f"Sender: {sender}")
                    print(f"Subject: {row.get('EMAIL_SUBJECT', '')}")
                    
                    body = row.get('EMAIL_BODY', '')
                    print(f"Body length: {len(body)} characters")
                    print()
                    
                    # Extract and clean HTML
                    print("=== CLEANED TEXT PREVIEW ===")
                    # Remove HTML tags but keep text content
                    clean_text = re.sub(r'<[^>]+>', ' ', body)
                    clean_text = unescape(clean_text)  # Decode HTML entities
                    clean_text = ' '.join(clean_text.split())  # Normalize whitespace
                    
                    print(f"Cleaned text length: {len(clean_text)} characters")
                    print(f"First 2000 characters:")
                    print(clean_text[:2000])
                    print()
                    
                    # Look for job-related patterns
                    print("=== SEARCHING FOR JOB PATTERNS ===")
                    
                    # Find all job URLs
                    job_urls = re.findall(r'https?://[^\s<>"]*jobs/view/\d+[^\s<>"]*', body)
                    print(f"Found {len(job_urls)} job URLs:")
                    for i, url in enumerate(job_urls[:3]):  # Show first 3
                        job_id = re.search(r'jobs/view/(\d+)', url)
                        if job_id:
                            print(f"  Job {i+1}: ID {job_id.group(1)}")
                            print(f"    URL: {url[:100]}...")
                    print()
                    
                    # Look for company patterns in the cleaned text
                    print("=== SEARCHING FOR COMPANY PATTERNS ===")
                    company_patterns = [
                        r'([A-Z][a-zA-Z\s&,.-]{2,50})\s+(?:is hiring|is looking for|posted|seeks)',
                        r'Apply to\s+([A-Z][a-zA-Z\s&,.-]{2,50})',
                        r'Join\s+([A-Z][a-zA-Z\s&,.-]{2,50})\s+team',
                        r'([A-Z][a-zA-Z\s&,.-]{2,50})\s+team',
                        r'Work at\s+([A-Z][a-zA-Z\s&,.-]{2,50})',
                    ]
                    
                    all_companies = set()
                    for pattern in company_patterns:
                        matches = re.findall(pattern, clean_text, re.IGNORECASE)
                        for match in matches:
                            company = match.strip()
                            if len(company) > 2 and not company.lower().startswith(('http', 'www', 'click')):
                                all_companies.add(company)
                    
                    print(f"Found potential companies: {list(all_companies)}")
                    print()
                    
                    # Test current parser
                    print("=== CURRENT PARSER RESULTS ===")
                    parser = LinkedInEmailParser()
                    result = parser.parse_linkedin_email(
                        sender,
                        row.get('EMAIL_SUBJECT', ''),
                        body,
                        row.get('EMAIL_DATE', '')
                    )
                    
                    print(f"Jobs found: {len(result.get('jobs', []))}")
                    for i, job in enumerate(result.get('jobs', [])[:3]):
                        print(f"  Job {i+1}: {job.get('job_id', 'No ID')}")
                        print(f"    Company: {job.get('company', 'NOT EXTRACTED')}")
                        print(f"    Position: {job.get('position', 'NOT EXTRACTED')}")
                    
                    count += 1
                    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_examine_real_email_structure()