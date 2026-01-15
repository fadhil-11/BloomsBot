"""
PDF text extraction module for BLOOMS BOT
Extracts readable text from uploaded PDF documents
"""

import PyPDF2
import re


def extract_text_from_pdf(pdf_path):
    """
    Extract text content from PDF file
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    try:
        text = ""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text:
                    text += page_text + "\n"
        
        # Clean extracted text
        text = clean_text(text)
        
        return text
        
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def clean_text(text):
    """
    Clean extracted text by removing extra whitespace and fixing common issues
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers (common pattern: isolated numbers)
    text = re.sub(r'\n\d+\n', '\n', text)
    
    # Fix common OCR issues
    text = text.replace('�', '')  # Remove replacement characters
    
    # Normalize line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_units_from_text(text):
    """
    Attempt to identify unit/module divisions in the text
    
    Args:
        text: Extracted text from document
        
    Returns:
        Dictionary mapping unit numbers to their content
    """
    units = {}
    
    # Common patterns for unit/module headings
    patterns = [
        r'UNIT[- ]?(\d+)[:\s]+(.*?)(?=UNIT[- ]?\d+|$)',
        r'MODULE[- ]?(\d+)[:\s]+(.*?)(?=MODULE[- ]?\d+|$)',
        r'Chapter[- ]?(\d+)[:\s]+(.*?)(?=Chapter[- ]?\d+|$)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            unit_num = match.group(1)
            unit_content = match.group(2).strip()
            units[f"Unit {unit_num}"] = unit_content
    
    # If no units found, treat entire document as single unit
    if not units:
        units["Unit 1"] = text
    
    return units


def extract_topics_from_unit(unit_text):
    """
    Extract key topics/concepts from a unit's text
    
    Args:
        unit_text: Text content of a unit
        
    Returns:
        List of identified topics
    """
    topics = []
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', unit_text)
    
    # Look for topic-like patterns (capitalized phrases, technical terms)
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Find capitalized multi-word terms (likely topics)
        topic_matches = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', sentence)
        topics.extend(topic_matches)
    
    # Remove duplicates and return
    return list(set(topics))


def identify_document_structure(text):
    """
    Analyze document structure to help with question generation
    
    Args:
        text: Full document text
        
    Returns:
        Dictionary with document analysis
    """
    structure = {
        'total_length': len(text),
        'has_units': False,
        'units': {},
        'key_terms': [],
        'document_type': 'general'
    }
    
    # Extract units
    units = extract_units_from_text(text)
    structure['units'] = units
    structure['has_units'] = len(units) > 1
    
    # Identify document type based on content
    if re.search(r'syllabus|curriculum|course outline', text, re.IGNORECASE):
        structure['document_type'] = 'syllabus'
    elif re.search(r'lecture|notes|chapter', text, re.IGNORECASE):
        structure['document_type'] = 'lecture_notes'
    
    # Extract key terms (capitalized technical terms)
    key_terms = re.findall(r'\b[A-Z][a-z]*(?:[A-Z][a-z]*)+\b', text)
    structure['key_terms'] = list(set(key_terms))[:50]  # Top 50 unique terms
    
    return structure
