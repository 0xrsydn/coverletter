import requests
import base64
import logging
import time
from typing import Dict, Any
from fastapi import UploadFile, File, HTTPException

from config import load_config
from modules.errors.exceptions import APIRequestError, ConfigurationError, ValidationError
from . import router

# Set up logging
logger = logging.getLogger(__name__)

async def call_openrouter_api(payload: Dict[str, Any], api_key: str, api_url: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Makes an API call to OpenRouter with retry logic.
    
    Args:
        payload: The request payload
        api_key: OpenRouter API key
        api_url: OpenRouter API URL
        max_retries: Maximum number of retry attempts
        
    Returns:
        The parsed JSON response
        
    Raises:
        APIRequestError: If the API call fails after all retries
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Retry configuration
    retry_delays = [1, 3, 5]  # Delays in seconds between retries
    last_exception = None
    
    # Try the request with retries
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response_data = response.json()
            
            # Check for API errors
            if response.status_code != 200:
                error_message = response_data.get('error', {}).get('message', 'Unknown error')
                logger.warning(f"OpenRouter API error (attempt {attempt+1}/{max_retries}): {error_message}")
                
                # If we've exhausted our retries, raise an exception
                if attempt == max_retries - 1:
                    raise APIRequestError(
                        message=error_message,
                        service_name="OpenRouter",
                        status_code=response.status_code,
                        details={"status_code": response.status_code, "response": response_data}
                    )
                
                # Otherwise, wait and retry
                time.sleep(retry_delays[min(attempt, len(retry_delays)-1)])
                continue
            
            # Success - return the data
            return response_data
            
        except requests.RequestException as e:
            last_exception = e
            logger.warning(f"Request error to OpenRouter API (attempt {attempt+1}/{max_retries}): {str(e)}")
            
            # If we've exhausted our retries, raise an exception
            if attempt == max_retries - 1:
                break
                
            # Otherwise, wait and retry
            time.sleep(retry_delays[min(attempt, len(retry_delays)-1)])
    
    # If we get here, all retries failed
    raise APIRequestError(
        message=f"Failed after {max_retries} attempts: {str(last_exception)}",
        service_name="OpenRouter",
        details={"last_error": str(last_exception)}
    )

async def analyze_job_description_image(image_bytes, content_type):
    """
    Analyze job description image using Gemini 2.0 via OpenRouter API.
    
    Args:
        image_bytes: The binary content of the image file
        content_type: The MIME type of the image
        
    Returns:
        Structured analysis of the job description
    """
    # Validate inputs
    if not image_bytes:
        raise ValidationError("Image data is empty", field="job_desc_image")
        
    if not content_type or not content_type.startswith("image/"):
        raise ValidationError(
            "Invalid content type for image", 
            field="job_desc_image",
            details={"provided_content_type": content_type, "expected": "image/*"}
        )
    
    # Load configuration
    config = load_config()
    openrouter_config = config["openrouter"]
    
    if not openrouter_config["api_key"]:
        raise ConfigurationError(
            message="API key is missing or empty",
            config_item="OPENROUTER_API_KEY"
        )
    
    try:
        # Convert image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Prepare the request to OpenRouter API
        payload = {
            "model": openrouter_config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are an extraction tool that analyzes job description images. Return ONLY the extracted information in a clean, structured format. Do NOT include any introductory phrases, explanations, or meta-commentary like 'Here is the breakdown...' or 'I've analyzed...'. Structure the output as follows:\n\nJOB TITLE: [extracted title]\nCOMPANY: [extracted company]\nLOCATION: [extracted location]\nRESPONSIBILITIES:\n- [responsibility 1]\n- [responsibility 2]\nQUALIFICATIONS:\n- [qualification 1]\n- [qualification 2]\nBENEFITS:\n- [benefit 1]\n- [benefit 2]\n\nIf any section is not found in the image, simply omit that section entirely."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the job description details from this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/{content_type.split('/')[1]};base64,{base64_image}"}}
                    ]
                }
            ]
        }
        
        # Make the API request with retry logic
        response_data = await call_openrouter_api(
            payload=payload,
            api_key=openrouter_config["api_key"],
            api_url=openrouter_config["api_url"]
        )
        
        # Extract and return the analysis
        analysis = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not analysis.strip():
            raise APIRequestError(
                message="Received empty analysis from image",
                service_name="OpenRouter",
                details={"content_type": content_type}
            )
        
        return analysis
    
    except Exception as e:
        # If it's not already an APIRequestError, wrap it
        if not isinstance(e, APIRequestError):
            raise APIRequestError(
                message=f"Error analyzing job description image: {str(e)}",
                service_name="OpenRouter", 
                details={"content_type": content_type, "error_type": type(e).__name__}
            ) from e
        raise

# API Routes
@router.post("/analyze_job_desc_image")
async def analyze_job_desc_image_route(job_desc_image: UploadFile = File(...)):
    """
    Analyze job description image using AI model.
    """
    # Validate file is an image
    if not job_desc_image.content_type.startswith("image/"):
        raise ValidationError(
            "Uploaded file is not an image", 
            field="job_desc_image",
            details={"provided_content_type": job_desc_image.content_type}
        )
    
    try:
        # Read the image file
        image_bytes = await job_desc_image.read()
        
        # Use the service to analyze the job description
        result = await analyze_job_description_image(image_bytes, job_desc_image.content_type)
        logger.info(f"Successfully analyzed job description image. Response length: {len(result)}")
        
        return result
        
    except Exception as e:
        # Let our global exception handler handle this
        logger.error(f"Error analyzing job description image: {str(e)}")
        raise 