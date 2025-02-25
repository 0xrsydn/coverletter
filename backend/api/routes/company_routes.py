from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
import logging
from services.company_service import analyze_company_info
from typing import Optional

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define request model for company analysis
class CompanyRequest(BaseModel):
    company_input: str

@router.post("/analyze_company")
async def analyze_company(
    company_request: Optional[CompanyRequest] = None,
    company_input: Optional[str] = Form(None)
):
    """
    Analyze a company based on name or URL input.
    Returns a plain text description of the company.
    
    Accepts both JSON body or form data with company_input field.
    """
    try:
        # Get input from either JSON body or form data
        input_value = company_input if company_input is not None else (
            company_request.company_input if company_request else None
        )
        
        if not input_value:
            return "Please enter a company name or URL"
            
        input_value = input_value.strip()
        logger.info(f"Analyzing company: {input_value}")

        company_info = await analyze_company_info(input_value)
        return company_info
            
    except Exception as e:
        logger.error(f"Error analyzing company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing company: {str(e)}") 