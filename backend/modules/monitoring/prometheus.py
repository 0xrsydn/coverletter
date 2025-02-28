"""
Prometheus metrics configuration for FastAPI
"""
import time
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client import Counter, Histogram
import logging

logger = logging.getLogger(__name__)

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

def setup_metrics(app):
    """
    Set up Prometheus metrics for the FastAPI application.
    
    Args:
        app: FastAPI application
    """
    # Create instrumentator
    instrumentator = Instrumentator()
    
    # Add default metrics
    instrumentator.add(metrics.latency())
    instrumentator.add(metrics.requests())
    instrumentator.add(metrics.requests_in_progress())
    instrumentator.add(metrics.dependency_timing())
    instrumentator.add(metrics.cpu_usage())
    instrumentator.add(metrics.memory_usage())
    
    # Add custom metrics handler
    @app.get("/metrics")
    async def metrics():
        return instrumentator.expose()
    
    # Expose Prometheus metrics endpoint and instrument app
    instrumentator.instrument(app).expose(app)
    
    logger.info("Prometheus metrics enabled at /metrics")
    
    return instrumentator

class StepTimer:
    """
    Context manager for timing processing steps and recording them in Prometheus
    
    Usage:
        with StepTimer("document_processing"):
            # code to time
    """
    def __init__(self, step_name):
        self.step_name = step_name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        PROCESSING_TIME.labels(step=self.step_name).observe(duration)
        logger.debug(f"Step {self.step_name} completed in {duration:.2f} seconds") 