from fastapi import HTTPException
import logging
from typing import Dict, Any, Union

from config import load_config
from . import router

# Set up logging
logger = logging.getLogger(__name__)

async def analyze_company_info(company_name: str) -> Union[str, Dict[str, Any]]:
    """
    Analyze a company based on name input using Exa AI.
    
    Args:
        company_name: Company name to search for
        
    Returns:
        Plain text description of the company
    """
    # Load configuration
    config = load_config()
    exa_client = config["exa"]["client"]
    
    if not exa_client:
        raise HTTPException(status_code=500, detail="Exa AI client not properly configured. Please check your API key.")

    # Prepare search query for the company
    search_query = f"Description of {company_name} company:"
    
    # Perform web search for company info with "company" category
    search_results = exa_client.search_and_contents(
        query=search_query,
        num_results=1,
        use_autoprompt=True,
        summary={
            "query": f"What does {company_name} do as a company? What are their main products and services?"
        },
        highlights={
            "numSentences": 3,
            "highlightsPerUrl": 2,
            "query": f"Key information about {company_name} company"
        },
        category="company"  # Add company category filter for better results
    )

    # Process the search results into plain text
    if search_results.results:
        best_result = search_results.results[0]
        summary = getattr(best_result, "summary", "")
        highlights = getattr(best_result, "highlights", [])
        source_title = getattr(best_result, "title", "")
        source_url = getattr(best_result, "url", "")
        
        # Format the information into a readable text
        company_info = f"## {company_name.upper()} ##\n\n"
        
        # Add the summary if available
        if summary:
            company_info += f"{summary}\n\n"
        
        # Add a key highlight if available (just the first one to keep it concise)
        if highlights and len(highlights) > 0:
            company_info += "Additional information:\n"
            company_info += f"{highlights[0].strip()}\n\n"
        
        # Add source
        if source_title or source_url:
            company_info += f"Source: {source_title} ({source_url})"
        
        return company_info
    else:
        return f"No information found for {company_name}."

# API Routes
@router.post("/analyze_company", response_model=str)
async def analyze_company_route(company_name: str):
    """
    Analyze a company based on name input.
    Returns a plain text description of the company.
    
    Args:
        company_name: Name of the company to analyze
    """
    try:
        if not company_name or not company_name.strip():
            raise HTTPException(status_code=400, detail="Please enter a company name")
            
        company_name = company_name.strip()
        logger.info(f"Analyzing company: {company_name}")

        company_description = await analyze_company_info(company_name)
        return company_description
            
    except Exception as e:
        logger.error(f"Error analyzing company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing company: {str(e)}") 