# https://youtu.be/K21BSZPFIjQ
"""
Extract selected mails from your gmail account

1. Make sure you enable IMAP in your gmail settings
(Log on to your Gmail account and go to Settings, See All Settings, and select
 Forwarding and POP/IMAP tab. In the "IMAP access" section, select Enable IMAP.)

2. If you have 2-factor authentication, gmail requires you to create an application
specific password that you need to use. 
Go to your Google account settings and click on 'Security'.
Scroll down to App Passwords under 2 step verification.
Select Mail under Select App. and Other under Select Device. (Give a name, e.g., python)
The system gives you a password that you need to use to authenticate from python.

"""

import sys
import os
import imaplib
import email

from custom_logging.logger import logger
from .email_parser import LinkedInEmailParser
from dotenv import load_dotenv

load_dotenv()

# Get credentials from environment variables
user = os.getenv("INBOX_SCRAPER_MAIL")
password = os.getenv("INBOX_SCRAPER_PWD")
parser = LinkedInEmailParser()

# Validate that credentials are provided
if not user or not password:
    logger.error("Email credentials not found in environment variables")
    logger.error("Please set INBOX_SCRAPER_MAIL and INBOX_SCRAPER_PWD in your .env file")
    exit(1)

logger.info(f"Using email: {user}")

imap_url = 'imap.gmail.com'

logger.info("making imap connection")

my_mail = imaplib.IMAP4_SSL(imap_url)

logger.info("initiate login")

my_mail.login(user, password)
logger.info("login is passed")

# Select the Inbox to fetch messages
my_mail.select('Inbox')

#Define Key and Value for email search
#For other keys (criteria): https://gist.github.com/martinrusev/6121028#file-imap-search
key = 'FROM'
value = 'jobs-noreply@linkedin.com>'
_, data = my_mail.search(None, key, value)  #Search for emails with specific key and value

mail_id_list = data[0].split()  #IDs of all emails that we want to fetch 

msgs = [] # empty list to capture all messages
#Iterate through messages and extract data into the msgs list
logger.info(f"Total mail id: {len(mail_id_list)}")


for num in mail_id_list:
    typ, data = my_mail.fetch(num, '(RFC822)') #RFC822 returns whole message (BODY fetches just body)
    msgs.append(data)

logger.info("messages are appended")
#Now we have all messages, but with a lot of details
#Let us extract the right text and print on the screen

#In a multipart e-mail, email.message.Message.get_payload() returns a 
# list with one item for each part. The easiest way is to walk the message 
# and get the payload on each part:
# https://stackoverflow.com/questions/1463074/how-can-i-get-an-email-messages-text-content-using-python

# NOTE that a Message object consists of headers and payloads.

logger.info("reading messages")

for idx, msg in enumerate(msgs[::-1]):
    logger.info(f"Reading the {idx}th message")
    if idx == 5:
        break
    for response_part in msg:
        if type(response_part) is tuple:
            my_msg=email.message_from_bytes((response_part[1]))
            print("_________________________________________")
            
            result = parser.parse_email(str(my_msg))
            
            jobs, len_jobs = parser.deduplicated_jobs(result)
            recommended_jobs, len_recommended_jobs = parser.deduplicated_recommended_jobs(result, jobs)
            # print ("subj:", my_msg['subject'])
            # print ("from:", my_msg['from'])
            # print ("body:", my_msg['body'])
            print("--------------JOBS--------------")
            print(f"TOTAL JOBS: {len_jobs}")
            print(jobs)
            
            print("--------------RECOMMENDED JOBS--------------")
            print(f"TOTAL RECOMMENDED JOBS: {len_recommended_jobs}") 
            print(recommended_jobs)
            
            print("_________________________________________")
            for part in my_msg.walk():  
                #print(part.get_content_type())
                if part.get_content_type() == 'text/plain':
                    print (part.get_payload())
            