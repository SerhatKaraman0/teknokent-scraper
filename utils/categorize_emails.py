#!/usr/bin/env python3
"""
Categorize LinkedIn emails by sender type and subject patterns.
Save one representative HTML sample per category in organized folders.
"""

import csv
import sys
import os
import re
from collections import defaultdict

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
        return 'other'

def extract_subject_pattern(subject):
    """Extract a broad pattern/category from the subject line."""
    if not subject:
        return 'no_subject'
    
    # Decode UTF-8 encoded subjects and normalize
    subject_lower = subject.lower()
    
    # Remove UTF encoding artifacts and special characters
    normalized = re.sub(r'=\?utf-\d+\?[qb]\?', '', subject_lower)  # Remove UTF encoding
    normalized = re.sub(r'\?=', '', normalized)  # Remove encoding end markers
    normalized = re.sub(r'[=\+\-_]+', ' ', normalized)  # Replace special chars with space
    normalized = re.sub(r'\b\d+\+?\b', '', normalized)  # Remove all numbers
    normalized = re.sub(r'\s+', ' ', normalized).strip()  # Clean up spaces
    
    # Broad Job-related patterns (combine similar categories)
    if 'is looking for' in normalized or 'looking for' in normalized:
        return 'job_company_looking_for'
    
    if 'is hiring' in normalized or 'are hiring' in normalized or 'hiring now' in normalized or 'now hiring' in normalized:
        return 'job_company_hiring'
    
    # Job alerts/opportunities (combine all variations)
    if any(keyword in normalized for keyword in ['job', 'jobs', 'opportunities', 'opportunity', 'positions', 'position', 'job alert', 'roles']):
        if 'your top' in normalized or 'top opportunities' in normalized:
            return 'job_top_opportunities'
        return 'job_alerts'
    
    # Message patterns
    if 'confirm' in normalized and 'email' in normalized:
        return 'email_verification'
    if 'invitation' in normalized or 'invited' in normalized or 'invite' in normalized:
        return 'invitations'
    if 'message' in normalized or 'sent you' in normalized:
        return 'direct_messages'
    
    # Update/content patterns (combine similar)
    if 'share' in normalized or 'shared' in normalized or 'thoughts' in normalized:
        return 'content_shared'
    if 'posted' in normalized or 'post' in normalized or 'just posted' in normalized:
        return 'content_posted'
    if 'article' in normalized:
        return 'articles'
    
    # Notification patterns
    if 'viewed' in normalized and 'profile' in normalized:
        return 'profile_views'
    if 'endorsed' in normalized or 'endorsement' in normalized:
        return 'endorsements'
    if 'mentioned' in normalized or 'mention' in normalized:
        return 'mentions'
    if 'connection' in normalized:
        return 'connections'
    
    # Job alert management
    if 'turned off' in normalized or 'turn off' in normalized:
        return 'alert_management'
    if 'continue receiving' in normalized or 'want to continue' in normalized:
        return 'alert_management'
    if 'get more out' in normalized or 'tips' in normalized:
        return 'tips_and_advice'
    
    # LinkedIn learning/premium
    if 'learning' in normalized or 'course' in normalized:
        return 'linkedin_learning'
    if 'premium' in normalized:
        return 'premium_notifications'
    
    # Career advice/events
    if 'career' in normalized or 'event' in normalized or 'webinar' in normalized:
        return 'career_events'
    
    # Network updates
    if 'network' in normalized or 'happened in your' in normalized:
        return 'network_updates'
    
    # Default
    return 'other'

def categorize_emails(csv_path, output_base_dir):
    """
    Categorize emails and save one representative sample per category.
    """
    # Track categories: {sender_type: {subject_pattern: [emails]}}
    categories = defaultdict(lambda: defaultdict(list))
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                sender = row.get('EMAIL_SENDER', '')
                subject = row.get('EMAIL_SUBJECT', '')
                body = row.get('EMAIL_BODY', '')
                date = row.get('EMAIL_DATE', '')
                
                if not sender or 'linkedin' not in sender.lower():
                    continue
                
                sender_type = identify_sender_type(sender)
                subject_pattern = extract_subject_pattern(subject)
                
                categories[sender_type][subject_pattern].append({
                    'sender': sender,
                    'subject': subject,
                    'body': body,
                    'date': date,
                    'sender_type': sender_type,
                    'subject_pattern': subject_pattern
                })
    
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Save one sample per category
    total_saved = 0
    
    for sender_type, patterns in sorted(categories.items()):
        # Create sender type directory
        sender_dir = os.path.join(output_base_dir, sender_type)
        ensure_dir(sender_dir)
        
        print(f"\n{'='*60}")
        print(f"📁 {sender_type.upper()} ({len(patterns)} subject patterns)")
        print(f"{'='*60}")
        
        for subject_pattern, emails in sorted(patterns.items()):
            # Pick the first email as representative
            email = emails[0]
            
            # Create safe filename (remove/replace problematic characters)
            safe_pattern = subject_pattern.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            filename = f"{safe_pattern}.html"
            filepath = os.path.join(sender_dir, filename)
            
            # Save HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(email['body'])
            
            # Save metadata as comment in HTML
            meta_comment = f"""<!--
Category: {sender_type} / {subject_pattern}
Sender: {email['sender']}
Subject: {email['subject']}
Date: {email['date']}
Count: {len(emails)} similar email(s)
-->
"""
            # Prepend metadata
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(meta_comment + '\n' + content)
            
            print(f"  ✅ {subject_pattern}.html ({len(emails)} emails)")
            print(f"     Subject: {email['subject'][:60]}...")
            
            total_saved += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Total: {total_saved} category samples saved")
    print(f"📂 Location: {output_base_dir}")
    print(f"{'='*60}")

def main():
    csv_path = "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/SERHATKEDU_MAIL_OUTPUTS.csv"
    output_base_dir = "/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs/diagnostics"
    
    print("Categorizing LinkedIn emails...")
    print(f"Input: {csv_path}")
    print(f"Output: {output_base_dir}")
    
    categorize_emails(csv_path, output_base_dir)

if __name__ == "__main__":
    main()

