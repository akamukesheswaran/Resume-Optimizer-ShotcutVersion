import PyPDF2
from docx import Document
from typing import Optional
import io

class ResumeParser:
    """Parse resume from different file formats"""
    
    @staticmethod
    def extract_text_from_pdf(file) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error parsing DOCX: {str(e)}")
    
    @staticmethod
    def extract_text_from_txt(file) -> str:
        """Extract text from TXT file"""
        try:
            # Read as bytes first, then decode
            content = file.read()
            if isinstance(content, bytes):
                return content.decode('utf-8').strip()
            return content.strip()
        except Exception as e:
            raise ValueError(f"Error parsing TXT: {str(e)}")
    
    @classmethod
    def parse_resume(cls, file) -> str:
        """Parse resume based on file type"""
        filename = file.name.lower()
        
        if filename.endswith('.pdf'):
            return cls.extract_text_from_pdf(file)
        elif filename.endswith('.docx'):
            return cls.extract_text_from_docx(file)
        elif filename.endswith('.txt'):
            return cls.extract_text_from_txt(file)
        else:
            raise ValueError("Unsupported file format. Please upload PDF, DOCX, or TXT file.")