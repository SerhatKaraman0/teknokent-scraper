# https://youtu.be/K21BSZPFIjQ
"""
1. Make sure you enable IMAP in your gmail settings
(Log on to your Gmail account and go to Settings, See All Settings, and select
 the Forwarding and POP/IMAP tab and make sure IMAP is enabled.)

2. If you have 2-factor authentication, gmail requires you to create an application
specific password that you need to use.
"""

import imaplib
import os
import re
import email
from datetime import datetime
from email.utils import parsedate_tz, mktime_tz
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing
from functools import partial
import threading
from queue import Queue
import numpy as np

import time
from custom_logging.logger import logger
from .email_parser import LinkedInEmailParser
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

NUM_THREADS = 2  # Very conservative to avoid Gmail rate limits
NUM_PROCESSES = os.cpu_count() or 1  

logger.info(f"System detected: {NUM_PROCESSES} CPU cores")
logger.info(f"Using {NUM_THREADS} threads for email fetching and {NUM_PROCESSES} processes for email processing")

def fetch_single_email(args):
    """Worker function to fetch a single email - with shared connection"""
    shared_connection, email_id = args
    
    try:
        typ, msg_data = shared_connection.fetch(email_id, '(RFC822)')
        if typ == 'OK' and msg_data and msg_data[0]:
            return email_id, msg_data
        else:
            logger.warning(f"Failed to fetch mail id {email_id}: {typ}")
            return email_id, None
            
    except Exception as e:
        logger.error(f"Error fetching email {email_id}: {e}")
        return email_id, None

def process_single_email(msg_data):
    """Worker function to process a single email - CPU intensive"""
    try:
        if not msg_data:
            return None
            
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                my_msg = email.message_from_bytes(response_part[1])
                
                mail = {}
                mail["EMAIL_SENDER"] = my_msg["from"]
                mail["EMAIL_SUBJECT"] = my_msg["subject"]
                
                # Collect all payloads and their content types
                bodies = []
                content_types = []
                for part in my_msg.walk():
                    if part.get_content_type() is not None and part.get_content_maintype() != 'multipart':
                        payload = part.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            body = payload.decode('utf-8', errors='ignore')
                        else:
                            body = str(payload)
                        bodies.append(body)
                        content_types.append(part.get_content_type())
                mail["EMAIL_BODY"] = bodies
                mail["EMAIL_CONTENT_TYPE"] = content_types
                
                mail["EMAIL_PAYLOAD"] = str(my_msg)
                return mail
                
        return None
    except Exception as e:
        logger.error(f"Error processing email: {e}")
        return None

class InboxScraper():
    def __init__(self, max_threads=None, max_processes=None):
        self.user = os.getenv("WORKMAIL_INBOX_SCRAPER_MAIL")
        self.password = os.getenv("WORKMAIL_INBOX_SCRAPER_PWD")
        if not self.user or not self.password:
            raise ValueError("WORKMAIL_INBOX_SCRAPER_MAIL and WORKMAIL_INBOX_SCRAPER_PWD environment variables must be set and non-empty.")
        
        # Initialize with NumPy arrays for better performance
        self.email_data = {
            'senders': np.array([], dtype=object),
            'subjects': np.array([], dtype=object),
            'bodies': np.array([], dtype=object),
            'payloads': np.array([], dtype=object),
            'content_types': np.array([], dtype=object),
            'dates': np.array([], dtype=object),
            'timestamps': np.array([], dtype=object)
        }
        
        self.df = pd.DataFrame(columns=["EMAIL_SENDER", "EMAIL_SUBJECT", "EMAIL_BODY", "EMAIL_PAYLOAD", "EMAIL_CONTENT_TYPE", "EMAIL_DATE", "EMAIL_TIMESTAMP"])
        self.imap_url = "imap.gmail.com"
        self.my_mail = imaplib.IMAP4_SSL(self.imap_url)
        
        # Set threading/processing limits
        self.max_threads = max_threads or NUM_THREADS
        self.max_processes = max_processes or NUM_PROCESSES
        
        logger.info(f"InboxScraper initialized with {self.max_threads} threads and {self.max_processes} processes")
        logger.info("Using NumPy arrays for optimized data processing")
    
    def initiate_mail_login(self):
        try:
            logger.info("Started initial_mail_login function")
            if not self.user or not self.password:
                raise ValueError("User and password must be set")
            self.my_mail.login(self.user, self.password)
            self.my_mail.select('Inbox')
            logger.info("Successful initial_mail_login function")
        except Exception as e:
            raise Exception(f"Failed process due to {e}")
        
    def access_mail(self, key: str, value = None):
        try:
            OPTIONS = [
                "ALL",
                "ANSWERED",
                "DELETED",
                "DRAFT",
                "FLAGGED",
                "FROM",
                "KEYWORD",
                "LARGER",
                "NEW",
                "NOT",
                "OLD",
                "ON",
                "RECENT",
                "SEEN",
                "SENTBEFORE",
                "SENTON",
                "SENTSINCE",
                "SINCE",
                "SMALLER",
                "SUBJECT",
                "TEXT",
                "TO",
                "UID",
                "UNANSWERED",
                "UNDELETED",
                "UNDRAFT",
                "UNFLAGGED",
                "UNKEYWORD",
                "UNSEEN"
            ]
            logger.info("access_mail function started")
            
            if key not in OPTIONS:
                raise Exception(f"Invalid key {key}. Accepted keys: {OPTIONS}")
            
            if value:
                typ, data = self.my_mail.search(None, key, value)
            else:
                typ, data = self.my_mail.search(None, key)
                
            logger.info(f"Search completed with {len(data[0].split())} results")
            
            return data
        except Exception as e:
            raise Exception(f"Failed process due to {e}")

    def access_msgs_parallel(self, data):
        """Sequential email fetching with NumPy optimization and SSL error handling"""
        try:
            logger.info("Started access_msgs_parallel function with NumPy optimization")
            
            # Convert to NumPy array for vectorized operations
            mail_id_list = np.array(data[0].split(), dtype=object)
            logger.info(f"mail_id_list extracted - found {len(mail_id_list)} emails")
            
            if len(mail_id_list) == 0:
                return np.array([], dtype=object)
            
            # Pre-allocate NumPy array for messages (much faster than list.append)
            msgs = np.empty(len(mail_id_list), dtype=object)
            valid_count = 0
            failed_count = 0
            ssl_errors = 0
            
            # Fetch emails sequentially using optimized for loop
            logger.info("Fetching emails sequentially with NumPy arrays and SSL error handling...")
            
            with tqdm(total=len(mail_id_list), desc="📧 Fetching emails (NumPy + SSL safe)", unit="email") as pbar:
                for i in range(len(mail_id_list)):
                    email_id = mail_id_list[i]
                    try:
                        typ, msg_data = self.my_mail.fetch(email_id, '(RFC822)')
                        if typ == 'OK' and msg_data and msg_data[0]:
                            msgs[valid_count] = msg_data
                            valid_count += 1
                        else:
                            logger.warning(f"Failed to fetch mail id {email_id}: {typ}")
                            failed_count += 1
                            
                    except Exception as e:
                        error_str = str(e)
                        if 'ssl' in error_str.lower() or 'eof' in error_str.lower():
                            ssl_errors += 1
                            # Try to reconnect on SSL errors
                            if ssl_errors % 10 == 0:  # Reconnect every 10 SSL errors
                                logger.warning(f"SSL reconnection attempt after {ssl_errors} errors...")
                                try:
                                    self.my_mail.close()
                                    self.my_mail.logout()
                                    self.my_mail = imaplib.IMAP4_SSL(self.imap_url)
                                    if self.user and self.password:
                                        self.my_mail.login(self.user, self.password)
                                        self.my_mail.select('Inbox')
                                        logger.info("SSL reconnection successful")
                                except:
                                    logger.error("SSL reconnection failed")
                        
                        logger.error(f"Error fetching email {email_id}: {e}")
                        failed_count += 1
                    
                    pbar.update(1)
            
            # Trim array to actual size (remove empty slots)
            valid_msgs = msgs[:valid_count] if valid_count > 0 else np.array([], dtype=object)
            
            # Save valid_msgs as backup in case processing fails
            self.save_valid_msgs_backup(valid_msgs)
            
            logger.info(f"Successfully fetched {valid_count} emails, failed: {failed_count}, SSL errors: {ssl_errors}")
            return valid_msgs
            
        except Exception as e:
            raise Exception(f"Failed process due to {e}")
    
    def prepare_dataframe_parallel(self, msgs):
        """NumPy-optimized dataframe preparation with vectorized operations"""
        try:
            logger.info("Started prepare_dataframe_parallel function with NumPy optimization")
            
            if len(msgs) == 0:
                logger.warning("No messages to process")
                return self.df
            
            # Pre-allocate NumPy arrays for email data (much faster than lists)
            num_msgs = len(msgs)
            senders = np.empty(num_msgs, dtype=object)
            subjects = np.empty(num_msgs, dtype=object)
            bodies = np.empty(num_msgs, dtype=object)
            payloads = np.empty(num_msgs, dtype=object)
            content_types = np.empty(num_msgs, dtype=object)
            dates = np.empty(num_msgs, dtype=object)
            timestamps = np.empty(num_msgs, dtype=object)
            
            valid_count = 0
            
            logger.info("Processing emails with NumPy vectorized operations...")
            
            with tqdm(total=num_msgs, desc="⚡ Processing emails (NumPy vectorized)", unit="email") as pbar:
                for i in range(num_msgs):
                    msg_data = msgs[i]
                    try:
                        if msg_data is not None:
                            for response_part in msg_data:
                                if isinstance(response_part, tuple):
                                    my_msg = email.message_from_bytes(response_part[1])
                                    
                                    # Direct array assignment (faster than dict operations)
                                    senders[valid_count] = my_msg["from"]
                                    subjects[valid_count] = my_msg["subject"]
                                    payloads[valid_count] = str(my_msg)
                                    
                                    # Extract email date and timestamp
                                    date_tuple = parsedate_tz(my_msg.get("Date", ""))
                                    if date_tuple:
                                        # Convert to timestamp
                                        timestamp = mktime_tz(date_tuple)
                                        # Convert to readable datetime
                                        email_datetime = datetime.fromtimestamp(timestamp)
                                        dates[valid_count] = email_datetime.strftime("%Y-%m-%d %H:%M:%S")
                                        timestamps[valid_count] = timestamp
                                    else:
                                        dates[valid_count] = "Unknown"
                                        timestamps[valid_count] = 0
                                    
                                    body_found = False
                                    for part in my_msg.walk():
                                        payload = part.get_payload(decode=True)
                                        if isinstance(payload, bytes):
                                            bodies[valid_count] = payload.decode('utf-8', errors='ignore')
                                        else:
                                            bodies[valid_count] = str(payload)
                                        content_types[valid_count] = part.get_content_type()
                                        body_found = True
                                    
                                    if not body_found:
                                        bodies[valid_count] = ""
                                        content_types[valid_count] = "unknown"
                                    
                                    valid_count += 1
                                    break
                                    
                    except Exception as e:
                        logger.error(f"Error processing email {i}: {e}")
                    
                    pbar.update(1)
            
            if valid_count > 0:
                logger.info(f"Creating DataFrame from {valid_count} processed emails with NumPy")
                
                # Create DataFrame from NumPy arrays (much faster than from list of dicts)
                # Create DataFrame from NumPy arrays (much faster than from list of dicts)
                email_dict = {
                    "EMAIL_SENDER": senders[:valid_count],
                    "EMAIL_SUBJECT": subjects[:valid_count],
                    "EMAIL_BODY": bodies[:valid_count],
                    "EMAIL_PAYLOAD": payloads[:valid_count],
                    "EMAIL_CONTENT_TYPE": content_types[:valid_count],
                    "EMAIL_DATE": dates[:valid_count],
                    "EMAIL_TIMESTAMP": timestamps[:valid_count]
                }
                self.df = pd.DataFrame(email_dict)
                logger.info(f"NumPy-optimized DataFrame created with shape: {self.df.shape}")
            else:
                logger.warning("No emails were successfully processed")
            
            return self.df
            
        except Exception as e:
            logger.error(f"Failed to prepare dataframe: {e}")
            raise Exception(f"Failed process due to {e}")

    def save_valid_msgs_backup(self, valid_msgs):
        """Save valid_msgs as backup in case processing fails"""
        try:
            import pickle
            backup_dir = os.path.join(os.getcwd(), "email_outputs", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"valid_msgs_backup_{timestamp}.pkl")
            
            with open(backup_file, 'wb') as f:
                pickle.dump(valid_msgs, f)
            
            logger.info(f"Backup saved: {backup_file} ({len(valid_msgs)} messages)")
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")
            return None

    def load_valid_msgs_backup(self, backup_file):
        """Load valid_msgs from backup file"""
        try:
            import pickle
            with open(backup_file, 'rb') as f:
                valid_msgs = pickle.load(f)
            
            logger.info(f"Backup loaded: {backup_file} ({len(valid_msgs)} messages)")
            return valid_msgs
            
        except Exception as e:
            logger.error(f"Failed to load backup: {e}")
            return None

    def save_to_csv(self, output_path="/Users/user/Desktop/Projects/teknokent_scraper/email_automation/email_outputs", filename="SERHATKARAMANWORKMAIL_MAIL_OUTPUTS.csv"):
        """Save the processed emails to CSV file"""
        try:
            logger.info("Saving to csv started.")
            
            full_output_path = os.path.join(os.getcwd(), output_path)
            os.makedirs(full_output_path, exist_ok=True)
            
            file_path = os.path.join(full_output_path, filename)
            self.df.to_csv(file_path, index=False)
            
            logger.info(f"File saved at {file_path}")
            logger.info(f"Saved {len(self.df)} emails to CSV")
            
            return file_path
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            raise Exception(f"Failed to save CSV due to {e}")

    def get_performance_stats(self):
        """Get performance statistics for the current dataset"""
        try:
            stats = {
                'total_emails': len(self.df),
                'memory_usage_mb': self.df.memory_usage(deep=True).sum() / 1024**2,
                'data_types': dict(self.df.dtypes),
                'null_counts': dict(self.df.isnull().sum())
            }
            
            logger.info(f"Performance Stats - Emails: {stats['total_emails']}, Memory: {stats['memory_usage_mb']:.2f}MB")
            return stats
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}

    def get_emails_by_date_range(self, start_date, end_date):
        """Filter emails by date range"""
        try:
            if 'EMAIL_DATE' not in self.df.columns:
                logger.warning("Email dates not available")
                return pd.DataFrame()
            
            # Convert date strings to datetime for filtering
            self.df['EMAIL_DATE_PARSED'] = pd.to_datetime(self.df['EMAIL_DATE'], errors='coerce')
            
            # Filter by date range
            mask = (self.df['EMAIL_DATE_PARSED'] >= start_date) & (self.df['EMAIL_DATE_PARSED'] <= end_date)
            filtered_df = self.df.loc[mask]
            
            logger.info(f"Found {len(filtered_df)} emails between {start_date} and {end_date}")
            return filtered_df
            
        except Exception as e:
            logger.error(f"Failed to filter by date range: {e}")
            return pd.DataFrame()

    def get_email_stats_by_date(self):
        """Get email statistics grouped by date"""
        try:
            if 'EMAIL_DATE' not in self.df.columns:
                logger.warning("Email dates not available")
                return {}
            
            # Convert to datetime and extract date only
            self.df['EMAIL_DATE_PARSED'] = pd.to_datetime(self.df['EMAIL_DATE'], errors='coerce')
            self.df['EMAIL_DATE_ONLY'] = self.df['EMAIL_DATE_PARSED'].dt.date
            
            # Group by date and count
            date_stats = self.df.groupby('EMAIL_DATE_ONLY').size().sort_index(ascending=False)
            
            stats = {
                'emails_per_day': date_stats.to_dict(),
                'busiest_day': date_stats.idxmax() if not date_stats.empty else None,
                'max_emails_per_day': date_stats.max() if not date_stats.empty else 0,
                'date_range': {
                    'earliest': date_stats.index.min() if not date_stats.empty else None,
                    'latest': date_stats.index.max() if not date_stats.empty else None
                }
            }
            
            logger.info(f"Email date stats: {stats['max_emails_per_day']} max emails on {stats['busiest_day']}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get email stats by date: {e}")
            return {}

if __name__ == "__main__":
    scraper = InboxScraper()
    scraper.initiate_mail_login()
    data = scraper.access_mail("ALL")
    msgs = scraper.access_msgs_parallel(data)
    df = scraper.prepare_dataframe_parallel(msgs)
    file_path = scraper.save_to_csv()
    print(f"Processing complete. Saved to: {file_path}")