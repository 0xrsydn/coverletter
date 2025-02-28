import os
from dotenv import load_dotenv
from typing import List

try:
    from exa_py import Exa
except ImportError:
    print("Error: The 'exa_py' package is not installed. Please install it using: pip install exa-py")
    Exa = None

def get_cors_origins() -> List[str]:
    """
    Get the list of allowed CORS origins from environment variable.
    Format: comma-separated list of origins, e.g., "http://localhost:3000,https://example.com"
    
    Returns:
        List of allowed origins or ["*"] as fallback
    """
    origins_str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # If the value is "*", return it as a wildcard
    if origins_str == "*":
        return ["*"]
        
    # Otherwise, split by comma and strip whitespace
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

def load_config():
    """Load and return application configuration from environment variables"""
    # Load environment variables
    load_dotenv()
    
    # Determine the environment
    env = os.getenv("APP_ENV", "development").lower()
    
    config = {
        # Application environment
        "env": env,
        "debug": env != "production",
        
        # CORS configuration
        "cors": {
            "allow_origins": get_cors_origins(),
            "allow_credentials": True,
            "allow_methods": ["*"] if env != "production" else ["GET", "POST"],
            "allow_headers": ["*"],
        },
        
        # Rate limiting configuration - different limits based on environment
        "rate_limits": {
            # Global limit (applied to all endpoints if not overridden)
            "global": "60/minute" if env == "development" else "30/minute",
            
            # Endpoint-specific limits (these override the global limit)
            "endpoints": {
                # Main endpoint - more restricted due to resource usage
                "generate_cover_letter": "10/hour" if env == "development" else "5/hour",
                
                # Analysis endpoints
                "analyze_company": "30/hour" if env == "development" else "15/hour",
                "analyze_job_desc_image": "20/hour" if env == "development" else "10/hour",
            }
        },
        
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
    
    # Initialize Exa client if API key exists and Exa module is available
    if config["exa"]["api_key"] and Exa is not None:
        config["exa"]["client"] = Exa(api_key=config["exa"]["api_key"])
    
    return config 