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
            for email in emails:
                try:
                    if email.get('body'):
                        sections = self.splitter.parse(email['body'])
                        email['sections'] = sections
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing email {email.get('id')}: {str(e)}")
                    continue
            
            # Save processed emails to file
            if processed_count > 0:
                self.fetcher.save_emails(emails, self.output_file)
                logger.info(f"Saved {processed_count} processed emails to {self.output_file}")
            
            return processed_count

        except Exception as e:
            logger.error(f"Email processing failed: {str(e)}")
            raise
        finally:
            self.fetcher.disconnect()
            logger.info("Disconnected from email server") 