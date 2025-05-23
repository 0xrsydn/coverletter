from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, UploadFile, File, Request
from typing import Optional, List
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

# --- Add Static Files Mounting ---
# Create static directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True) 
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- Add Jinja2Templates Configuration ---
# Create templates directory if it doesn't exist
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

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

# --- Modify Root Endpoint to Serve HTML ---
# Root endpoint
@app.get("/", response_class=HTMLResponse) # Add new root endpoint for HTML
async def read_root(request: Request): # Add request parameter
    # Render the index.html template
    # Pass the request object to the template context, required by Jinja2Templates
    return templates.TemplateResponse("index.html", {"request": request})

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

# Define allowed file types and size limits
ALLOWED_CV_EXTENSIONS = ['.pdf', '.docx', '.doc']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ALLOWED_CV_CONTENT_TYPES = [
    'application/pdf', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
]
ALLOWED_IMAGE_CONTENT_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
MAX_CV_SIZE_MB = 3
MAX_IMAGE_SIZE_MB = 5

def validate_file(
    file: UploadFile, 
    allowed_extensions: List[str], 
    allowed_content_types: List[str], 
    max_size_mb: int, 
    field_name: str
) -> None:
    """
    Validate a file upload based on extension, content type, and size.
    
    Args:
        file: The uploaded file to validate
        allowed_extensions: List of allowed file extensions (including period)
        allowed_content_types: List of allowed content types
        max_size_mb: Maximum file size in MB
        field_name: Name of the field for error messages
        
    Raises:
        ValidationError: If validation fails
    """
    if not file:
        return
        
    # Get file extension
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    
    # Validate file extension
    if file_ext not in allowed_extensions:
        allowed_ext_str = ', '.join(allowed_extensions)
        raise ValidationError(
            f"File must be one of these types: {allowed_ext_str}",
            field=field_name
        )
    
    # Validate content type
    if file.content_type not in allowed_content_types:
        allowed_types_str = ', '.join(allowed_content_types)
        raise ValidationError(
            f"File content type must be one of: {allowed_types_str}",
            field=field_name
        )
        
    # Check file size by reading the first chunk
    file.file.seek(0, 2)  # Seek to the end
    file_size = file.file.tell()  # Get current position
    file.file.seek(0)  # Reset to beginning
    
    # Convert bytes to MB
    file_size_mb = file_size / (1024 * 1024)
    
    if file_size_mb > max_size_mb:
        raise ValidationError(
            f"File too large ({file_size_mb:.2f}MB). Maximum allowed size is {max_size_mb}MB",
            field=field_name
        )

# Main cover letter generation endpoint
@app.post("/api/generate_cover_letter", response_class=PlainTextResponse)
@limiter.limit(config["rate_limits"]["endpoints"]["generate_cover_letter"])
async def generate_cover_letter_main(
    request: Request,  # Required for rate limiting
    cv_file: UploadFile = File(...),
    job_desc_text: Optional[str] = Form(None),
    job_desc_image: UploadFile = File(None),
    company_name: Optional[str] = Form(None),
    word_limit: Optional[int] = Form(300)
):
    """
    Main entry point for generating a cover letter from the frontend form.
    This consolidated endpoint handles:
    1. CV document parsing
    2. Job description (text or image)
    3. Company information (optional)
    4. Word limit setting (optional, defaults to 300)
    5. Cover letter generation
    """
    start_time = time.time()
    logger.info("Starting cover letter generation process")
    request_id = getattr(request.state, "request_id", None)
    
    try:
        # Validate inputs
        if not cv_file:
            raise ValidationError("CV file is required")
            
        if not job_desc_text and not job_desc_image:
            raise ValidationError("Either job description text or image must be provided")
            
        if word_limit and (word_limit < 250 or word_limit > 400):
            raise ValidationError("Word limit must be between 250 and 400 words")
        
        # Validate CV file
        validate_file(
            cv_file, 
            ALLOWED_CV_EXTENSIONS, 
            ALLOWED_CV_CONTENT_TYPES, 
            MAX_CV_SIZE_MB, 
            "cv_file"
        )
        
        # Validate job description image if provided
        if job_desc_image:
            validate_file(
                job_desc_image, 
                ALLOWED_IMAGE_EXTENSIONS, 
                ALLOWED_IMAGE_CONTENT_TYPES, 
                MAX_IMAGE_SIZE_MB, 
                "job_desc_image"
            )
            
        # Step 1: Process CV document
        try:
            with StepTimer("document_processing", request_id):
                cv_text = await extract_docs(cv_file)
                if not cv_text or len(cv_text.strip()) < 10:
                    raise DocumentProcessingError("Could not extract sufficient text from CV document", "CV")
                logger.info(f"CV processed: {len(cv_text)} characters extracted")
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise DocumentProcessingError(f"Error processing your CV: {str(e)}", "CV")
        
        # Step 2: Process job description
        job_description = None
        try:
            with StepTimer("job_analysis", request_id):
                if job_desc_text:
                    job_description = job_desc_text
                    logger.info("Job description processed from text input")
                elif job_desc_image:
                    job_description = await analyze_job_description_image(await job_desc_image.read(), job_desc_image.content_type)
                    logger.info("Job description processed from image")
                else:
                    raise ValidationError("Either job description text or image must be provided")
                    
                # Analyze job requirements
                job_analysis = await analyze_job_requirements(job_description)
                logger.info(f"Job requirements extracted: {len(job_analysis)} requirements found")
        except Exception as e:
            logger.error(f"Error processing job description: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error analyzing job description: {str(e)}")
        
        # Step 3: Get company information if provided
        company_info = None
        if company_name:
            try:
                with StepTimer("company_analysis", request_id):
                    company_info = analyze_company_info(company_name)
                    logger.info(f"Company information retrieved for {company_name}")
            except Exception as e:
                logger.warning(f"Error retrieving company info for {company_name}: {str(e)}")
                # Continue without company info rather than failing
                company_info = None
                logger.info("Continuing without company information")
        
        # Step 4: Generate cover letter
        try:
            with StepTimer("letter_generation", request_id):
                cover_letter = await generate_cover_letter(
                    resume_text=cv_text,
                    job_description=job_description,
                    company_info=company_info,
                    word_limit=word_limit
                )
                if not cover_letter or len(cover_letter.strip()) < 50:
                    raise HTTPException(
                        status_code=500, 
                        detail="Generated cover letter is too short or empty. Please try again."
                    )
                logger.info(f"Cover letter generated: {len(cover_letter)} characters")
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating cover letter: {str(e)}")
        
        generation_time = time.time() - start_time
        logger.info(f"Cover letter generated successfully in {generation_time:.2f} seconds")
        
        # Record success in metrics
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "success", request_id)
        
        return cover_letter
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "validation_error", request_id)
        raise HTTPException(status_code=400, detail=str(e))
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "document_error", request_id)
        raise HTTPException(status_code=422, detail=str(e))
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "error", request_id)
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error generating cover letter: {str(e)}")
        increment_counter_with_exemplar(COVER_LETTER_GENERATED, "status", "error", request_id)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
