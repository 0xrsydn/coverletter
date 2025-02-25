from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from typing import Optional

# Internal imports
from config import load_config
from modules.document.document import extract_docs
from modules.job.job import analyze_job_description_image
from modules.company.company import analyze_company_info
from modules.cover_letter.cover_letter import generate_cover_letter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = load_config()

# Create FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI"}

# Main cover letter generation endpoint
@app.post("/generate_cover_letter", response_class=PlainTextResponse)
async def generate_cover_letter_main(
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
        cv_file: The user's CV/resume file (PDF or DOCX)
        job_desc_text: Job description text (optional if job_desc_image is provided)
        job_desc_image: Job description image file (optional if job_desc_text is provided)
        company_name: Name of the company to analyze (optional)
    """
    try:
        # Step 1: Extract text from the CV document
        resume_text = await extract_docs(cv_file)
        
        # Validate CV text
        if not resume_text or not resume_text.strip():
            raise HTTPException(status_code=400, detail="CV text extraction failed or CV is empty")
        
        # Step 2: Process job description (either text or image)
        job_description = ""
        
        # Validate that at least one job description input is provided
        if not job_desc_text and not job_desc_image:
            raise HTTPException(
                status_code=400, 
                detail="Either job description text or job description image must be provided"
            )
        
        if job_desc_image and job_desc_text:
            # If both are provided, prioritize the image
            if job_desc_image.content_type.startswith("image/"):
                # Read the image file
                image_bytes = await job_desc_image.read()
                # Use the service to analyze the job description image
                job_description = await analyze_job_description_image(image_bytes, job_desc_image.content_type)
                logger.info(f"Using analyzed job description from image. Length: {len(job_description)}")
            else:
                raise HTTPException(status_code=400, detail="Uploaded file is not a valid image format")
        elif job_desc_image:
            # Only image is provided
            if not job_desc_image.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, 
                    detail="Uploaded file is not a valid image format. Supported formats include: JPEG, PNG, GIF, etc."
                )
                
            # Read the image file
            image_bytes = await job_desc_image.read()
            # Use the service to analyze the job description image
            job_description = await analyze_job_description_image(image_bytes, job_desc_image.content_type)
            logger.info(f"Using analyzed job description from image. Length: {len(job_description)}")
        elif job_desc_text:
            # Only text is provided
            if not job_desc_text.strip():
                raise HTTPException(status_code=400, detail="Job description text cannot be empty")
                
            job_description = job_desc_text
            logger.info(f"Using provided job description text. Length: {len(job_description)}")
        
        # Step 3: Get company information if company name is provided
        company_information = ""
        if company_name and company_name.strip():
            company_information = await analyze_company_info(company_name)
            logger.info(f"Retrieved company information for {company_name}. Length: {len(company_information)}")
        
        # Step 4: Generate the cover letter
        logger.info(f"Generating cover letter (CV length: {len(resume_text)}, Job desc length: {len(job_description)}, Company info length: {len(company_information)})")
        cover_letter = await generate_cover_letter(resume_text, job_description, company_information)
        
        # Return the cover letter as plain text to preserve formatting
        return cover_letter
        
    except Exception as e:
        logger.error(f"Error in main cover letter endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating cover letter: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
