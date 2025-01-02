import imaplib
import email
import os
import json
from dotenv import load_dotenv
from email.header import decode_header, make_header
import logging
from datetime import datetime
logger = logging.getLogger(__name__)

class EmailFetcher:
    """
    EmailFetcher is a class to fetch emails from a specified email address.
    It connects to the Gmail server using IMAP, searches for emails from a specific sender,
    and retrieves the email content.
    """
    def __init__(self, email_address: str, password: str = None) -> None:
        if not password:
            load_dotenv()
            self.password = password or os.getenv('EMAIL_PASSWORD')
        else:
            self.password = password
        self.email_address = email_address        
        self.mail = None

    def connect(self) -> None:
        try:
            self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
            self.mail.login(self.email_address, self.password)
            self.mail.select('inbox')
        except imaplib.IMAP4.error as e:
            raise ConnectionError(f"Failed to connect to email server: {str(e)}")
    
    def disconnect(self) -> None:
        if self.mail:
            self.mail.logout()

    def _get_text_from_email(self, msg) -> bytes:
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                return part.get_payload(decode=True)

    def load_existing_emails(self, path: str) -> list[dict]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                existing_emails = json.load(f)
                logger.info(f"Loaded {len(existing_emails)} existing emails from {path}")
                # Log some sample IDs for debugging
                if existing_emails:
                    # Normalize existing IDs
                    for email in existing_emails:
                        if 'id' in email:
                            email['id'] = email['id'].strip('<>').strip()
                    sample_ids = [email['id'] for email in existing_emails[:3]]
                    logger.debug(f"Sample existing email IDs: {sample_ids}")
                return existing_emails
        return []

    def get_message_ids(self, mail, email_ids):
        message_ids = {}
        for email_id in email_ids:
            _, response = mail.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
            message_id_header = response[0][1].decode()
            try:
                # Handle both Message-ID and Message-Id formats
                if 'Message-ID:' in message_id_header:
                    message_id = message_id_header.split('Message-ID:', 1)[1].strip()
                elif 'Message-Id:' in message_id_header:
                    message_id = message_id_header.split('Message-Id:', 1)[1].strip()
                else:
                    logger.warning(f"No Message-ID found in header: {message_id_header}")
                    continue
                
                # Clean the ID by removing angle brackets and whitespace
                message_ids[email_id] = message_id.strip('<>').strip()
                logger.debug(f"Successfully parsed Message-ID: {message_ids[email_id]}")
            except Exception as e:
                logger.warning(f"Error parsing Message-ID from header: {message_id_header}. Error: {str(e)}")
                continue
        return message_ids

    def fetch_emails(self, label: str, processed_email_output_path: str) -> list[dict]:
        """Fetch emails from specified label"""
        try:
            # Gmail labels need to be accessed with their full path including parent labels
            status, response = self.mail.select(f'"{label}"')
            if status != 'OK':
                logger.error(f'Failed to select label "{label}". Please ensure the label exists and is accessible.')
                raise ValueError(f'Label "{label}" not found or inaccessible')
            
            # Search for all emails in the label
            status, response = self.mail.search(None, 'ALL')
            email_binary_ids = response[0].split()
            email_ids = self.get_message_ids(self.mail, email_binary_ids)
            email_list = []

            existing_emails = self.load_existing_emails(processed_email_output_path)
            existing_ids = {email['id'] for email in existing_emails}
            
            if existing_ids:
                sample_existing = list(existing_ids)[:3]
                logger.info(f"Sample existing IDs: {sample_existing}")
            
            new_ids = [k for k, v in email_ids.items() if v not in existing_ids]
            logger.info(f"Found {len(new_ids)} new emails out of {len(email_ids)} total emails in label '{label}'")
            
            if new_ids:
                sample_new = [email_ids[k] for k in new_ids[:3]]
                logger.info(f"Sample new email IDs: {sample_new}")

            for i, email_id in enumerate(new_ids):
                email_data = {}
                _, msg_data = self.mail.fetch(email_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                msg_id = msg['Message-ID']
                if msg_id:
                    msg_id = msg_id.strip('<>').strip()
                
                if msg_id in existing_ids:
                    logger.debug(f"Skipping already processed email with ID: {msg_id}")
                    continue

                logger.debug(f"Processing new email {i+1}/{len(new_ids)} with ID: {msg_id}")

                email_data['id'] = msg_id
                email_data['subject'] = str(make_header(decode_header(msg['Subject'])))
                email_data['from'] = msg['From']
                date_str = msg['date'].replace(" (UTC)", "")  # Remove (UTC) if present
                email_data['date'] = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z").isoformat()

                body = self._get_text_from_email(msg)
                if body:
                    email_data['body'] = body.decode()

                # Mark the email as read by setting the Seen flag
                self.mail.store(email_id, '+FLAGS', '\\Seen')
                email_list.append(email_data)

            return email_list

        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise

    def save_emails(self, emails: list[dict], path: str) -> None:
        """Save emails to the output file, merging with existing emails"""
        existing_emails = self.load_existing_emails(path)
        
        # Create a dictionary of existing emails by ID for faster lookup
        existing_dict = {email['id']: email for email in existing_emails}
        
        # Update existing emails and add new ones
        for email in emails:
            if email['id'] in existing_dict:
                existing_dict[email['id']].update(email)
            else:
                existing_dict[email['id']] = email
        
        # Convert back to list and sort by date
        all_emails = list(existing_dict.values())
        all_emails.sort(key=lambda x: x['date'], reverse=True)
        
        # Save to file
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(all_emails, f, indent=2)
        logger.info(f"Saved {len(all_emails)} emails to {path}")
