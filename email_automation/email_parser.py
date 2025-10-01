#!/usr/bin/env python3
"""
Comprehensive LinkedIn Email Parser

This script extracts comprehensive job and application information from LinkedIn emails,
including application dates, status tracking, company information, and URL analysis.
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from custom_logging.logger import logger


class LinkedInEmailParser:
    """Comprehensive LinkedIn Email Parser with advanced analysis capabilities"""
    
    def __init__(self):
        self.status_patterns = {
            'applied_job': re.compile(r'applied_jobs-\d+-applied_job', re.IGNORECASE),
            'viewed_job': re.compile(r'job_application_viewed', re.IGNORECASE),
            'similar_job': re.compile(r'similar_jobs-\d+-similar_job', re.IGNORECASE),
            'application_date': re.compile(r'Applied on ([^<]+)', re.IGNORECASE),
            'job_status': re.compile(r'(rejected|accepted|reviewed|pending|viewed)', re.IGNORECASE)
        }
        
        self.url_patterns = {
            'job_id': re.compile(r'jobs(?:%2F|/)view(?:%2F|/)(\d+)', re.IGNORECASE),  # Handle both encoded and decoded URLs
            'tracking_id': re.compile(r'trackingId=3D([^&]+)', re.IGNORECASE),
            'ref_id': re.compile(r'refId=3D([^&]+)', re.IGNORECASE),
        }
    
    def clean_html_text(self, text: str) -> str:
        """Remove HTML entities and clean up text with better Turkish character support"""
        # First handle URL-encoded characters
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&middot;': '·',
            # Turkish characters
            '=C3=A7': 'ç',
            '=C3=87': 'Ç',
            '=C4=9F': 'ğ',
            '=C4=9E': 'Ğ',
            '=C4=B1': 'ı',
            '=C4=B0': 'İ',
            '=C3=B6': 'ö',
            '=C3=96': 'Ö',
            '=C5=9F': 'ş',
            '=C5=9E': 'Ş',
            '=C3=BC': 'ü',
            '=C3=9C': 'Ü',
            # Other common encoded characters
            '=C3=A9': 'é',
            '=E2=80=99': "'",
            '=E2=80=93': '–',
            '=E2=80=94': '—',
            '=3D': '=',
            # Line breaks and soft hyphens
            '= ': '',  # Remove soft line breaks
            ' =': '',  # Remove trailing soft breaks
            '=\n': '', # Remove line break encodings
            '=\r\n': '', # Remove Windows line breaks
        }
        
        # Replace HTML entities
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        # Handle remaining URL-encoded characters more systematically
        import re
        import urllib.parse
        
        # Try URL decoding first for any remaining encoded sequences
        try:
            text = urllib.parse.unquote(text, encoding='utf-8', errors='ignore')
        except:
            pass
            
        # Remove any remaining hex-encoded patterns that couldn't be decoded
        text = re.sub(r'=[A-F0-9]{2}', '', text)
        
        # Fix common encoding artifacts more generally
        # Remove trailing equals signs from words
        text = re.sub(r'(\w+)=\s*$', r'\1', text, flags=re.MULTILINE)
        text = re.sub(r'(\w+)=\s*(\w+)', r'\1\2', text)  # Fix broken words with = in middle
        
        # Fix broken words across lines (common in email encoding)
        text = re.sub(r'(\w+)\s+(\w+)', lambda m: self._fix_broken_word(m.group(1), m.group(2)), text)
        
        # Clean up double character issues (like çÇ at start of words)
        text = re.sub(r'([çğıöşüÇĞİÖŞÜ])\1+', r'\1', text)  # Remove duplicate Turkish chars
        text = re.sub(r'([a-zA-Z])\1{2,}', r'\1', text)  # Remove excessive repetition
        
        # Clean up multiple whitespace and normalize
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _fix_broken_word(self, word1: str, word2: str) -> str:
        """Intelligently fix broken words that were split during encoding"""
        combined = word1 + word2
        
        # Common word patterns that get broken
        word_fixes = {
            # Technical terms
            'artifi cial': 'artificial',
            'intelli gence': 'intelligence',
            'machi ne': 'machine',
            'back end': 'backend',
            'front end': 'frontend',
            'full stack': 'full-stack',
            'soft ware': 'software',
            'data base': 'database',
            'web site': 'website',
            
            # Turkish names (common patterns)
            'çağ daş': 'çağdaş',
            'meh met': 'mehmet',
            'ah met': 'ahmet',
            'mus tafa': 'mustafa',
            'özg ür': 'özgür',
            'ser hat': 'serhat',
            
            # Common company/location terms
            'istan bul': 'istanbul',
            'anka ra': 'ankara',
            'tek nokent': 'teknokent',
            'uni versity': 'university',
        }
        
        # Check if the combined lowercase version matches any known fixes
        combined_lower = combined.lower()
        spaced_version = f"{word1.lower()} {word2.lower()}"
        
        for broken, fixed in word_fixes.items():
            if broken == spaced_version or broken == combined_lower:
                # Preserve original case pattern
                if word1.isupper() and word2.isupper():
                    return fixed.upper()
                elif word1.istitle() or word2.istitle():
                    return fixed.title()
                else:
                    return fixed
        
        # If no specific fix found, check if it looks like it should be combined
        if len(word1) <= 3 or len(word2) <= 3:  # Short fragments often belong together
            return combined
        
        # Default: keep as separate words
        return f"{word1} {word2}"

    def extract_application_status(self, content: str) -> List[Dict[str, Any]]:
        """Extract job application status information"""
        applications = []
        
        # Look for applied job sections
        applied_job_sections = re.split(r'(?=applied_jobs-\d+-applied_job)', content)
        
        for section in applied_job_sections:
            if 'applied_job' not in section:
                continue
            
            app_info = {}
            
            # Extract job ID from URL
            job_id_match = self.url_patterns['job_id'].search(section)
            if job_id_match:
                app_info['job_id'] = job_id_match.group(1)
                app_info['job_link'] = f"https://www.linkedin.com/jobs/view/{job_id_match.group(1)}"
            
            # Extract tracking information
            tracking_match = self.url_patterns['tracking_id'].search(section)
            if tracking_match:
                app_info['tracking_id'] = self.clean_html_text(tracking_match.group(1))
            
            # Extract application date
            date_match = self.status_patterns['application_date'].search(section)
            if date_match:
                app_info['application_date'] = self.clean_html_text(date_match.group(1))
            
            # Extract job title
            title_patterns = [
                r'line-height: 1\.25; color: #0a66c2;">\s*([^<]+?)\s*</a>',
                r'text-color-brand[^>]*>\s*([^<]+?)\s*</a>',
                r'text-md[^>]*>\s*([^<]+?)\s*</a>'
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, section, re.IGNORECASE)
                if title_match:
                    title = self.clean_html_text(title_match.group(1))
                    if len(title) > 5:  # Filter out short non-title text
                        app_info['job_title'] = title
                        break
            
            # Extract company name
            company_patterns = [
                r'alt=3D"([^"]+)"[^>]*company-log',  # URL-encoded alt with company-log
                r'alt="([^"]+)"[^>]*company-logo',   # Regular alt with company-logo
                r'text-sm[^>]*>\s*([A-Z][^&<]+?)\s*&middot;',  # Company name before middot
                r'>\s*([A-Z][A-Za-z0-9\s]+?)\s*&middot;[^<]*(?:Istanbul|Ankara|Turkey|T=C3=BCrkiye)',  # Company before location (with numbers)
                r'>\s*([A-Z][A-Za-z0-9\s]+?)\s*&middot;[^<]*(?:Istanbul|Ankara|Turkey|Türkiye)',  # Company before decoded location (with numbers)
                r'>\s*([A-Z][a-z0-9]+)\s*&middot;',  # Short company names like F4e
            ]
            
            for pattern in company_patterns:
                company_match = re.search(pattern, section, re.IGNORECASE)
                if company_match:
                    company = self.clean_html_text(company_match.group(1))
                    if len(company) > 1 and company != 'Profile Picture' and not re.match(r'^[a-z]+$', company):
                        app_info['company'] = company
                        break
            
            # Extract location
            location_match = re.search(r'&middot;\s*([^<]+?)(?:\s*</p>)', section, re.IGNORECASE)
            if location_match:
                location = self.clean_html_text(location_match.group(1))
                if any(loc_word in location.lower() for loc_word in ['turkey', 'türkiye', 'istanbul', 'ankara', 'remote']):
                    app_info['location'] = location
            
            # Mark as applied job
            app_info['status'] = 'Applied'
            app_info['status_source'] = 'URL tracking parameter'
            
            if 'job_title' in app_info or 'job_id' in app_info:
                applications.append(app_info)
        
        return applications
    
    def extract_similar_jobs(self, content: str) -> List[Dict[str, Any]]:
        """Extract similar job recommendations"""
        similar_jobs = []
        
        # Look for similar job sections
        similar_sections = re.split(r'(?=similar_jobs-\d+-similar_job)', content)
        
        for section in similar_sections:
            if 'similar_job' not in section:
                continue
            
            job_info = {}
            
            # Extract job ID
            job_id_match = self.url_patterns['job_id'].search(section)
            if job_id_match:
                job_info['job_id'] = job_id_match.group(1)
                job_info['job_link'] = f"https://www.linkedin.com/jobs/view/{job_id_match.group(1)}"
            
            # Extract job title - be more specific to avoid matching person names
            title_patterns = [
                r'font-weight: 600[^>]*>\s*([^<]+?)\s*</a>',
                r'text-system-blue-50[^>]*>\s*([^<]+?)\s*</a>'
            ]
            
            for pattern in title_patterns:
                title_match = re.search(pattern, section, re.IGNORECASE)
                if title_match:
                    title = self.clean_html_text(title_match.group(1))
                    # Filter out person names and only keep job-like titles
                    if (len(title) > 5 and 
                        not re.match(r'^[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+$', title) and  # Not "Name Surname"
                        any(job_word in title.lower() for job_word in ['developer', 'engineer', 'intern', 'specialist', 'manager', 'analyst', 'designer', 'architect', 'lead', 'senior', 'junior', 'full-stack', 'backend', 'frontend', 'software', 'data', 'ai', 'artificial intelligence', 'machine learning', 'devops', 'qa', 'tester'])):
                        job_info['job_title'] = title
                        break
            
            # Extract company
            company_patterns = [
                r'alt=3D"([^"]+)"[^>]*company-log',  # URL-encoded alt with company-log
                r'alt="([^"]+)"[^>]*company-logo',   # Regular alt with company-logo
                r'>\s*([A-Z][A-Za-z0-9\s]+?)\s*&middot;[^<]*(?:Istanbul|Ankara|Turkey|T=C3=BCrkiye)',  # Company before location (with numbers)
                r'>\s*([A-Z][A-Za-z0-9\s]+?)\s*&middot;[^<]*(?:Istanbul|Ankara|Turkey|Türkiye)',  # Company before decoded location (with numbers)
                r'>\s*([A-Z][a-z0-9]+)\s*&middot;',  # Short company names like F4e
            ]
            
            for pattern in company_patterns:
                company_match = re.search(pattern, section, re.IGNORECASE)
                if company_match:
                    company = self.clean_html_text(company_match.group(1))
                    if len(company) > 1 and company != 'Profile Picture' and not re.match(r'^[a-z]+$', company):
                        job_info['company'] = company
                        break
            
            # Extract location
            location_match = re.search(r'&middot;\s*([^<]+?)(?:\s*</p>)', section, re.IGNORECASE)
            if location_match:
                location = self.clean_html_text(location_match.group(1))
                if any(loc_word in location.lower() for loc_word in ['turkey', 'türkiye', 'istanbul', 'ankara', 'remote']):
                    job_info['location'] = location
            
            job_info['status'] = 'Recommended'
            job_info['status_source'] = 'Similar job suggestion'
            
            if 'job_title' in job_info:
                similar_jobs.append(job_info)
        
        return similar_jobs
    
    def analyze_email_type(self, content: str) -> Dict[str, Any]:
        """Analyze the type and purpose of the email"""
        analysis = {
            'email_type': 'Unknown',
            'contains_applied_jobs': False,
            'contains_similar_jobs': False,
            'contains_application_status': False,
            'tracking_indicators': []
        }
        
        # Check for applied jobs
        if re.search(r'applied_jobs-\d+-applied_job', content):
            analysis['contains_applied_jobs'] = True
            analysis['tracking_indicators'].append('Applied job tracking')
        
        # Check for similar jobs
        if re.search(r'similar_jobs-\d+-similar_job', content):
            analysis['contains_similar_jobs'] = True
            analysis['tracking_indicators'].append('Similar job recommendations')
        
        # Check for application viewed notification
        if re.search(r'job_application_viewed', content):
            analysis['contains_application_status'] = True
            analysis['email_type'] = 'Job Application Status Update'
            analysis['tracking_indicators'].append('Application view tracking')
        
        # Check for application dates
        if re.search(r'Applied on', content):
            analysis['tracking_indicators'].append('Application date tracking')
        
        return analysis
    
    def parse_email(self, content: str) -> Dict[str, Any]:
        """Parse LinkedIn email and extract comprehensive job and application information"""
        
        try:
            
            
            logger.info("File loaded, analyzing email structure and extracting information...")
            
            # Extract profile info
            profile_info = {}
            recipient_match = re.search(r'This email was intended for ([^(]+)\(([^)]+)\)', content)
            if recipient_match:
                profile_info['name'] = self.clean_html_text(recipient_match.group(1).strip())
                profile_info['profile_description'] = self.clean_html_text(recipient_match.group(2))
            
            # Analyze email type and structure
            email_analysis = self.analyze_email_type(content)
            
            # Extract application status information
            applied_jobs = self.extract_application_status(content)
            
            # Extract similar/recommended jobs
            similar_jobs = self.extract_similar_jobs(content)
            
            # Combine all data
            result = {
                'profile_info': profile_info,
                'email_analysis': email_analysis,
                'applied_jobs': applied_jobs,
                'recommended_jobs': similar_jobs,
                'summary': {
                    'total_applied_jobs': len(applied_jobs),
                    'total_recommended_jobs': len(similar_jobs),
                    'email_purpose': email_analysis['email_type'],
                    'tracking_features': email_analysis['tracking_indicators']
                }
            }
            
            logger.info(f"Email parsing completed!")
            logger.info(f"Found {len(applied_jobs)} applied jobs and {len(similar_jobs)} recommended jobs")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced email parsing: {str(e)}")
            raise
    
    def deduplicated_jobs(self, result: dict) -> Tuple[set, int]:
        seen_job_ids = set()
        deduplicated_applied = []
        for job in result['applied_jobs']:
            job_id = job.get('job_id') or job.get('job_link', '').split('/')[-1] if job.get('job_link') else None
            if job_id and job_id not in seen_job_ids:
                seen_job_ids.add(job_id)
                deduplicated_applied.append(job)
            elif not job_id:  # Keep jobs without IDs (they might be different)
                deduplicated_applied.append(job)
        return seen_job_ids, len(deduplicated_applied)
    
    def deduplicated_recommended_jobs(self, result: dict, seen_job_ids: set) -> Tuple[List, int]:
        deduplicated_recommended = []
        for job in result['recommended_jobs']:
            job_id = job.get('job_id') or job.get('job_link', '').split('/')[-1] if job.get('job_link') else None
            if job_id and job_id not in seen_job_ids:
                seen_job_ids.add(job_id)
                deduplicated_recommended.append(job)
            elif not job_id:  # Keep jobs without IDs (they might be different)
                deduplicated_recommended.append(job)
        return deduplicated_recommended, len(deduplicated_recommended)

def main():
    """Main function for comprehensive email parsing"""
    try:
        parser = LinkedInEmailParser()

        # EXAMPLE USAGE
         
        #email_file = "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/output.txt"
        
        #result = parser.parse_email(email_file)
        
        #jobs, len_jobs = parser.deduplicated_jobs(result)
        #recommended_jobs, len_recommended_jobs = parser.deduplicated_recommended_jobs(result, jobs)

    except Exception as e:
        raise e

if __name__ == "__main__":
    main()