import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

def pytest_sessionstart(session):
    """
    Called after the Session object has been created and before performing collection
    and entering the run test loop.
    """
    # Load test environment variables
    test_env_path = Path(__file__).parent / '.env.test'
    if test_env_path.exists():
        load_dotenv(dotenv_path=test_env_path, override=True)  # override=True to ensure test values take precedence
    
    # Set environment variables globally (similar to config.py)
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY', '')
    os.environ["OPENSEARCH_URL"] = os.getenv('OPENSEARCH_URL', '')
    os.environ["OPENSEARCH_ID"] = os.getenv('OPENSEARCH_ID', '')
    os.environ["OPENSEARCH_PASSWORD"] = os.getenv('OPENSEARCH_PASSWORD', '')
    
    # Verify required variables are set
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please create a tests/.env.test file with your test API key."
        ) 