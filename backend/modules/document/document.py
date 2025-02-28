import fitz  # PyMuPDF
import docx
import logging
import os
import tempfile
from fastapi import UploadFile
from typing import Optional

from modules.errors.exceptions import DocumentProcessingError, ValidationError

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
        
        if not text.strip():
            raise DocumentProcessingError(
                "Extracted PDF is empty or contains no text",
                doc_type="PDF",
                details={"file_path": file_path}
            )
            
        return text
    except fitz.FileDataError as e:
        raise DocumentProcessingError(
            f"Invalid or corrupted PDF file: {str(e)}",
            doc_type="PDF",
            details={"file_path": file_path, "error": str(e)}
        )
    except Exception as e:
        raise DocumentProcessingError(
            f"Error extracting text from PDF: {str(e)}",
            doc_type="PDF", 
            details={"file_path": file_path, "error_type": type(e).__name__}
        )

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file using python-docx"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
            
        if not text.strip():
            raise DocumentProcessingError(
                "Extracted DOCX is empty or contains no text",
                doc_type="DOCX",
                details={"file_path": file_path}
            )
            
        return text
    except docx.opc.exceptions.PackageNotFoundError:
        raise DocumentProcessingError(
            "Invalid or corrupted DOCX file",
            doc_type="DOCX",
            details={"file_path": file_path}
        )
    except Exception as e:
        raise DocumentProcessingError(
            f"Error extracting text from DOCX: {str(e)}",
            doc_type="DOCX",
            details={"file_path": file_path, "error_type": type(e).__name__}
        )

async def extract_docs(cv_file: UploadFile) -> str:
    """
    Extract text from a CV document (PDF or DOCX).
    
    Args:
        cv_file: The uploaded CV file
        
    Returns:
        The extracted text from the document
    """
    # Validate file extension
    if not cv_file or not cv_file.filename:
        raise ValidationError("No file provided or filename is empty", field="cv_file")
        
    filename = cv_file.filename.lower()
    logger.info(f"Processing file: {filename}")
    
    if not (filename.endswith('.pdf') or filename.endswith('.docx')):
        raise ValidationError(
            "Only PDF and DOCX files are supported", 
            field="cv_file",
            details={"allowed_formats": ["pdf", "docx"], "provided": filename.split(".")[-1]}
        )
    
    # Create a temporary file to store the uploaded content
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            # Write the uploaded file content to the temp file
            content = await cv_file.read()
            
            if not content:
                raise ValidationError("Uploaded file is empty", field="cv_file")
                
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Extract text based on file type
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(temp_path)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(temp_path)
        else:
            # This should never happen due to the earlier check
            raise ValidationError(
                "Unsupported file format", 
                field="cv_file",
                details={"file_extension": os.path.splitext(filename)[1]}
            )
        
        # Cleanup text - remove excessive whitespace
        text = " ".join(text.split())
        
        # Verify we got meaningful content
        if not text or len(text) < 100:  # Arbitrary minimum length for a reasonable CV
            logger.warning(f"Extracted text too short ({len(text)} chars) from file: {filename}")
            raise DocumentProcessingError(
                "Extracted CV text is too short or contains no meaningful content",
                doc_type=os.path.splitext(filename)[1].upper().replace('.', ''),
                details={"text_length": len(text), "threshold": 100}
            )
        
        logger.info(f"Successfully extracted {len(text)} characters from {filename}")
        
        return text
    
    except Exception as e:
        # If it's not a ValidationError or DocumentProcessingError, wrap it
        if not isinstance(e, (ValidationError, DocumentProcessingError)):
            raise DocumentProcessingError(
                f"Error processing document: {str(e)}",
                doc_type=os.path.splitext(filename)[1].upper().replace('.', '') if filename else "Unknown",
                details={"filename": filename, "error_type": type(e).__name__}
            ) from e
        raise
    
    finally:
        # Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Deleted temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}") 