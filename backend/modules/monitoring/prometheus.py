"""
Prometheus metrics configuration for FastAPI
"""
import time
import platform
import os
from prometheus_client import Counter, Histogram, Info, REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest
from fastapi import Request, Response
import logging

logger = logging.getLogger(__name__)

# Get application info from environment
APP_NAME = os.getenv("APP_NAME", "cover-letter-api")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "development")

# Custom metrics
COVER_LETTER_GENERATED = Counter(
    "cover_letter_generated_total",
    "Number of cover letters generated",
    ["status"]  # success or error
)

PROCESSING_TIME = Histogram(
    "cover_letter_processing_time_seconds",
    "Time taken to process cover letter generation steps",
    ["step"]  # document_processing, job_analysis, company_analysis, letter_generation
)

API_ERRORS = Counter(
    "external_api_errors_total",
    "Number of errors encountered when calling external APIs",
    ["api_name"]  # openrouter, exa
)

# System information metrics
SYSTEM_INFO = Info(
    "application_info", 
    "Application information"
)

def get_exemplar_value(request: Request):
    """Extract the request ID from the request state to use as an exemplar"""
    try:
        if hasattr(request.state, "request_id"):
            return {"request_id": request.state.request_id}
        return {}
    except:
        return {}

def metrics(request: Request) -> Response:
    """Expose metrics with exemplars in OpenMetrics format"""
    return Response(
        generate_latest(REGISTRY), 
        headers={"Content-Type": CONTENT_TYPE_LATEST}
    )

# Helper functions for incrementing counters with exemplars
def increment_counter_with_exemplar(counter, label_name=None, label_value=None, request_id=None):
    """
    Increment a counter with optional exemplar
    
    Args:
        counter: The Counter object
        label_name: The name of the label (optional)
        label_value: The value of the label (optional)
        request_id: Request ID for exemplar (optional)
    """
    exemplar = {"request_id": request_id} if request_id else None
    
    if label_name and label_value:
        counter.labels(**{label_name: label_value}).inc(exemplar=exemplar)
    else:
        counter.inc(exemplar=exemplar)

class StepTimer:
    """
    Context manager for timing processing steps and recording them in Prometheus
    
    Usage:
        with StepTimer("document_processing"):
            # code to time
    """
    def __init__(self, step_name, request_id=None):
        self.step_name = step_name
        self.start_time = None
        self.request_id = request_id
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Add exemplar if we have a request_id
        exemplar = {}
        if self.request_id:
            exemplar = {"request_id": self.request_id}
            
        PROCESSING_TIME.labels(step=self.step_name).observe(
            duration, 
            exemplar=exemplar
        )
        logger.debug(f"Step {self.step_name} completed in {duration:.2f} seconds") 