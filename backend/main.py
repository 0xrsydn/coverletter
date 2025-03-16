from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import logging
import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, UploadFile, File, Request
from typing import Optional
import time
from contextvars import ContextVar

# Internal imports
from config import load_config
from modules.document.document import extract_docs
from modules.job.job import analyze_job_description_image, analyze_job_requirements
from modules.company.company import analyze_company_info
from modules.cover_letter.cover_letter import generate_cover_letter
from modules.errors import register_exception_handlers
from modules.errors.exceptions import ValidationError, DocumentProcessingError
# Add monitoring imports
from modules.monitoring import setup_metrics
from modules.monitoring.prometheus import StepTimer, COVER_LETTER_GENERATED, API_ERRORS, increment_counter_with_exemplar
from modules.rate_limit import setup_rate_limiting, limiter

# Import routers
from modules.job import router as job_router
from modules.company import router as company_router
from modules.document import router as document_router
from modules.cover_letter import router as cover_letter_router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a context var to store request ID in logging context
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")

# Custom Log Filter to inject request ID into log records
class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx_var.get() or "-"
        return True

# Add request ID to log format
for handler in logging.getLogger().handlers:
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - [%(request_id)s] - %(levelname)s - %(message)s'
    ))
    handler.addFilter(RequestIDFilter())

# Load configuration
config = load_config()

# Create request ID middleware
async def request_id_middleware(request: Request, call_next):
    """
    Middleware that adds a unique request ID to each request.
    This ID can be used to correlate logs and metrics.
    """
    request_id = str(uuid.uuid4())
    # Store request ID in request state for access in route handlers
    request.state.request_id = request_id
    
    # Store request ID in context var for logging
    token = request_id_ctx_var.set(request_id)
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        # Reset context var
        request_id_ctx_var.reset(token)

# Create FastAPI app
app = FastAPI(
    title="Cover Letter Generator API",
    description="API for generating personalized cover letters based on CV and job description",
    version="1.0.0",
)

# Add request ID middleware
app.middleware("http")(request_id_middleware)

# Register exception handlers
register_exception_handlers(app)

# Configure CORS with environment-based settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=config["cors"]["allow_origins"],
    allow_credentials=config["cors"]["allow_credentials"],
    allow_methods=config["cors"]["allow_methods"],
    allow_headers=config["cors"]["allow_headers"],
)

# Setup rate limiting
setup_rate_limiting(app, config)

# Setup Prometheus metrics
setup_metrics(app)

# Include routers
app.include_router(job_router)
app.include_router(company_router)
app.include_router(document_router)
app.include_router(cover_letter_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Cover Letter Generator API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    import platform
    import psutil
    
    # Get system information
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "api_version": app.version,
        "environment": config["env"],
        "system": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory_info.percent,
            "disk_usage_percent": disk_info.percent
        },
        "timestamp": time.time()
    }

# Main cover letter generation endpoint
@app.post("/generate_cover_letter", response_class=PlainTextResponse)
@limiter.limit(config["rate_limits"]["endpoints"]["generate_cover_letter"])
async def generate_cover_letter_main(
    request: Request,  # Required for rate limiting
    cv_file: UploadFile = File(...),
    job_desc_text: Optional[str] = Form(None),
    job_desc_image: UploadFile = File(None),
    company_name: Optional[str] = Form(None)
):
    """
    Main entry point for generating a cover letter from the frontend form.
    This consolidated endpoint handles:
    1. CV document parsing
    2. Job description (text or image)
    3. Company information (optional)
    4. Cover letter generation
    """
    start_time = time.time()
    logger.info("Starting cover letter generation process")
    request_id = getattr(request.state, "request_id", None)
    
    try:
        # Step 1: Process CV document
        with StepTimer("document_processing", request_id):
            cv_text = await extract_docs(cv_file)
            logger.info(f"CV processed: {len(cv_text)} characters extracted")
        
        # Step 2: Process job description
        job_description = None
        with StepTimer("job_analysis", request_id):
            if job_desc_text:
                job_description = job_desc_text
                logger.info("Job description processed from text input")
            elif job_desc_image:
                job_description = await analyze_job_description_image(job_desc_image)
                logger.info("Job description processed from image")
            else:
                raise ValidationError("Either job description text or image must be provided")
                
            # Analyze job requirements
            job_requirements = analyze_job_requirements(job_description)
            logger.info(f"Job requirements extracted: {len(job_requirements)} requirements found")
        
        # Step 3: Get company information if provided
        company_info = None
        if company_name:
            with StepTimer("company_analysis", request_id):
                company_info = analyze_company_info(company_name)
                logger.info(f"Company information retrieved for {company_name}")
        
        # Step 4: Generate cover letter
        with StepTimer("letter_generation", request_id):
            cover_letter = generate_cover_letter(
                cv_text=cv_text,
                job_description=job_description,
                company_info=company_info
            )
            logger.info(f"Cover letter generated: {len(cover_letter)} characters")
        
        generation_time = time.time() - start_time
        logger.info(f"Cover letter generated successfully in {generation_time:.2f} seconds")
        
        # Record success in metrics
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "success", request_id)
        
        return cover_letter
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        
        # Record error in metrics
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "error", request_id)
        
        if isinstance(e, ValidationError) or isinstance(e, DocumentProcessingError):
            raise e
        raise HTTPException(status_code=500, detail=f"Error generating cover letter: {str(e)}")

@app.post("/api/generate-cover-letter")
@limiter.limit(config["rate_limits"]["endpoints"]["generate_cover_letter"])
async def generate_cover_letter_endpoint(
    request: Request,
    resume: UploadFile = File(...),
    job_desc: str = Form(...),
    company: Optional[str] = Form(None),
    app_id: Optional[str] = Form(None)
):
    """
    Generate a cover letter based on the uploaded resume and job description.
    Optionally, provide company information and an application ID.
    """
    try:
        logger.info("Cover letter generation request received")
        start_time = time.time()
        
        # Step 1: Extract resume data
        logger.info("Step 1: Extracting resume data")
        with StepTimer("document_processing"):
            resume_content = await resume.read()
            resume_text = extract_docs(resume_content, resume.filename)
        logger.info(f"Resume extracted ({len(resume_text)} chars)")
            
        # Step 2: Analyze job description
        logger.info("Step 2: Analyzing job description")
        with StepTimer("job_analysis"):
            job_analysis = analyze_job_requirements(job_desc)
        logger.info("Job description analyzed")
        
        # Step 3: Company analysis (if provided)
        company_info = None
        if company:
            logger.info(f"Step 3: Analyzing company information for: {company}")
            with StepTimer("company_analysis"):
                company_info = analyze_company_info(company)
            logger.info("Company information analyzed")
        
        # Step 4: Generate cover letter
        logger.info("Step 4: Generating cover letter")
        with StepTimer("letter_generation"):
            cover_letter = generate_cover_letter(
                resume_text, 
                job_desc, 
                job_analysis, 
                company_info
            )
        
        generation_time = time.time() - start_time
        logger.info(f"Cover letter generated successfully in {generation_time:.2f} seconds")
        
        # Record success in metrics
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "success")
        
        return {"cover_letter": cover_letter}
        
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        
        # Record error in metrics
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "error")
        
        if isinstance(e, ValidationError) or isinstance(e, DocumentProcessingError):
            raise e
        raise HTTPException(status_code=500, detail=f"Error generating cover letter: {str(e)}")

@app.post("/api/analyze-job-description-image")
@limiter.limit(config["rate_limits"]["endpoints"]["analyze_job_desc_image"])
async def analyze_job_description_image_endpoint(
    request: Request,
    image: UploadFile = File(...)
):
    """
    Extract and analyze job description from an uploaded image
    """
    try:
        with StepTimer("job_image_analysis"):
            image_data = await image.read()
            result = analyze_job_description_image(image_data)
        return result
    except Exception as e:
        # Track API errors in metrics
        increment_counter_with_exemplar(API_ERRORS, "api_name", "job_analysis")
        
        logger.error(f"Error analyzing job description image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-company")
@limiter.limit(config["rate_limits"]["endpoints"]["analyze_company"])
async def analyze_company_endpoint(
    request: Request,
    company_name: str = Form(...)
):
    """
    Analyze company information
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        with StepTimer("company_analysis", request_id):
            result = analyze_company_info(company_name)
        return result
    except Exception as e:
        # Track API errors in metrics
        increment_counter_with_exemplar(API_ERRORS, "api_name", "company_analysis", request_id)
        
        logger.error(f"Error analyzing company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
