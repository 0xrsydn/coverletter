"""
Custom exception classes for better error handling.
"""
from typing import Optional, Dict, Any

class AppBaseException(Exception):
    """Base exception for all application exceptions"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class APIRequestError(AppBaseException):
    """Exception for errors when calling external APIs"""
    def __init__(self, message: str, service_name: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        super().__init__(
            message=f"{service_name} API Error: {message}", 
            status_code=status_code, 
            details=details
        )


class DocumentProcessingError(AppBaseException):
    """Exception for errors when processing documents"""
    def __init__(self, message: str, doc_type: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        self.doc_type = doc_type
        super().__init__(
            message=f"Error processing {doc_type} document: {message}", 
            status_code=status_code, 
            details=details
        )


class ValidationError(AppBaseException):
    """Exception for input validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        self.field = field
        field_prefix = f"Invalid {field}: " if field else "Validation error: "
        super().__init__(
            message=f"{field_prefix}{message}", 
            status_code=status_code, 
            details=details
        )


class ConfigurationError(AppBaseException):
    """Exception for configuration errors"""
    def __init__(self, message: str, config_item: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.config_item = config_item
        super().__init__(
            message=f"Configuration error for {config_item}: {message}", 
            status_code=status_code, 
            details=details
        ) 