import requests
import logging
import re
import time
from typing import Optional, Dict, Any

from config import load_config
from modules.errors.exceptions import APIRequestError, ConfigurationError

# Set up logging
logger = logging.getLogger(__name__)

def format_cover_letter(text: str) -> str:
    """
    Format the cover letter text by replacing escaped newlines and cleaning up spacing.
    
    Args:
        text: The raw cover letter text
        
    Returns:
        Properly formatted cover letter text
    """
    # Replace escaped newlines with actual newlines
    formatted_text = text.replace('\\n', '\n')
    
    # Handle other escaped characters
    formatted_text = formatted_text.replace('\\"', '"').replace("\\'", "'").replace('\\t', '\t')
    
    # Clean up excessive newlines
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    
    # Remove any JSON artifacts
    if formatted_text.startswith('"') and formatted_text.endswith('"'):
        formatted_text = formatted_text[1:-1]
    
    return formatted_text

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

async def generate_cover_letter(resume_text: str, job_description: str, company_info: str) -> str:
    """
    Generate a personalized cover letter using OpenRouter API with CV, job description, and company info.
    
    Args:
        resume_text: Extracted text from the user's CV/resume
        job_description: Job description text
        company_info: Information about the company
        
    Returns:
        Generated cover letter text
    """
    # Load configuration
    config = load_config()
    openrouter_config = config["openrouter"]
    
    if not openrouter_config["api_key"]:
        raise ConfigurationError(
            message="API key is missing or empty",
            config_item="OPENROUTER_API_KEY"
        )
    
    # Create a prompt for the cover letter generation
    system_prompt = """You are an expert cover letter writer with experience in HR and recruitment. 
Your task is to create a personalized, professional cover letter based on the provided CV/resume, 
job description, and company information. Follow these guidelines:

1. Use a professional business letter format.
2. Personalize the letter for the specific job and company.
3. Highlight relevant skills and experiences from the CV that match the job requirements.
4. Keep the tone professional but conversational.
5. Be concise - aim for about 350-450 words.
6. Include a strong opening paragraph, 2-3 body paragraphs, and a closing paragraph.
7. Don't include the date or physical addresses.

Begin with "Dear Hiring Manager," unless a specific name is provided.
End with "Sincerely," followed by a placeholder for the applicant's name.
"""

    user_prompt = f"""Generate a personalized cover letter based on the following information:

CV/RESUME INFORMATION:
{resume_text}

JOB DESCRIPTION:
{job_description}

COMPANY INFORMATION:
{company_info}

Please write a tailored cover letter that highlights the relevant skills and experiences from my CV 
that match the job requirements, while also showing knowledge of and enthusiasm for the company.
"""
    
    # Prepare the payload for the OpenRouter API
    payload = {
        "model": openrouter_config["model"],
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.6,
    }
    
    try:
        # Call OpenRouter API with retry logic
        response_data = await call_openrouter_api(
            payload=payload,
            api_key=openrouter_config["api_key"],
            api_url=openrouter_config["api_url"]
        )
        
        # Extract the generated cover letter
        cover_letter = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Handle empty response
        if not cover_letter.strip():
            raise APIRequestError(
                message="Received empty response",
                service_name="OpenRouter",
                details={"response": response_data}
            )
        
        # Format the cover letter text before returning
        formatted_cover_letter = format_cover_letter(cover_letter)
        
        return formatted_cover_letter
    
    except Exception as e:
        # If it's not already an APIRequestError, wrap it
        if not isinstance(e, APIRequestError):
            raise APIRequestError(
                message=f"Error generating cover letter: {str(e)}",
                service_name="Cover Letter Generator", 
                details={"error_type": type(e).__name__}
            ) from e
        raise 