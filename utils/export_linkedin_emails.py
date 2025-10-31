#!/usr/bin/env python3
"""
Export all LinkedIn emails from the main CSV to a separate, organized CSV file.
"""

import csv
import sys
import os
from datetime import datetime

def export_linkedin_emails(input_csv, output_csv):
    """
    Extract all LinkedIn emails and save to a new CSV with organized columns.
    """
    # Increase field size limit
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int / 10)
    
    linkedin_emails = []
    
    print(f"Reading emails from: {input_csv}")
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                sender = row.get('EMAIL_SENDER', '')
                
                # Filter only LinkedIn emails
                if sender and 'linkedin' in sender.lower():
                    # Identify sender type
                    sender_lower = sender.lower()
                    if 'jobalerts-noreply@linkedin.com' in sender_lower:
                        sender_type = 'job_alerts'
                    elif 'jobs-noreply@linkedin.com' in sender_lower:
                        sender_type = 'jobs_noreply'
                    elif 'jobs-listings@linkedin.com' in sender_lower:
                        sender_type = 'jobs_listings'
                    elif 'messages-noreply@linkedin.com' in sender_lower:
                        sender_type = 'messages'
                    elif 'notifications-noreply@linkedin.com' in sender_lower:
                        sender_type = 'notifications'
                    elif 'updates-noreply@linkedin.com' in sender_lower:
                        sender_type = 'updates'
                    else:
                        sender_type = 'other'
                    
                    linkedin_emails.append({
                        'sender_type': sender_type,
                        'sender': sender,
                        'subject': row.get('EMAIL_SUBJECT', ''),
                        'date': row.get('EMAIL_DATE', ''),
                        'body': row.get('EMAIL_BODY', ''),
                        'body_length': len(row.get('EMAIL_BODY', ''))
                    })
    
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    if not linkedin_emails:
        print("No LinkedIn emails found!")
        return
    
    # Sort by date
    linkedin_emails.sort(key=lambda x: x['date'])
    
    # Write to new CSV
    print(f"\nWriting {len(linkedin_emails)} LinkedIn emails to: {output_csv}")
    
    fieldnames = ['sender_type', 'sender', 'subject', 'date', 'body_length', 'body']
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(linkedin_emails)
    
    # Print statistics
    print("\n=== EXPORT STATISTICS ===")
    print(f"Total LinkedIn emails: {len(linkedin_emails)}")
    
    sender_counts = {}
    for email in linkedin_emails:
        sender_type = email['sender_type']
        sender_counts[sender_type] = sender_counts.get(sender_type, 0) + 1
    
    print("\nEmails by sender type:")
    for sender_type, count in sorted(sender_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {sender_type}: {count}")
    
    print(f"\n✅ Export complete: {output_csv}")


if __name__ == "__main__":
    input_csv = "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/SERHATKEDU_MAIL_OUTPUTS.csv"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/linkedin_emails_{timestamp}.csv"
    
    export_linkedin_emails(input_csv, output_csv)

