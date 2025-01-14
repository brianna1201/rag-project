import datetime as dt
import os
from dotenv import load_dotenv
from pathlib import Path

## Load .env
CWD_PATH = Path(__file__).resolve()
WORKSPACE_PATH = CWD_PATH.parent

env_path = WORKSPACE_PATH / '.env'
print(env_path)

# Load .env
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    raise ValueError("Missing .env file. Please create one in the root directory.")

# For testing, override with .env.test if it exists
test_env_path = WORKSPACE_PATH / '.env.test'
if test_env_path.exists():
    load_dotenv(dotenv_path=test_env_path, override=True)
else:
    raise ValueError("Missing .env.test file. Please create one in the root directory.") 

print(os.getenv('OPENAI_API_KEY'))
print(os.getenv('OPENSEARCH_URL'))
print(os.getenv('OPENSEARCH_ID'))
print(os.getenv('OPENSEARCH_PASSWORD'))