#!/usr/bin/env python3
"""
Dump raw HTML from different LinkedIn email types for analysis.
Creates separate files for updates, messages, and other email types.
"""

import csv
import sys
import os
import re
from datetime import datetime

# Increase field size limit for large email bodies
maxInt = sys.maxsize
while True:
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt/10)

def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def identify_sender_type(sender):
    """Identify the type of LinkedIn email."""
    if not sender:
        return 'unknown'
    sender_lower = sender.lower()
    if 'messages-noreply@linkedin.com' in sender_lower:
        return 'messages'
    elif 'updates-noreply@linkedin.com' in sender_lower:
        return 'updates'
    elif 'notifications-noreply@linkedin.com' in sender_lower:
        return 'notifications'
    elif 'jobs-listings@linkedin.com' in sender_lower:
        return 'jobs_listings'
    elif 'jobs-noreply@linkedin.com' in sender_lower:
        return 'jobs_noreply'
    elif 'jobalerts-noreply@linkedin.com' in sender_lower:
        return 'job_alerts'
    else:
        return 'unknown'

def dump_email_samples(csv_path, output_dir, email_types=None, samples_per_type=3):
    """
    Dump raw HTML from different email types.
    
    Args:
        csv_path: Path to the CSV file with emails
        output_dir: Directory to save the raw HTML files
        email_types: List of email types to extract (None = all non-job types)
        samples_per_type: Number of samples to dump per type
    """
    ensure_dir(output_dir)
    
    # Default to non-job email types
    if email_types is None:
        email_types = ['messages', 'updates', 'notifications', 'unknown']
    
    # Track samples per type
    samples_collected = {email_type: 0 for email_type in email_types}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                sender = row.get('EMAIL_SENDER', '')
                subject = row.get('EMAIL_SUBJECT', '')
                body = row.get('EMAIL_BODY', '')
                date = row.get('EMAIL_DATE', '')
                
                sender_type = identify_sender_type(sender)
                
                # Skip if not in requested types or already have enough samples
                if sender_type not in email_types:
                    continue
                if samples_collected[sender_type] >= samples_per_type:
                    continue
                
                # Increment counter
                samples_collected[sender_type] += 1
                sample_num = samples_collected[sender_type]
                
                # Save raw HTML
                html_filename = f"{sender_type}_{sample_num}_raw.html"
                html_path = os.path.join(output_dir, html_filename)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(body)
                
                # Save metadata
                meta_filename = f"{sender_type}_{sample_num}_meta.txt"
                meta_path = os.path.join(output_dir, meta_filename)
                
                with open(meta_path, 'w', encoding='utf-8') as f:
                    f.write(f"Sender: {sender}\n")
                    f.write(f"Subject: {subject}\n")
                    f.write(f"Date: {date}\n")
                    f.write(f"Type: {sender_type}\n")
                    f.write(f"\nBody Length: {len(body)} characters\n")
                
                print(f"✅ Saved {sender_type} sample {sample_num}")
                
                # Check if we're done with all types
                if all(count >= samples_per_type for count in samples_collected.values()):
                    break
    
    except Exception as e:
        print(f"Error: {e}")
        return
    
    print(f"\n{'='*50}")
    print("Summary:")
    for email_type, count in samples_collected.items():
        print(f"  {email_type}: {count} samples")
    print(f"{'='*50}")
    print(f"\nFiles saved to: {output_dir}")

def main():
    csv_path = "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/SERHATKEDU_MAIL_OUTPUTS.csv"
    output_dir = "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/diagnostics"
    
    # Dump samples from non-job email types
    email_types = ['messages', 'updates', 'notifications', 'unknown']
    
    print("Dumping raw HTML samples from LinkedIn emails...")
    print(f"Looking for types: {', '.join(email_types)}")
    print(f"Samples per type: 3\n")
    
    dump_email_samples(csv_path, output_dir, email_types=email_types, samples_per_type=3)

if __name__ == "__main__":
    main()

