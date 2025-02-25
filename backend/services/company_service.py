from urllib.parse import urlparse
import logging
from config import load_config

# Set up logging
logger = logging.getLogger(__name__)

async def analyze_company_info(company_input):
    """
    Analyze a company based on name or URL input using Exa AI.
    
    Args:
        company_input: Company name or URL
        
    Returns:
        Plain text description of the company
    """
    # Load configuration
    config = load_config()
    exa_client = config["exa"]["client"]
    
    if not exa_client:
        return "Exa AI client not properly configured. Please check your API key."

    # Determine if input is a URL or company name
    is_url = company_input.startswith(('http://', 'https://'))
    
    # Prepare search query based on input type
    if is_url:
        # Extract domain name for better search results
        domain = urlparse(company_input).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        search_query = f"{domain} company about us description"
        
        # Also add a search specifically for this URL
        try:
            url_search_results = exa_client.search_and_contents(
                query="",
                urls=[company_input],
                num_results=1,
                text=True
            )
            url_content = url_search_results.results[0].text if url_search_results.results else ""
        except Exception as e:
            logger.warning(f"Error fetching URL content: {str(e)}")
            url_content = ""
    else:
        search_query = f"{company_input} company about us description"
        url_content = ""

    # Perform web search for company info
    search_results = exa_client.search_and_contents(
        query=search_query,
        num_results=3,
        use_autoprompt=True,
        text=True
    )

    # Format the search results into a readable company description
    company_info = ""
    
    # If we have direct URL content, prioritize that
    if url_content:
        # Take the first 1000 characters to keep it concise
        trimmed_content = url_content[:1000] + "..." if len(url_content) > 1000 else url_content
        company_info = f"Information about {company_input} from their website:\n\n{trimmed_content}"
    # Otherwise, use the search results
    elif search_results.results:
        # Take the most relevant result (first one)
        best_result = search_results.results[0]
        result_text = getattr(best_result, 'text', None)
        
        if result_text:
            # If the result has text content, use that
            trimmed_content = result_text[:1000] + "..." if len(result_text) > 1000 else result_text
            company_info = f"Information about {company_input}:\n\n{trimmed_content}"
        else:
            # Otherwise just provide the title and URL
            title = getattr(best_result, 'title', 'No title available')
            url = getattr(best_result, 'url', 'No URL available')
            company_info = f"Information about {company_input}:\n\n{title}\nURL: {url}"
    else:
        company_info = f"No detailed information found for {company_input}. Please try a different company name or URL."
    
    return company_info 