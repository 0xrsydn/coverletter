"""
Rate limiting implementation for the API.
Uses slowapi to implement IP-based rate limiting with standard headers.
"""
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Set up logging
logger = logging.getLogger(__name__)

# Initialize limiter with IP-based rate limiting
limiter = Limiter(key_func=get_remote_address)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns a user-friendly error message with standard headers.
    """
    response = JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": str(exc),
            "detail": "Too many requests. Please try again later."
        }
    )
    
    # Log the rate limit exceeded event
    logger.warning(
        f"Rate limit exceeded: IP={request.client.host}, "
        f"path={request.url.path}, method={request.method}"
    )
    
    return response

def setup_rate_limiting(app: FastAPI, config: Dict[str, Any]) -> None:
    """
    Configure rate limiting for the FastAPI application.
    
    Args:
        app: The FastAPI application instance
        config: Configuration dict containing rate limit settings
    """
    # Store limiter in app state (required by slowapi)
    app.state.limiter = limiter
    
    # Add rate limiting middleware
    app.add_middleware(SlowAPIMiddleware)
    
    # Add custom exception handler for rate limit exceeded errors
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    # Log rate limiting configuration
    env = config.get("env", "development")
    limits = config.get("rate_limits", {})
    logger.info(f"Rate limiting enabled in {env} environment")
    logger.info(f"Global rate limit: {limits.get('global', 'Not set')}")
    
    for endpoint, limit in limits.get("endpoints", {}).items():
        logger.info(f"Endpoint rate limit - {endpoint}: {limit}") 