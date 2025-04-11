"""
Error handling middleware and utilities.
"""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .exceptions import AppBaseException

# Set up logging
logger = logging.getLogger(__name__)

async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for all unhandled exceptions.
    Converts exceptions to a consistent JSON response format.
    """
    # Get exception details
    error_location = f"{request.method} {request.url.path}"
    exception_type = type(exc).__name__
    exception_msg = str(exc)
    
    # Default error response
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_detail = {
        "error": exception_type,
        "message": exception_msg,
        "path": error_location
    }
    
    # Handle custom application exceptions
    if isinstance(exc, AppBaseException):
        status_code = exc.status_code
        error_detail["message"] = exc.message
        if exc.details:
            error_detail["details"] = exc.details
    
    # Handle FastAPI validation errors
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail["error"] = "ValidationError"
        error_detail["message"] = "Request validation error"
        error_detail["details"] = exc.errors()
    
    # Log the error with appropriate severity
    log_message = f"Error in {error_location}: {exception_type}: {exception_msg}"
    if status_code >= 500:
        logger.error(log_message)
        logger.error(traceback.format_exc())
    else:
        logger.warning(log_message)
    
    # Return consistent JSON response
    return JSONResponse(
        status_code=status_code,
        content=error_detail
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    """
    # Register custom exception handler for all exceptions
    app.add_exception_handler(Exception, exception_handler)
    # Add specific handlers for FastAPI exceptions
    app.add_exception_handler(RequestValidationError, exception_handler) 