import datetime as dt
import os
from dotenv import load_dotenv
from pathlib import Path

## Load .env
CWD_PATH = Path(__file__).resolve()
WORKSPACE_PATH = CWD_PATH.parent

# Load environment variables with error checking
def load_env_vars():
    # Try loading .env first
    env_path = WORKSPACE_PATH / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # For testing, override with .env.test if it exists
    test_env_path = WORKSPACE_PATH / '.env.test'
    if test_env_path.exists():
        load_dotenv(dotenv_path=test_env_path, override=True)
    
    # Verify required variables
    required_vars = ['OPENAI_API_KEY', 'OPENSEARCH_URL', 'OPENSEARCH_ID', 'OPENSEARCH_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Load environment variables
load_env_vars()

# Set environment variables globally
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENSEARCH_URL = os.getenv('OPENSEARCH_URL')
OPENSEARCH_ID = os.getenv('OPENSEARCH_ID')
OPENSEARCH_PASSWORD = os.getenv('OPENSEARCH_PASSWORD')
OPENSEARCH_AUTH = (OPENSEARCH_ID, OPENSEARCH_PASSWORD)

# Set in os.environ for libraries that read directly from there
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENSEARCH_URL"] = OPENSEARCH_URL
os.environ["OPENSEARCH_ID"] = OPENSEARCH_ID
os.environ["OPENSEARCH_PASSWORD"] = OPENSEARCH_PASSWORD

# OpenSearch Headers
OPENSEARCH_HEADERS = {
    "Content-Type": "application/json",
}

# Translation Configuration
KOREAN_DETECTION_THRESHOLD = 0.5  # Ratio of Korean characters to consider text as Korean
TRANSLATION_MODEL_NAME = "Helsinki-NLP/opus-mt-ko-en"  # MarianMT model for Korean to English translation

# LLM Configuration
LLM_MODEL_NAME = "gpt-4o-mini"  # OpenAI model to use
LLM_TEMPERATURE = 0  # Temperature for LLM responses

# Available OpenSearch indices used in the application:
# - chat-history: Stores chat history between users and the chatbot
# - user-photos: Stores user uploaded photos
# - schedule: Stores user schedules
# - topics: Stores news topics
# - news: Stores news articles