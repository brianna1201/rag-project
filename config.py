import datetime as dt

import os
from dotenv import load_dotenv
from pathlib import Path

## Load .env
CWD_PATH = Path(__file__).resolve().parent
WORKSPACE_PATH = CWD_PATH.parent

load_dotenv(dotenv_path= WORKSPACE_PATH / '.env')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# OpenSearch Configuration
OPENSEARCH_URL = os.getenv('OPENSEARCH_URL')  # Your OpenSearch domain URL

# OpenSearch Authentication
OPENSEARCH_ID = os.getenv('OPENSEARCH_ID')
OPENSEARCH_PASSWORD = os.getenv('OPENSEARCH_PASSWORD')
OPENSEARCH_AUTH = (OPENSEARCH_ID, OPENSEARCH_PASSWORD)  # Basic auth credentials for OpenSearch

# OpenSearch Headers
OPENSEARCH_HEADERS = {
    "Content-Type": "application/json",
    # Add any additional headers required for OpenSearch
}

# Available OpenSearch indices used in the application:
# - chat-history: Stores chat history between users and the chatbot
# - user-photos: Stores user uploaded photos
# - schedule: Stores user schedules
# - topics: Stores news topics
# - news: Stores news articles