"""Image preprocessing for better Telugu OCR results."""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional
import cv2

from ..utils.exceptions import PreprocessingException
from ..utils.logging_config import get_logger_config


class ImagePreprocessor:
    """Handles image preprocessing for optimal Telugu OCR results."""
    
    def __init__(self, config: dict = None):
        """Initialize image preprocessor with configuration."""
        self.config = config or {}
        self.logger_config = get_logger_config()
        self.process_logger = self.logger_config.get_process_logger()
        self.error_logger = self.logger_config.get_error_logger()
        
        # Default preprocessing parameters
        self.resize_factor = self.config.get('resize_factor', 2.0)
        self.noise_reduction = self.config.get('noise_reduction', True)
        self.contrast_enhancement = self.config.get('contrast_enhancement', True)
        self.deskew = self.config.get('deskew', True)
        self.binarization = self.config.get('binarization', True)
    
    def preprocess_image(self, image: Image.Image, page_number: int = 1) -> Image.Image:
        """
        Apply comprehensive preprocessing to improve OCR accuracy.
        
        Args:
            image: PIL Image to preprocess
            page_number: Page number for logging
            
        Returns:
            Preprocessed PIL Image
        """
        self.process_logger.info(f"Preprocessing page {page_number}")
        
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply preprocessing steps
            processed_image = image
            
            if self.resize_factor != 1.0:
                processed_image = self._resize_image(processed_image, self.resize_factor)
            
            if self.noise_reduction:
                processed_image = self._reduce_noise(processed_image)
            
            if self.contrast_enhancement:
                processed_image = self._enhance_contrast(processed_image)
            
            if self.deskew:
                processed_image = self._deskew_image(processed_image)
            
            if self.binarization:
                processed_image = self._binarize_image(processed_image)
            
            self.process_logger.info(f"Page {page_number} preprocessing completed")
            return processed_image
            
        except Exception as e:
            raise PreprocessingException(f"Failed to preprocess page {page_number}: {str(e)}")
    
    def enhance_for_telugu(self, image: Image.Image) -> Image.Image:
        """
        Apply Telugu-specific enhancements.
        
        Args:
            image: PIL Image to enhance
            
        Returns:
            Enhanced PIL Image
        """
        try:
            # Telugu script benefits from higher contrast and sharpening
            enhanced = image
            
            # Increase sharpness for Telugu characters
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = sharpness_enhancer.enhance(1.5)
            
            # Enhance contrast for better character separation
            contrast_enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = contrast_enhancer.enhance(1.3)
            
            # Apply unsharp mask for Telugu character clarity
            enhanced = enhanced.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            return enhanced
            
        except Exception as e:
            self.error_logger.warning(f"Telugu enhancement failed: {str(e)}")
            return image  # Return original if enhancement fails
    
    def _resize_image(self, image: Image.Image, factor: float) -> Image.Image:
        """Resize image by given factor."""
        if factor == 1.0:
            return image
        
        width, height = image.size
        new_width = int(width * factor)
        new_height = int(height * factor)
        
        # Use high-quality resampling
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _reduce_noise(self, image: Image.Image) -> Image.Image:
        """Apply noise reduction filters."""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Apply bilateral filter for noise reduction while preserving edges
            denoised = cv2.bilateralFilter(cv_image, 9, 75, 75)
            
            # Convert back to PIL
            denoised_rgb = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
            return Image.fromarray(denoised_rgb)
            
        except Exception as e:
            self.error_logger.warning(f"Noise reduction failed: {str(e)}")
            # Fallback to PIL-based noise reduction
            return image.filter(ImageFilter.MedianFilter(size=3))
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast."""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab[:, :, 0] = clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Convert back to PIL
            enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
            return Image.fromarray(enhanced_rgb)
            
        except Exception as e:
            self.error_logger.warning(f"Contrast enhancement failed: {str(e)}")
            # Fallback to PIL-based contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(1.2)
    
    def _deskew_image(self, image: Image.Image) -> Image.Image:
        """Correct image skew/rotation."""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            
            # Detect lines using HoughLines
            edges = cv2.Canny(cv_image, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None and len(lines) > 0:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:10]:  # Use first 10 lines
                    angle = theta * 180 / np.pi
                    if angle > 90:
                        angle = angle - 180
                    angles.append(angle)
                
                if angles:
                    avg_angle = np.median(angles)
                    
                    # Only rotate if angle is significant
                    if abs(avg_angle) > 0.5:
                        # Rotate image
                        rotated = image.rotate(-avg_angle, expand=True, fillcolor='white')
                        self.process_logger.debug(f"Deskewed image by {avg_angle:.2f} degrees")
                        return rotated
            
            return image
            
        except Exception as e:
            self.error_logger.warning(f"Deskewing failed: {str(e)}")
            return image
    
    def _binarize_image(self, image: Image.Image) -> Image.Image:
        """Convert image to binary (black and white)."""
        try:
            # Convert to grayscale first
            gray = image.convert('L')
            
            # Convert to OpenCV format
            cv_image = np.array(gray)
            
            # Apply adaptive thresholding for better results with varying lighting
            binary = cv2.adaptiveThreshold(
                cv_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL
            return Image.fromarray(binary).convert('RGB')
            
        except Exception as e:
            self.error_logger.warning(f"Binarization failed: {str(e)}")
            # Fallback to simple threshold
            gray = image.convert('L')
            return gray.point(lambda x: 0 if x < 128 else 255, '1').convert('RGB')
    
    def create_preprocessing_variants(self, image: Image.Image) -> dict:
        """
        Create multiple preprocessing variants for comparison.
        
        Args:
            image: Original PIL Image
            
        Returns:
            Dictionary of preprocessed image variants
        """
        variants = {}
        
        try:
            # Original image
            variants['original'] = image
            
            # Light preprocessing
            variants['light'] = self._light_preprocessing(image)
            
            # Standard preprocessing
            variants['standard'] = self.preprocess_image(image)
            
            # Heavy preprocessing
            variants['heavy'] = self._heavy_preprocessing(image)
            
            # Telugu-optimized
            variants['telugu_optimized'] = self.enhance_for_telugu(
                self.preprocess_image(image)
            )
            
        except Exception as e:
            self.error_logger.error(f"Failed to create preprocessing variants: {str(e)}")
            variants = {'original': image}  # Fallback to original only
        
        return variants
    
    def _light_preprocessing(self, image: Image.Image) -> Image.Image:
        """Apply minimal preprocessing."""
        processed = image
        if image.mode != 'RGB':
            processed = processed.convert('RGB')
        
        # Only resize and light contrast enhancement
        if self.resize_factor != 1.0:
            processed = self._resize_image(processed, self.resize_factor)
        
        enhancer = ImageEnhance.Contrast(processed)
        processed = enhancer.enhance(1.1)
        
        return processed
    
    def _heavy_preprocessing(self, image: Image.Image) -> Image.Image:
        """Apply aggressive preprocessing."""
        processed = image
        if image.mode != 'RGB':
            processed = processed.convert('RGB')
        
        # All preprocessing steps with stronger parameters
        processed = self._resize_image(processed, self.resize_factor * 1.5)
        processed = self._reduce_noise(processed)
        processed = self._enhance_contrast(processed)
        processed = self._deskew_image(processed)
        processed = self._binarize_image(processed)
        
        # Additional sharpening
        processed = processed.filter(ImageFilter.SHARPEN)
        
        return processed