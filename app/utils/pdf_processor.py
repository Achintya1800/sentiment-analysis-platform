"""
PDF Processing Utilities
Handles PDF text extraction and preprocessing for sentiment analysis.
"""

import PyPDF2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file):
    """
    Extract text content from uploaded PDF file.
    
    Args:
        pdf_file: FileStorage object containing the PDF file
        
    Returns:
        str: Extracted text content or None if extraction fails
        
    Raises:
        Exception: If PDF processing fails
    """
    try:
        logger.info(f"Starting PDF text extraction for file: {pdf_file.filename}")
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        # Extract text from all pages
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            text += page_text + "\n"
            logger.debug(f"Extracted {len(page_text)} characters from page {page_num + 1}")
        
        # Clean and process the extracted text
        text = text.strip()
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        logger.info(f"Successfully extracted {len(text)} characters from {len(pdf_reader.pages)} pages")
        
        return text if text else None
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

def preprocess_text(text, max_length=2000):
    """
    Preprocess text for sentiment analysis.
    
    Args:
        text (str): Raw extracted text
        max_length (int): Maximum text length for API processing
        
    Returns:
        str: Preprocessed text ready for sentiment analysis
    """
    if not text:
        return ""
    
    # Remove non-ASCII characters for better API compatibility
    text = ''.join(char for char in text if ord(char) < 128)
    
    # Limit text length for API constraints
    if len(text) > max_length:
        text = text[:max_length]
        logger.info(f"Text truncated to {max_length} characters for API processing")
    
    return text.strip()

def validate_pdf_content(text, min_length=10):
    """
    Validate that extracted PDF content is suitable for analysis.
    
    Args:
        text (str): Extracted text content
        min_length (int): Minimum required text length
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not text:
        return False, "No text could be extracted from the PDF"
    
    if len(text.strip()) < min_length:
        return False, f"PDF contains insufficient text for analysis (minimum {min_length} characters required)"
    
    # Check for meaningful content (not just whitespace/special characters)
    meaningful_chars = sum(1 for char in text if char.isalnum())
    if meaningful_chars < min_length // 2:
        return False, "PDF does not contain sufficient meaningful text content"
    
    return True, ""