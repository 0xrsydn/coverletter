from fastapi import HTTPException, Form, Request
import logging
import time
from typing import Dict, Any, Union, Optional

from config import load_config
from modules.errors.exceptions import APIRequestError, ConfigurationError, ValidationError
from modules.rate_limit import limiter
from . import router

# Set up logging
logger = logging.getLogger(__name__)

async def execute_exa_search(exa_client, query: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Execute a search query with the Exa API with retry logic.
    
    Args:
        exa_client: The initialized Exa client
        query: Search query string
        max_retries: Maximum number of retry attempts
        
    Returns:
        Search results from Exa
        
    Raises:
        APIRequestError: If the API call fails after all retries
    """
    # Retry configuration
    retry_delays = [1, 2, 4]  # Exponential backoff
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            search_results = exa_client.search_and_contents(
                query=query,
                num_results=1,
                use_autoprompt=True,
                summary={
                    "query": f"What does {query.split(':')[0].replace('Description of ', '')} do as a company? What are their main products and services?"
                },
                highlights={
                    "numSentences": 3,
                    "highlightsPerUrl": 2,
                    "query": f"Key information about {query.split(':')[0].replace('Description of ', '')} company"
                },
                category="company"  # Add company category filter for better results
            )
            return search_results
            
        except Exception as e:
            last_exception = e
            logger.warning(f"Exa API error (attempt {attempt+1}/{max_retries}): {str(e)}")
            
            # Wait before retrying with exponential backoff
            time.sleep(retry_delays[min(attempt, len(retry_delays)-1)])
    
    # If we get here, all retries failed
    raise APIRequestError(
        message=f"Failed after {max_retries} attempts: {str(last_exception)}",
        service_name="Exa AI",
        details={"query": query, "last_error": str(last_exception)}
    )

async def analyze_company_info(company_name: str) -> Union[str, Dict[str, Any]]:
    """
    Analyze a company based on name input using Exa AI.
    
    Args:
        company_name: Company name to search for
        
    Returns:
        Plain text description of the company
    """
    # Input validation
    if not company_name or not company_name.strip():
        raise ValidationError("Company name cannot be empty", field="company_name")
    
    # Load configuration
    config = load_config()
    exa_client = config["exa"]["client"]
    
    if not exa_client:
        raise ConfigurationError(
            message="Exa AI client not properly configured. Please check your API key.",
            config_item="EXA_API_KEY"
        )

    # Prepare search query for the company
    search_query = f"Description of {company_name} company:"
    
    try:
        # Perform search with retry logic
        search_results = await execute_exa_search(exa_client, search_query)
        
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
            else:
                company_info += f"No detailed summary found for {company_name}.\n\n"
            
            # Add a key highlight if available (just the first one to keep it concise)
            if highlights and len(highlights) > 0:
                company_info += "Additional information:\n"
                company_info += f"{highlights[0].strip()}\n\n"
            
            # Add source
            if source_title or source_url:
                company_info += f"Source: {source_title} ({source_url})"
            
            return company_info
        else:
            logger.warning(f"No results found for company: {company_name}")
            return f"No detailed information found for {company_name}. You might want to include your own knowledge about the company in your cover letter."
    
    except Exception as e:
        # If it's not already an APIRequestError, wrap it
        if not isinstance(e, APIRequestError):
            raise APIRequestError(
                message=f"Error analyzing company: {str(e)}",
                service_name="Exa AI", 
                details={"company_name": company_name, "error_type": type(e).__name__}
            ) from e
        raise

# API Routes
@router.post("/analyze_company", response_model=str)
@limiter.limit(load_config()["rate_limits"]["endpoints"]["analyze_company"])
async def analyze_company_route(
    request: Request,  # Required for rate limiting
    company_name: str = Form(...)
):
    """
    Analyze a company based on name input.
    Returns a plain text description of the company.
    
    Args:
        request: The HTTP request (required for rate limiting)
        company_name: Name of the company to analyze (from form data)
    """
    try:
        if not company_name or not company_name.strip():
            raise ValidationError("Please enter a company name", field="company_name")
            
        company_name = company_name.strip()
        logger.info(f"Analyzing company: {company_name}")

        company_description = await analyze_company_info(company_name)
        return company_description
            
    except Exception as e:
        # Let our global exception handler handle this
        logger.error(f"Error analyzing company: {str(e)}")
        raise 