from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
from services.job_service import analyze_job_description_image

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/analyze_job_desc_image")
async def analyze_job_desc_image(job_desc_image: UploadFile = File(...)):
    """
    Analyze job description image using AI model.
    """
    # Validate file is an image
    if not job_desc_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")
    
    try:
        # Read the image file
        image_bytes = await job_desc_image.read()
        
        # Use the service to analyze the job description
        result = await analyze_job_description_image(image_bytes, job_desc_image.content_type)
        logger.info(f"Successfully analyzed job description image. Response length: {len(result)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing job description image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing job description: {str(e)}") 