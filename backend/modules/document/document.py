import fitz  # PyMuPDF
import docx
import logging
import os
import tempfile
from fastapi import UploadFile

# Set up logging
logger = logging.getLogger(__name__)

# Document processing service functions
def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using PyMuPDF"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise e

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file using python-docx"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        raise e

async def extract_docs(cv_file: UploadFile) -> str:
    """
    Extract text from a CV document (PDF or DOCX).
    
    Args:
        cv_file: The uploaded CV file
        
    Returns:
        The extracted text from the document
    """
    # Validate file extension
    filename = cv_file.filename.lower()
    logger.info(f"Processing file: {filename}")
    
    if not (filename.endswith('.pdf') or filename.endswith('.docx')):
        raise ValueError("Only PDF and DOCX files are supported")
    
    # Create a temporary file to store the uploaded content
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
        # Write the uploaded file content to the temp file
        content = await cv_file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Extract text based on file type
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(temp_path)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(temp_path)
        else:
            # This should never happen due to the earlier check
            raise ValueError("Unsupported file format")
        
        # Cleanup text - remove excessive whitespace
        text = " ".join(text.split())
        
        logger.info(f"Successfully extracted {len(text)} characters from {filename}")
        
        return text
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise ValueError(f"Error parsing document: {str(e)}")
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.debug(f"Deleted temporary file: {temp_path}") 