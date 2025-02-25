from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from services.company_service import analyze_company_info

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define request model for company analysis
class CompanyRequest(BaseModel):
    company_input: str

@router.post("/analyze_company")
async def analyze_company(company_request: CompanyRequest):
    """
    Analyze a company based on name or URL input.
    Returns a plain text description of the company.
    """
    try:
        company_input = company_request.company_input.strip()
        logger.info(f"Analyzing company: {company_input}")

        if not company_input:
            return "Please enter a company name or URL"

        company_info = await analyze_company_info(company_input)
        return company_info
            
    except Exception as e:
        logger.error(f"Error analyzing company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing company: {str(e)}") 