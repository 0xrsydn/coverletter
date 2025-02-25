import os
from dotenv import load_dotenv
from exa_py import Exa

def load_config():
    """Load and return application configuration from environment variables"""
    # Load environment variables
    load_dotenv()
    
    config = {
        # OpenRouter API configuration
        "openrouter": {
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model": os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001"),
            "api_url": "https://openrouter.ai/api/v1/chat/completions"
        },
        
        # Exa AI configuration
        "exa": {
            "api_key": os.getenv("EXA_API_KEY"),
            "client": None  # Will be initialized if API key exists
        }
    }
    
    # Initialize Exa client if API key exists
    if config["exa"]["api_key"]:
        config["exa"]["client"] = Exa(api_key=config["exa"]["api_key"])
    
    return config 