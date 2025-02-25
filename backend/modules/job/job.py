import requests
import base64
import logging
from fastapi import UploadFile, File, HTTPException

from config import load_config
from . import router

# Set up logging
logger = logging.getLogger(__name__)

async def analyze_job_description_image(image_bytes, content_type):
    """
    Analyze job description image using Gemini 2.0 via OpenRouter API.
    
    Args:
        image_bytes: The binary content of the image file
        content_type: The MIME type of the image
        
    Returns:
        Structured analysis of the job description
    """
    # Load configuration
    config = load_config()
    openrouter_config = config["openrouter"]
    
    if not openrouter_config["api_key"]:
        raise ValueError("OpenRouter API key not configured")
    
    # Convert image to base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    
    # Prepare the request to OpenRouter API
    headers = {
        "Authorization": f"Bearer {openrouter_config['api_key']}",
        "Content-Type": "application/json"
    }
    
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
    
    # Make the API request
    response = requests.post(openrouter_config["api_url"], json=payload, headers=headers)
    response_data = response.json()
    
    # Check for errors in the API response
    if response.status_code != 200:
        logger.error(f"OpenRouter API error: {response_data}")
        error_message = response_data.get('error', {}).get('message', 'Unknown error')
        raise ValueError(f"Error from OpenRouter API: {error_message}")
    
    # Extract and return the analysis
    analysis = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    return analysis

# API Routes
@router.post("/analyze_job_desc_image")
async def analyze_job_desc_image_route(job_desc_image: UploadFile = File(...)):
    """
    Analyze job description image using AI model.
    """
    # Validate file is an image
    if not job_desc_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")
    
    try:
        # Read the image file
        image_bytes = await job_desc_image.read()
        
        # Use the service to analyze the job description
        result = await analyze_job_description_image(image_bytes, job_desc_image.content_type)
        logger.info(f"Successfully analyzed job description image. Response length: {len(result)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing job description image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing job description: {str(e)}") 