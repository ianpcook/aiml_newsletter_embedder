from typing import Optional
import logging
from datetime import datetime

from .email_fetcher import EmailFetcher
from .content_splitter import ContentSplitter
from ...core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class NewsletterProcessor:
    def __init__(
        self,
        email_address: str,
        output_file: str,
        error_file: str,
        check_interval: int
    ):
        self.email_address = email_address
        self.output_file = output_file
        self.error_file = error_file
        self.check_interval = check_interval
        self.fetcher = EmailFetcher(email_address)
        self.splitter = ContentSplitter()

    async def process_emails(self) -> int:
        """Process new newsletter emails"""
        try:
            self.fetcher.connect()
            logger.info("Connected to email server")
            
            emails = self.fetcher.fetch_emails(settings.EMAIL_LABEL, self.output_file)
            logger.info(f"Fetched {len(emails)} new emails")
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for email in emails:
                try:
                    if not email.get('body'):
                        logger.warning(f"Skipping email {email.get('id')} - No body content")
                        skipped_count += 1
                        continue
                        
                    try:
                        sections = self.splitter.parse(email['body'])
                        if not sections:
                            logger.warning(f"Skipping email {email.get('id')} - No sections parsed")
                            skipped_count += 1
                            continue
                            
                        email['sections'] = sections
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error parsing sections for email {email.get('id')}: {str(e)}")
                        error_count += 1
                        continue
                        
                except Exception as e:
                    logger.error(f"Error processing email {email.get('id')}: {str(e)}")
                    error_count += 1
                    continue
            
            # Save processed emails to file
            if len(emails) > 0:
                self.fetcher.save_emails(emails, self.output_file)
                logger.info(f"Email processing summary:")
                logger.info(f"- Successfully processed: {processed_count}")
                logger.info(f"- Skipped: {skipped_count}")
                logger.info(f"- Errors: {error_count}")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Email processing failed: {str(e)}")
            raise
        finally:
            self.fetcher.disconnect()
            logger.info("Disconnected from email server") 