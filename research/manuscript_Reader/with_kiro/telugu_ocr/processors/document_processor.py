"""Document processing for PDF to image conversion."""

import os
from pathlib import Path
from typing import List, Optional
from PIL import Image
import tempfile

from ..utils.exceptions import UnsupportedFormatException, PreprocessingException
from ..utils.logging_config import get_logger_config


class DocumentProcessor:
    """Handles PDF to image conversion and basic validation."""
    
    def __init__(self):
        """Initialize document processor."""
        self.logger_config = get_logger_config()
        self.process_logger = self.logger_config.get_process_logger()
        self.error_logger = self.logger_config.get_error_logger()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            import pdf2image
            self.pdf2image = pdf2image
        except ImportError:
            raise PreprocessingException(
                "pdf2image library not found. Install with: pip install pdf2image"
            )
    
    def convert_pdf_to_images(self, pdf_path: str, dpi: int = 300) -> List[Image.Image]:
        """
        Convert PDF to list of PIL Images.
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for conversion (default: 300)
            
        Returns:
            List of PIL Image objects, one per page
            
        Raises:
            UnsupportedFormatException: If file is not a valid PDF
            PreprocessingException: If conversion fails
        """
        pdf_path = Path(pdf_path)
        
        # Validate input file
        if not pdf_path.exists():
            raise UnsupportedFormatException(f"PDF file not found: {pdf_path}")
        
        if pdf_path.suffix.lower() != '.pdf':
            raise UnsupportedFormatException(f"File is not a PDF: {pdf_path}")
        
        self.process_logger.info(f"Converting PDF to images: {pdf_path}")
        
        try:
            # Convert PDF to images
            images = self.pdf2image.convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt='RGB'
            )
            
            self.process_logger.info(f"Successfully converted {len(images)} pages from PDF")
            
            # Validate images
            validated_images = []
            for i, image in enumerate(images, 1):
                if self._validate_image(image, i):
                    validated_images.append(image)
            
            if not validated_images:
                raise PreprocessingException("No valid images extracted from PDF")
            
            return validated_images
            
        except Exception as e:
            if isinstance(e, (UnsupportedFormatException, PreprocessingException)):
                raise
            else:
                raise PreprocessingException(f"Failed to convert PDF to images: {str(e)}")
    
    def _validate_image(self, image: Image.Image, page_number: int) -> bool:
        """
        Validate that an image is suitable for OCR processing.
        
        Args:
            image: PIL Image to validate
            page_number: Page number for logging
            
        Returns:
            bool: True if image is valid
        """
        try:
            # Check image dimensions
            width, height = image.size
            if width < 100 or height < 100:
                self.error_logger.warning(f"Page {page_number}: Image too small ({width}x{height})")
                return False
            
            # Check if image is too large (memory concerns)
            if width * height > 50_000_000:  # ~50MP
                self.error_logger.warning(f"Page {page_number}: Image very large ({width}x{height}), may cause memory issues")
            
            # Check image mode
            if image.mode not in ['RGB', 'L', 'RGBA']:
                self.process_logger.info(f"Page {page_number}: Converting image mode from {image.mode} to RGB")
                image = image.convert('RGB')
            
            self.process_logger.debug(f"Page {page_number}: Image validated ({width}x{height}, {image.mode})")
            return True
            
        except Exception as e:
            self.error_logger.error(f"Page {page_number}: Image validation failed: {str(e)}")
            return False
    
    def save_images_for_debug(self, images: List[Image.Image], output_dir: str) -> List[str]:
        """
        Save images to disk for debugging purposes.
        
        Args:
            images: List of PIL Images
            output_dir: Directory to save images
            
        Returns:
            List of saved image paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        for i, image in enumerate(images, 1):
            image_path = output_path / f"page_{i:03d}.png"
            try:
                image.save(image_path, 'PNG')
                saved_paths.append(str(image_path))
                self.process_logger.debug(f"Saved debug image: {image_path}")
            except Exception as e:
                self.error_logger.error(f"Failed to save debug image {image_path}: {str(e)}")
        
        return saved_paths
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get basic information about the PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF information
        """
        pdf_path = Path(pdf_path)
        
        info = {
            "file_path": str(pdf_path),
            "file_size": pdf_path.stat().st_size if pdf_path.exists() else 0,
            "exists": pdf_path.exists(),
            "is_pdf": pdf_path.suffix.lower() == '.pdf'
        }
        
        try:
            # Try to get page count without full conversion
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info["page_count"] = len(pdf_reader.pages)
        except:
            # Fallback: estimate based on file size (very rough)
            info["page_count"] = max(1, info["file_size"] // 100000)  # Rough estimate
        
        return info