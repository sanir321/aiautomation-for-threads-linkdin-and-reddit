import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import database
from .prompt_builder import build_system_context, build_post_prompt

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KILO_API_URL = "https://api.kilo.ai/api/gateway/v1/chat/completions"

def get_session():
    """Create a requests session with a retry strategy for network resilience."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session

def generate_post(platform: str, trends: list) -> dict:
    """Calls Kilo Gateway to generate a post. Returns dict with content and usage."""
    config = database.get_config()
    api_key = config.get('kilo_api_key')
    model = config.get('model_name', 'openai/gpt-4o-mini')
    
    system_prompt = build_system_context()
    user_prompt = build_post_prompt(platform, trends)
    
    if not api_key:
        logger.warning(f"No API key found for {platform}. Returning mock content.")
        return {
            'content': f"[DRAFT MOCK POST FOR {platform.upper()}]\nThis is a mocked post. No API key found.",
            'usage': {'prompt_tokens': 0, 'completion_tokens': 0},
            'model': 'mock'
        }
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }
    
    session = get_session()
    try:
        logger.info(f"Requesting post generation from Kilo AI for {platform}...")
        response = session.post(KILO_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        post_content = data['choices'][0]['message']['content'].strip()
        usage = data.get('usage', {'prompt_tokens': 0, 'completion_tokens': 0})
        
        logger.info(f"Successfully generated post for {platform} (Usage: {usage})")
        return {
            'content': post_content,
            'usage': usage,
            'model': model
        }
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error during AI generation for {platform}: {e}")
    except requests.exceptions.JSONDecodeError as e:
        logger.error(f"JSON Decode Error during AI generation for {platform}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during AI generation for {platform}: {e}")

    return {
        'content': f"[ERROR - {platform.upper()}] Post generation failed.",
        'usage': {'prompt_tokens': 0, 'completion_tokens': 0},
        'model': model
    }
