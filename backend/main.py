from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, UploadFile, File, Request
from typing import Optional

# Internal imports
from config import load_config
from modules.document.document import extract_docs
from modules.job.job import analyze_job_description_image
from modules.company.company import analyze_company_info
from modules.cover_letter.cover_letter import generate_cover_letter
from modules.errors import register_exception_handlers
from modules.errors.exceptions import ValidationError, DocumentProcessingError
from modules.monitoring import setup_metrics
from modules.monitoring.prometheus import StepTimer, COVER_LETTER_GENERATED, API_ERRORS
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

# Load configuration
config = load_config()

# Create FastAPI app
app = FastAPI(
    title="Cover Letter Generator API",
    description="API for generating personalized cover letters based on CV and job description",
    version="1.0.0",
)

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

# Setup metrics for Prometheus
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
    return {
        "status": "healthy",
        "api_version": app.version,
        "environment": config["env"]
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
    3. Company analysis
    4. Cover letter generation
    
    Usage Options:
    - CV file is always required (PDF or DOCX)
    - For job description, you must provide EITHER:
      a) job_desc_text: Plain text job description, OR
      b) job_desc_image: An image/screenshot of a job posting
    - Company name is optional but recommended for better results
    
    Note: If both job description text and image are provided, the image will be prioritized.
    
    Args:
        request: The HTTP request (required for rate limiting)
        cv_file: The user's CV/resume file (PDF or DOCX)
        job_desc_text: Job description text (optional if job_desc_image is provided)
        job_desc_image: Job description image file (optional if job_desc_text is provided)
        company_name: Name of the company to analyze (optional)
    """
    try:
        # Validate inputs - more robust validation
        if not cv_file:
            raise ValidationError("CV file is required", field="cv_file")
            
        if not cv_file.filename:
            raise ValidationError("CV file has no name", field="cv_file")
            
        # Check file extension
        filename = cv_file.filename.lower()
        if not (filename.endswith('.pdf') or filename.endswith('.docx')):
            raise ValidationError(
                "Only PDF and DOCX files are supported", 
                field="cv_file",
                details={"allowed_formats": ["pdf", "docx"], "provided": filename.split(".")[-1]}
            )
        
        # Validate that at least one job description input is provided
        if not job_desc_text and not job_desc_image:
            raise ValidationError(
                "Either job description text or job description image must be provided",
                details={"provided_fields": {"job_desc_text": bool(job_desc_text), "job_desc_image": bool(job_desc_image)}}
            )
        
        # Step 1: Extract text from the CV document
        with StepTimer("document_processing"):
            resume_text = await extract_docs(cv_file)
        
        # Validate CV text
        if not resume_text or not resume_text.strip():
            raise DocumentProcessingError("CV text extraction failed or CV is empty", doc_type="CV")
        
        # Step 2: Process job description (either text or image)
        job_description = ""
        
        if job_desc_image and job_desc_text:
            # If both are provided, prioritize the image
            if job_desc_image.content_type.startswith("image/"):
                with StepTimer("job_description_processing"):
                    # Read the image file
                    image_bytes = await job_desc_image.read()
                    # Use the service to analyze the job description image
                    job_description = await analyze_job_description_image(image_bytes, job_desc_image.content_type)
                logger.info(f"Using analyzed job description from image. Length: {len(job_description)}")
            else:
                raise ValidationError(
                    "Uploaded file is not a valid image format", 
                    field="job_desc_image",
                    details={"provided_content_type": job_desc_image.content_type}
                )
        elif job_desc_image:
            # Only image is provided
            if not job_desc_image.content_type.startswith("image/"):
                raise ValidationError(
                    "Uploaded file is not a valid image format. Supported formats include: JPEG, PNG, GIF, etc.",
                    field="job_desc_image",
                    details={"provided_content_type": job_desc_image.content_type}
                )
            
            with StepTimer("job_description_processing"):
                # Read the image file
                image_bytes = await job_desc_image.read()
                # Use the service to analyze the job description image
                job_description = await analyze_job_description_image(image_bytes, job_desc_image.content_type)
            logger.info(f"Using analyzed job description from image. Length: {len(job_description)}")
        elif job_desc_text:
            # Only text is provided
            if not job_desc_text.strip():
                raise ValidationError("Job description text cannot be empty", field="job_desc_text")
                
            job_description = job_desc_text
            logger.info(f"Using provided job description text. Length: {len(job_description)}")
        
        # Step 3: Get company information if company name is provided
        company_information = ""
        if company_name and company_name.strip():
            with StepTimer("company_analysis"):
                company_information = await analyze_company_info(company_name)
            logger.info(f"Retrieved company information for {company_name}. Length: {len(company_information)}")
        
        # Step 4: Generate the cover letter
        logger.info(f"Generating cover letter (CV length: {len(resume_text)}, Job desc length: {len(job_description)}, Company info length: {len(company_information)})")
        
        with StepTimer("cover_letter_generation"):
            cover_letter = await generate_cover_letter(resume_text, job_description, company_information)
        
        # Record success in metrics
        COVER_LETTER_GENERATED.labels(status="success").inc()
        
        # Return the cover letter as plain text to preserve formatting
        return cover_letter
        
    except Exception as e:
        # Record failure in metrics
        COVER_LETTER_GENERATED.labels(status="error").inc()
        
        # Let our global exception handler take care of this
        logger.error(f"Error in main cover letter endpoint: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
