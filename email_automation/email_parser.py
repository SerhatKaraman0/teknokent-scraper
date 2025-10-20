#!/usr/bin/env python3

import re
import json
import csv
from datetime import datetime
from typing import List, Dict, Any


class LinkedInEmailParser:
    
    def __init__(self):
        self.sender_types = {
            'job_alerts': 'LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>',
            'jobs_noreply': 'LinkedIn <jobs-noreply@linkedin.com>',
            'jobs_listings': 'LinkedIn <jobs-listings@linkedin.com>',
            'messages': 'LinkedIn <messages-noreply@linkedin.com>',
            'notifications': 'LinkedIn <notifications-noreply@linkedin.com>',
            'updates': 'LinkedIn <updates-noreply@linkedin.com>'
        }
    
    def clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_urls(self, html_content):
        urls = []
        if html_content:
            url_pattern = r'https?://[^\s<>"]+?linkedin\.com[^\s<>"]*'
            urls = re.findall(url_pattern, html_content)
        return urls
    
    def extract_job_id(self, url):
        if url:
            match = re.search(r'jobs/view/(\d+)', url)
            if match:
                return match.group(1)
        return None
    
    def extract_job_data_from_email(self, body, job_ids):
        """
        Extract job data by splitting email content and matching with job IDs by order
        Pattern: "Position Title CompanyName · Location Actively recruiting Easy Apply"
        """
        # Clean and decode the email body
        cleaned_body = self.clean_text(body)
        
        # Find all job entries using a more specific pattern
        # Look for the pattern: text followed by "Actively recruiting Easy Apply"
        job_pattern = r'([^A]+?)(?=Actively recruiting\s*Easy Apply)'
        job_matches = re.findall(job_pattern, cleaned_body, re.DOTALL)
        
        job_data = {}
        
        # Process each job match
        for i, job_text in enumerate(job_matches):
            if i < len(job_ids):
                job_id = job_ids[i]
                
                # Clean the job text and get the last meaningful line
                lines = [line.strip() for line in job_text.split('\n') if line.strip()]
                
                if lines:
                    # The job info is usually in the last line before "Actively recruiting"
                    job_line = lines[-1].strip()
                    
                    # Pattern: "Position Title CompanyName · Location"
                    # Split by " · " to separate company/position from location
                    if ' · ' in job_line:
                        job_part, location = job_line.split(' · ', 1)
                        
                        # Now split the job_part to get position and company
                        # The pattern is usually: "Position Title CompanyName"
                        # We need to find where the position ends and company begins
                        
                        # Try common patterns to separate position from company
                        words = job_part.strip().split()
                        if len(words) >= 2:
                            # Heuristic: Company names are often capitalized words at the end
                            # Look for capitalized words that might be company names
                            for split_idx in range(1, len(words)):
                                potential_company = ' '.join(words[split_idx:])
                                potential_position = ' '.join(words[:split_idx])
                                
                                # If the potential company has capitalized words, it's likely correct
                                if potential_company and potential_company[0].isupper():
                                    company = potential_company
                                    position = potential_position
                                    break
                            else:
                                # Fallback: assume last word is company
                                company = words[-1]
                                position = ' '.join(words[:-1])
                        else:
                            company = job_part
                            position = job_part
                    else:
                        # No location separator found, use the whole line
                        position = job_line
                        company = "NOT EXTRACTED"
                    
                    job_data[job_id] = {
                        'company': company.strip(),
                        'position': position.strip()
                    }
        
        return job_data
    
    def extract_company_for_job(self, body_text, job_id, job_url):
        """Extract company name for a specific job from email body text"""
        # Clean HTML and decode entities
        from html import unescape
        clean_text = re.sub(r'<[^>]+>', ' ', body_text)
        clean_text = unescape(clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)  # Normalize whitespace
        
        # Split by common job delimiters to isolate individual job sections
        job_sections = re.split(r'(Easy Apply|Actively recruiting|Apply now)', clean_text)
        
        for section in job_sections:
            if job_id in section:
                # Pattern: "Company · Location" - extract just the company name
                company_match = re.search(r'(\w+(?:\s+\w+)*)\s*·\s*[A-Za-z\s,]+', section)
                if company_match:
                    company = company_match.group(1).strip()
                    if self._is_valid_company_name(company):
                        return company
        
        # Fallback: look in the full text for company pattern
        company_matches = re.findall(r'(\w+)\s*·\s*[A-Za-z\s,]+', clean_text)
        for company in company_matches:
            if self._is_valid_company_name(company):
                return company
        
        return None
    
    def extract_position_for_job(self, body_text, job_id, job_url):
        """Extract position title for a specific job from email body text"""
        # Clean HTML and decode entities
        from html import unescape
        clean_text = re.sub(r'<[^>]+>', ' ', body_text)
        clean_text = unescape(clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text)  # Normalize whitespace
        
        # Split by common job delimiters to isolate individual job sections
        job_sections = re.split(r'(Easy Apply|Actively recruiting|Apply now)', clean_text)
        
        for section in job_sections:
            if job_id in section:
                # Pattern: "Job Title Company · Location" - extract the job title
                title_match = re.search(r'([\w\s/\-]+?(?:Developer|Engineer|Manager|Analyst|Director|Specialist|Consultant|Designer|Programmer|Architect))', section, re.IGNORECASE)
                if title_match:
                    position = title_match.group(1).strip()
                    # Clean up prefixes
                    position = re.sub(r'^.*?(?:you|for)\s+', '', position, flags=re.IGNORECASE)
                    position = re.sub(r'\s+position$', '', position, flags=re.IGNORECASE)
                    position = re.sub(r'\s+role$', '', position, flags=re.IGNORECASE)
                    position = position.strip()
                    if self._is_valid_position_name(position):
                        return position
                
                # Alternative: Look for job title before company · location pattern
                before_company_match = re.search(r'([\w\s/\-]+?)\s+(\w+)\s*·\s*[A-Za-z\s,]+', section)
                if before_company_match:
                    position = before_company_match.group(1).strip()
                    # Clean up prefixes
                    position = re.sub(r'^.*?(?:you|for)\s+', '', position, flags=re.IGNORECASE)
                    position = re.sub(r'\s+position$', '', position, flags=re.IGNORECASE)
                    position = re.sub(r'\s+role$', '', position, flags=re.IGNORECASE)
                    position = position.strip()
                    if self._is_valid_position_name(position) and len(position) > 3:
                        return position
        
        return None
    
    def _is_valid_company_name(self, company):
        """Check if extracted text is a valid company name"""
        if not company or len(company) < 2:
            return False
        
        # Filter out common false positives
        invalid_terms = [
            'new', 'job', 'jobs', 'the', 'and', 'for', 'your', 'you', 'this', 'that', 
            'with', 'from', 'apply', 'now', 'today', 'click', 'view', 'see', 'more',
            'position', 'role', 'team', 'looking', 'hiring', 'posted', 'great', 'other'
        ]
        
        company_lower = company.lower().strip()
        
        if (company_lower in invalid_terms or 
            company_lower.startswith(('http', 'www', 'click', 'view', 'see', 'apply')) or
            len(company) > 50):
            return False
            
        return True
    
    def _is_valid_position_name(self, position):
        """Check if extracted text is a valid position name"""
        if not position or len(position) < 3:
            return False
        
        position_lower = position.lower().strip()
        
        # Clean up common suffixes
        position = re.sub(r'\s+position$', '', position, flags=re.IGNORECASE)
        position = re.sub(r'\s+role$', '', position, flags=re.IGNORECASE)
        position = position.strip()
        
        if (position_lower.startswith(('http', 'www', 'click', 'view', 'see', 'apply')) or
            len(position) > 50 or len(position) < 3):
            return False
            
        return True
    
    def parse_job_alerts(self, subject, body, date):
        parsed_data = {
            'sender_type': 'job_alerts',
            'email_type': 'Job Alert',
            'subject': self.clean_text(subject),
            'date': date,
            'jobs': [],
            'alert_info': {},
            'statistics': {}
        }
        
        subject_lower = subject.lower()
        
        if 'job alert' in subject_lower:
            alert_match = re.search(r'job alert for (.+?) has been', subject_lower)
            if alert_match:
                parsed_data['alert_info']['search_term'] = alert_match.group(1)
        
        if 'created' in subject_lower:
            parsed_data['alert_info']['action'] = 'created'
        elif 'updated' in subject_lower:
            parsed_data['alert_info']['action'] = 'updated'
        
        location_match = re.search(r'in (.+?)$', subject_lower)
        if location_match:
            parsed_data['alert_info']['location'] = location_match.group(1)
        
        urls = self.extract_urls(body)
        job_urls = [url for url in urls if 'jobs/view' in url]
        
        unique_jobs = {}
        for url in job_urls:
            job_id = self.extract_job_id(url)
            if job_id and job_id not in unique_jobs:
                unique_jobs[job_id] = {
                    'job_id': job_id,
                    'job_url': url
                }
        
        parsed_data['jobs'] = list(unique_jobs.values())
        
        body_text = self.clean_text(body)
        job_count_match = re.search(r'(\d+)\s+(?:new\s+)?jobs?\s+(?:found|available)', body_text, re.IGNORECASE)
        if job_count_match:
            parsed_data['statistics']['total_jobs_found'] = int(job_count_match.group(1))
        
        parsed_data['statistics']['jobs_in_email'] = len(parsed_data['jobs'])
        
        return parsed_data
    
    def parse_jobs_noreply(self, subject, body, date):
        parsed_data = {
            'sender_type': 'jobs_noreply',
            'email_type': 'Job Recommendations',
            'subject': self.clean_text(subject),
            'date': date,
            'jobs': [],
            'recommendation_context': {},
            'statistics': {}
        }
        
        subject_lower = subject.lower()
        
        if 'similar to' in subject_lower:
            similar_match = re.search(r'similar to (.+?)(?:\s+\-|$)', subject_lower)
            if similar_match:
                parsed_data['recommendation_context']['based_on_job'] = similar_match.group(1).strip()
        
        if 'new jobs' in subject_lower:
            parsed_data['recommendation_context']['type'] = 'new_recommendations'
        elif 'recommended' in subject_lower:
            parsed_data['recommendation_context']['type'] = 'personalized_recommendations'
        
        location_match = re.search(r'in (.+?)$', subject_lower)
        if location_match:
            parsed_data['recommendation_context']['location'] = location_match.group(1)
        
        urls = self.extract_urls(body)
        job_urls = [url for url in urls if 'jobs/view' in url]
        
        unique_jobs = {}
        for url in job_urls:
            job_id = self.extract_job_id(url)
            if job_id and job_id not in unique_jobs:
                unique_jobs[job_id] = {
                    'job_id': job_id,
                    'job_url': url
                }
        
        parsed_data['jobs'] = list(unique_jobs.values())
        parsed_data['statistics']['total_recommendations'] = len(parsed_data['jobs'])
        
        return parsed_data
    
    def parse_jobs_listings(self, subject, body, date):
        parsed_data = {
            'sender_type': 'jobs_listings',
            'email_type': 'Job Listing Digest',
            'subject': self.clean_text(subject),
            'date': date,
            'featured_job': {},
            'jobs': []
        }
        
        if 'is looking for:' in subject:
            parts = subject.split('is looking for:')
            if len(parts) == 2:
                parsed_data['featured_job']['company'] = parts[0].strip()
                parsed_data['featured_job']['position'] = parts[1].strip()
        
        urls = self.extract_urls(body)
        job_urls = [url for url in urls if 'jobs/view' in url]
        
        # Extract job IDs first
        job_ids = []
        for url in job_urls:
            job_id = self.extract_job_id(url)
            if job_id:
                job_ids.append(job_id)
        
        # Remove duplicates while preserving order
        unique_job_ids = []
        seen = set()
        for job_id in job_ids:
            if job_id not in seen:
                unique_job_ids.append(job_id)
                seen.add(job_id)
        
        # Extract job data from the structured email content
        job_data_dict = self.extract_job_data_from_email(body, unique_job_ids)
        
        unique_jobs = {}
        for i, url in enumerate(job_urls):
            job_id = self.extract_job_id(url)
            if job_id and job_id not in unique_jobs:
                job_data = {
                    'job_id': job_id,
                    'job_url': url
                }
                
                # Get job data from the extracted dictionary
                if job_id in job_data_dict:
                    extracted_data = job_data_dict[job_id]
                    if extracted_data.get('company'):
                        job_data['company'] = extracted_data['company']
                    if extracted_data.get('position'):
                        job_data['position'] = extracted_data['position']
                
                unique_jobs[job_id] = job_data
        
        parsed_data['jobs'] = list(unique_jobs.values())
        
        if parsed_data['jobs']:
            parsed_data['featured_job']['job_url'] = parsed_data['jobs'][0]['job_url']
            parsed_data['featured_job']['job_id'] = parsed_data['jobs'][0]['job_id']
        
        return parsed_data
    
    def parse_messages(self, subject, body, date):
        parsed_data = {
            'sender_type': 'messages',
            'email_type': 'LinkedIn Message',
            'subject': self.clean_text(subject),
            'date': date,
            'message_type': 'unknown',
            'details': {},
            'urls': []
        }
        
        subject_lower = subject.lower()
        
        if 'confirm your email' in subject_lower or 'verify' in subject_lower:
            parsed_data['message_type'] = 'email_confirmation'
        elif 'getting noticed' in subject_lower or 'profile view' in subject_lower or 'viewed your profile' in subject_lower:
            parsed_data['message_type'] = 'profile_views'
            view_match = re.search(r'(\d+)\s+(?:people|recruiters|professionals)', subject_lower)
            if view_match:
                parsed_data['details']['viewer_count'] = int(view_match.group(1))
        elif 'connection' in subject_lower or 'invite' in subject_lower:
            parsed_data['message_type'] = 'connection_request'
            name_match = re.search(r'from ([A-Z][a-z]+ [A-Z][a-z]+)', subject)
            if name_match:
                parsed_data['details']['sender_name'] = name_match.group(1)
        elif 'message' in subject_lower:
            parsed_data['message_type'] = 'direct_message'
        elif 'endorsement' in subject_lower:
            parsed_data['message_type'] = 'skill_endorsement'
        elif 'recommendation' in subject_lower:
            parsed_data['message_type'] = 'recommendation'
        elif 'anniversary' in subject_lower or 'work anniversary' in subject_lower:
            parsed_data['message_type'] = 'work_anniversary'
        
        urls = self.extract_urls(body)
        parsed_data['urls'] = [url for url in urls if 'linkedin.com' in url]
        
        profile_urls = [url for url in urls if '/in/' in url]
        parsed_data['details']['profile_links'] = profile_urls
        
        return parsed_data
    
    def parse_notifications(self, subject, body, date):
        parsed_data = {
            'sender_type': 'notifications',
            'email_type': 'Notification Digest',
            'subject': self.clean_text(subject),
            'date': date,
            'notification_count': 0,
            'notification_types': [],
            'details': {},
            'urls': []
        }
        
        subject_lower = subject.lower()
        
        count_match = re.search(r'(\d+)\s+unread\s+notification', subject_lower)
        if count_match:
            parsed_data['notification_count'] = int(count_match.group(1))
        
        if 'profile view' in subject_lower:
            parsed_data['notification_types'].append('profile_views')
        if 'connection' in subject_lower:
            parsed_data['notification_types'].append('connections')
        if 'message' in subject_lower:
            parsed_data['notification_types'].append('messages')
        if 'job' in subject_lower:
            parsed_data['notification_types'].append('job_alerts')
        if 'endorsement' in subject_lower:
            parsed_data['notification_types'].append('endorsements')
        
        urls = self.extract_urls(body)
        parsed_data['urls'] = [url for url in urls if 'linkedin.com' in url]
        
        notification_urls = [url for url in urls if '/notifications' in url]
        parsed_data['details']['notification_links'] = notification_urls
        
        body_text = self.clean_text(body)
        
        view_count_match = re.search(r'(\d+)\s+(?:people|professionals)\s+viewed', body_text, re.IGNORECASE)
        if view_count_match:
            parsed_data['details']['profile_views'] = int(view_count_match.group(1))
        
        message_count_match = re.search(r'(\d+)\s+(?:new\s+)?messages?', body_text, re.IGNORECASE)
        if message_count_match:
            parsed_data['details']['new_messages'] = int(message_count_match.group(1))
        
        return parsed_data
    
    def parse_updates(self, subject, body, date):
        parsed_data = {
            'sender_type': 'updates',
            'email_type': 'LinkedIn Updates',
            'subject': self.clean_text(subject),
            'date': date,
            'update_type': 'general',
            'content_sources': [],
            'topics': [],
            'urls': [],
            'statistics': {}
        }
        
        subject_lower = subject.lower()
        
        if 'wall street journal' in subject_lower or 'news' in subject_lower:
            parsed_data['update_type'] = 'news_digest'
        elif 'connection' in subject_lower or 'network' in subject_lower:
            parsed_data['update_type'] = 'network_update'
        elif 'job' in subject_lower:
            parsed_data['update_type'] = 'job_market'
        elif 'trending' in subject_lower:
            parsed_data['update_type'] = 'trending_content'
        elif 'weekly' in subject_lower or 'daily' in subject_lower:
            parsed_data['update_type'] = 'periodic_digest'
        
        news_sources = ['wall street journal', 'bloomberg', 'reuters', 'forbes', 'techcrunch', 'harvard business review']
        for source in news_sources:
            if source in subject_lower:
                parsed_data['content_sources'].append(source)
        
        topics = ['ai', 'artificial intelligence', 'technology', 'business', 'finance', 'career', 'leadership', 'startup']
        for topic in topics:
            if topic in subject_lower:
                parsed_data['topics'].append(topic)
        
        urls = self.extract_urls(body)
        parsed_data['urls'] = [url for url in urls if 'linkedin.com' in url]
        
        article_urls = [url for url in urls if '/pulse/' in url or '/posts/' in url]
        parsed_data['statistics']['article_count'] = len(article_urls)
        
        body_text = self.clean_text(body)
        
        update_count_match = re.search(r'(\d+)\s+(?:updates?|posts?|articles?)', body_text, re.IGNORECASE)
        if update_count_match:
            parsed_data['statistics']['total_updates'] = int(update_count_match.group(1))
        
        return parsed_data
    
    def parse_linkedin_email(self, sender, subject, body, date):
        sender_lower = sender.lower()
        
        if 'jobalerts-noreply@linkedin.com' in sender_lower:
            return self.parse_job_alerts(subject, body, date)
        elif 'jobs-noreply@linkedin.com' in sender_lower:
            return self.parse_jobs_noreply(subject, body, date)
        elif 'jobs-listings@linkedin.com' in sender_lower:
            return self.parse_jobs_listings(subject, body, date)
        elif 'messages-noreply@linkedin.com' in sender_lower:
            return self.parse_messages(subject, body, date)
        elif 'notifications-noreply@linkedin.com' in sender_lower:
            return self.parse_notifications(subject, body, date)
        elif 'updates-noreply@linkedin.com' in sender_lower:
            return self.parse_updates(subject, body, date)
        else:
            return {
                'sender_type': 'unknown',
                'email_type': 'Unknown LinkedIn Email',
                'subject': self.clean_text(subject),
                'date': date,
                'sender': sender
            }
    
    def parse_csv_data(self, csv_path):
        linkedin_emails = []
        parsed_results = []
        
        try:
            csv.field_size_limit(500000)  # Increase field size limit
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'linkedin' in row.get('EMAIL_SENDER', '').lower():
                        linkedin_emails.append(row)
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return []
        
        for email in linkedin_emails:
            result = self.parse_linkedin_email(
                email.get('EMAIL_SENDER', ''),
                email.get('EMAIL_SUBJECT', ''),
                email.get('EMAIL_BODY', ''),
                email.get('EMAIL_DATE', '')
            )
            parsed_results.append(result)
        
        return parsed_results
    
    def show_examples(self, csv_path, num_examples=3):
        parsed_data = self.parse_csv_data(csv_path)
        
        if not parsed_data:
            print("No LinkedIn emails found in the CSV file.")
            return
        
        sender_type_examples = {}
        for data in parsed_data:
            sender_type = data['sender_type']
            if sender_type not in sender_type_examples:
                sender_type_examples[sender_type] = []
            if len(sender_type_examples[sender_type]) < num_examples:
                sender_type_examples[sender_type].append(data)
        
        print("=== LinkedIn Email Parsing Examples ===\n")
        
        for sender_type, examples in sender_type_examples.items():
            print(f"--- {sender_type.upper()} EMAILS ---")
            for i, example in enumerate(examples, 1):
                print(f"\nExample {i}:")
                print(json.dumps(example, indent=2, ensure_ascii=False))
            print("\n" + "="*50 + "\n")
        
        print(f"Total LinkedIn emails processed: {len(parsed_data)}")
        print(f"Sender types found: {list(sender_type_examples.keys())}")


def main():
    parser = LinkedInEmailParser()
    
    csv_path = "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/SERHATKEDU_MAIL_OUTPUTS.csv"
    
    print("Now testing with real CSV data...\n")
    parser.show_examples(csv_path, num_examples=2)


if __name__ == "__main__":
    main()