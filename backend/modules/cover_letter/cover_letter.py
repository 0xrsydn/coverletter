import requests
import logging
import re
from typing import Optional

from config import load_config

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
        raise ValueError("OpenRouter API key not configured")
    
    # Prepare the request to OpenRouter API
    headers = {
        "Authorization": f"Bearer {openrouter_config['api_key']}",
        "Content-Type": "application/json"
    }
    
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
    
    # Make the API request
    try:
        response = requests.post(openrouter_config["api_url"], json=payload, headers=headers)
        response_data = response.json()
        
        # Check for errors in the API response
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response_data}")
            error_message = response_data.get('error', {}).get('message', 'Unknown error')
            raise ValueError(f"Error from OpenRouter API: {error_message}")
        
        # Extract and return the generated cover letter
        cover_letter = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Format the cover letter text before returning
        formatted_cover_letter = format_cover_letter(cover_letter)
        
        return formatted_cover_letter
    
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise ValueError(f"Error generating cover letter: {str(e)}") 