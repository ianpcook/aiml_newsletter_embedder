import os
import asyncio
from newsletter_processor.newsletter_processor import NewsletterProcessor
from newsletter_processor.content_splitter import ContentSplitter

if __name__ == '__main__':
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    user_email = os.getenv('EMAIL_ADDRESS')
    output_file = os.path.abspath(os.path.join(os.getcwd(), 'data', 'newsletter_records.json'))
    error_file = os.path.abspath(os.path.join(os.getcwd(), 'data', 'error_records.json'))
    newsletter_processor = NewsletterProcessor(
        user_email, 
        splitter_class=ContentSplitter,
        output_file=output_file,
        error_file=error_file
    )
    emails = newsletter_processor.fetch_emails()
    # Run the asynchronous code
    asyncio.run(newsletter_processor.process_emails(emails, concurrent_limit=15))
