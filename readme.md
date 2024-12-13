# Email Parser and Vector Database Loader
This Python application demonstrates how to parse emails from a specified Gmail account using labels, and loads them into a vector database (Weaviate) for improved search capabilities. 

It uses OpenAI GPT-3.5 to help parse ambiguous parts of the email and provides parallelism for better performance. The application utilizes Docker for easy deployment.

## Requirements
- Python 3.9+
- Poetry (Python dependency management)
- Docker
- Docker Compose
- OpenAI API key
- Gmail account with App Password configured (regular password won't work with IMAP)

## Installation

1. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Start Docker services:
```bash
docker-compose build
docker-compose up -d
```

## Configuration
1. Create a .env file in the project root directory with the following contents:
```
OPENAI_API_KEY=your_openai_api_key
EMAIL_ADDRESS=your_email_address
EMAIL_PASSWORD=your_email_app_password
```
Replace the values with:
- your_openai_api_key: Your OpenAI API key
- your_email_address: Your Gmail address
- your_email_app_password: Your Gmail App Password (see Development Setup below)

2. Configure the docker-compose.yaml file as needed, including setting the desired ports and volume mappings.

## Development Setup

1. Configure Gmail for IMAP access:
   - Go to your Google Account settings
   - Navigate to Security > 2-Step Verification
   - Scroll to the bottom and click on "App passwords"
   - Select "Mail" and your device
   - Click "Generate"
   - Use this 16-character password as your EMAIL_PASSWORD in .env

2. Set up VS Code:
   - Install the Python extension if you haven't already
   - Open the command palette (Cmd/Ctrl + Shift + P)
   - Run "Python: Select Interpreter"
   - Choose the Poetry environment (it should be listed as "Poetry (EmailVectorDB)")

3. Create a test label in Gmail:
   - Open Gmail
   - Create a new label (e.g., "TestEmails")
   - Apply this label to a few test emails

## Testing

1. Quick test in VS Code:
```python
# test_email_fetch.py
from email_fetcher import EmailFetcher
from dotenv import load_dotenv
import os

def test_fetch():
    load_dotenv()
    email = os.getenv('EMAIL_ADDRESS')
    fetcher = EmailFetcher(email)
    
    try:
        # Connect to Gmail
        fetcher.connect()
        print("✓ Successfully connected to Gmail")
        
        # Try to fetch emails with your test label
        emails = fetcher.fetch_emails("TestEmails", "test_output.json")
        print(f"✓ Found {len(emails)} emails with label 'TestEmails'")
        
        # Print first email subject if any were found
        if emails:
            print(f"✓ Sample email subject: {emails[0]['subject']}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    finally:
        fetcher.disconnect()
        print("✓ Successfully disconnected")

if __name__ == "__main__":
    test_fetch()
```

2. Run the test:
```bash
poetry run python test_email_fetch.py
```

3. Debug in VS Code:
   - Set breakpoints in your code by clicking to the left of line numbers
   - Press F5 or click Run > Start Debugging
   - Select "Python File" as the debugger
   - The debugger will stop at your breakpoints

## Usage
```bash
poetry run ./load_data.sh
```
This script will:
- Fetch new emails from your Gmail account with the specified label
- Use OpenAI GPT-3.5 to parse ambiguous parts of the email, with parallelism for better performance
- Create a Weaviate newsletter schema
- Load the parsed data into Weaviate

The parsed emails will be loaded into the Weaviate vector database, enabling improved search capabilities.

## Example Searches
I have included an example Jupyter Notebook, example_searches.ipynb, which demonstrates various search queries and their results when run against the Weaviate database. The notebook contains real-world examples that showcase the power of the vector search enabled by loading parsed email data into Weaviate.

To run the notebook:
```bash
poetry run jupyter notebook example_searches.ipynb
```

Here is a sample query and its results from the notebook:

Query:
```python
run_query("framework for dealing with llm prompts")
```

Results:
```json
[
 {
  "header": "MODEL-TUNING VIA PROMPTS: IMPROVING ADVERSARIAL ROBUSTNESS IN NLP (15 MINUTE READ)",
  "links": ["https://arxiv.org/abs/2303.07320?utm_source=tldrai"],
  "received_date": "2023-03-15T13:13:19Z",
  "text_content": "The MVP method demonstrates surprising gains in adversarial robustness, improving performance against adversarial word-level synonym substitutions by an average of 8% over standard methods, and even outperforming state-of-art defenses by 3.5%. By modifying the input with a prompt template instead of modifying the model by appending an MLP head, MVP achieves better results in downstream tasks while maintaining clean accuracy."
 }
]
```






