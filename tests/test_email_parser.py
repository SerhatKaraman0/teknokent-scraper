import pytest
import csv
import json
import sys
import os

# Add the parent directory to the path to import the email_automation module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from email_automation.email_parser import LinkedInEmailParser


class TestLinkedInEmailParser:
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing"""
        return LinkedInEmailParser()
    
    @pytest.fixture
    def real_csv_data(self):
        """Load real CSV data for testing"""
        csv_path = '/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/SERHATKEDU_MAIL_OUTPUTS.csv'
        
        # Increase field size limit significantly
        csv.field_size_limit(10000000)
        emails = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    sender = row.get('EMAIL_SENDER', '')
                    if 'linkedin' in sender.lower():
                        # Skip emails with extremely large bodies that cause issues
                        body = row.get('EMAIL_BODY', '')
                        if len(body) > 500000:  # Skip emails larger than 500KB
                            continue
                            
                        emails.append({
                            'sender': sender,
                            'subject': row.get('EMAIL_SUBJECT', ''),
                            'body': body,
                            'date': row.get('EMAIL_DATE', '')
                        })
                        
                        # Limit to 50 emails for testing
                        if len(emails) >= 50:
                            break
                            
        except Exception as e:
            pytest.skip(f"Could not load CSV file: {e}")
            
        return emails
    
    def test_linkedin_senders_distribution(self, real_csv_data):
        """Test to see what LinkedIn senders we actually have"""
        senders = {}
        for email in real_csv_data:
            sender = email['sender']
            if sender not in senders:
                senders[sender] = 0
            senders[sender] += 1
        
        print("\n=== REAL LINKEDIN SENDERS FOUND ===")
        for sender, count in sorted(senders.items()):
            print(f"{sender}: {count} emails")
        
        assert len(senders) > 0, "No LinkedIn emails found"
    
    def test_job_listings_parsing(self, parser, real_csv_data):
        """Test job listings parsing with real data"""
        job_listing_emails = [
            email for email in real_csv_data 
            if 'jobs-listings' in email['sender'].lower()
        ]
        
        print(f"\n=== TESTING {len(job_listing_emails)} REAL JOB LISTING EMAILS ===")
        
        for i, email in enumerate(job_listing_emails[:5]):  # Test first 5
            print(f"\n--- REAL EMAIL {i+1} ---")
            print(f"Sender: {email['sender']}")
            print(f"Subject: {email['subject']}")
            print(f"Body preview: {email['body'][:200]}...")
            
            result = parser.parse_linkedin_email(
                email['sender'],
                email['subject'],
                email['body'],
                email['date']
            )
            
            print(f"\nPARSING RESULT:")
            print(json.dumps(result, indent=2))
            
            # Assertions
            assert result['sender_type'] == 'jobs_listings'
            assert 'jobs' in result
            # Every job must have all required fields
            for job in result['jobs']:
                assert job.get('company'), f"Missing company for job {job}"
                assert job.get('position'), f"Missing position for job {job}"
                assert job.get('location'), f"Missing location for job {job}"
                assert job.get('job_url'), f"Missing job_url for job {job}"
    
    def test_job_alerts_parsing(self, parser, real_csv_data):
        """Test job alerts parsing with real data"""
        job_alert_emails = [
            email for email in real_csv_data 
            if 'jobalerts-noreply' in email['sender'].lower()
        ]
        
        print(f"\n=== TESTING {len(job_alert_emails)} REAL JOB ALERT EMAILS ===")
        
        for i, email in enumerate(job_alert_emails[:2]):  # Test first 2
            print(f"\n--- REAL EMAIL {i+1} ---")
            print(f"Sender: {email['sender']}")
            print(f"Subject: {email['subject']}")
            
            result = parser.parse_linkedin_email(
                email['sender'],
                email['subject'],
                email['body'],
                email['date']
            )
            
            print(f"\nPARSING RESULT:")
            print(json.dumps(result, indent=2))
            
            assert result['sender_type'] == 'job_alerts'
            # If jobs discovered in alerts, enforce required fields
            for job in result.get('jobs', []):
                assert job.get('company'), f"Missing company for job {job}"
                assert job.get('position'), f"Missing position for job {job}"
                assert job.get('location'), f"Missing location for job {job}"
                assert job.get('job_url'), f"Missing job_url for job {job}"
    
    def test_messages_parsing(self, parser, real_csv_data):
        """Test messages parsing with real data"""
        message_emails = [
            email for email in real_csv_data 
            if 'messages-noreply' in email['sender'].lower()
        ]
        
        print(f"\n=== TESTING {len(message_emails)} REAL MESSAGE EMAILS ===")
        
        for i, email in enumerate(message_emails[:2]):  # Test first 2
            print(f"\n--- REAL EMAIL {i+1} ---")
            print(f"Sender: {email['sender']}")
            print(f"Subject: {email['subject']}")
            
            result = parser.parse_linkedin_email(
                email['sender'],
                email['subject'],
                email['body'],
                email['date']
            )
            
            print(f"\nPARSING RESULT:")
            print(json.dumps(result, indent=2))
            
            assert result['sender_type'] == 'messages'
    
    def test_all_linkedin_types(self, parser, real_csv_data):
        """Test parsing all types of LinkedIn emails"""
        type_counts = {}
        
        print(f"\n=== TESTING ALL {len(real_csv_data)} REAL LINKEDIN EMAILS ===")
        
        for email in real_csv_data:
            result = parser.parse_linkedin_email(
                email['sender'],
                email['subject'],
                email['body'],
                email['date']
            )
            
            sender_type = result['sender_type']
            if sender_type not in type_counts:
                type_counts[sender_type] = 0
            type_counts[sender_type] += 1
        
        print(f"\n=== PARSING RESULTS SUMMARY ===")
        for sender_type, count in sorted(type_counts.items()):
            print(f"{sender_type}: {count} emails")
        
        assert len(type_counts) > 0, "No emails were parsed"