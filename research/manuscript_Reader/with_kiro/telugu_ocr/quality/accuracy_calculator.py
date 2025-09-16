"""Accuracy calculation and metrics for OCR results."""

import re
import difflib
from typing import List, Dict, Tuple, Optional
from collections import Counter
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import Levenshtein

from ..models.data_models import OCRResult, AccuracyReport
from ..utils.logging_config import get_logger_config


class AccuracyCalculator:
    """Calculates various accuracy metrics for OCR results."""
    
    def __init__(self):
        """Initialize accuracy calculator."""
        self.logger_config = get_logger_config()
        self.quality_logger = self.logger_config.get_quality_logger()
        
        # Download required NLTK data if not present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
            except:
                pass  # Continue without NLTK if download fails
    
    def calculate_character_accuracy(self, extracted_text: str, reference_text: str) -> float:
        """
        Calculate character-level accuracy.
        
        Args:
            extracted_text: Text extracted by OCR
            reference_text: Ground truth reference text
            
        Returns:
            Character accuracy as percentage (0.0 to 1.0)
        """
        if not reference_text:
            return 0.0
        
        try:
            # Normalize texts
            extracted = self._normalize_text(extracted_text)
            reference = self._normalize_text(reference_text)
            
            # Calculate edit distance
            edit_distance = Levenshtein.distance(extracted, reference)
            
            # Calculate accuracy
            max_length = max(len(extracted), len(reference))
            if max_length == 0:
                return 1.0
            
            accuracy = 1.0 - (edit_distance / max_length)
            return max(0.0, accuracy)
            
        except Exception as e:
            self.quality_logger.error(f"Character accuracy calculation failed: {str(e)}")
            return 0.0
    
    def calculate_word_accuracy(self, extracted_text: str, reference_text: str) -> float:
        """
        Calculate word-level accuracy.
        
        Args:
            extracted_text: Text extracted by OCR
            reference_text: Ground truth reference text
            
        Returns:
            Word accuracy as percentage (0.0 to 1.0)
        """
        if not reference_text:
            return 0.0
        
        try:
            # Tokenize into words
            extracted_words = self._tokenize_words(extracted_text)
            reference_words = self._tokenize_words(reference_text)
            
            if not reference_words:
                return 1.0 if not extracted_words else 0.0
            
            # Calculate word-level edit distance
            correct_words = 0
            total_words = len(reference_words)
            
            # Use sequence matching to find correct words
            matcher = difflib.SequenceMatcher(None, extracted_words, reference_words)
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    correct_words += (i2 - i1)
            
            accuracy = correct_words / total_words if total_words > 0 else 0.0
            return min(1.0, accuracy)
            
        except Exception as e:
            self.quality_logger.error(f"Word accuracy calculation failed: {str(e)}")
            return 0.0
    
    def calculate_bleu_score(self, extracted_text: str, reference_text: str) -> float:
        """
        Calculate BLEU score for text similarity.
        
        Args:
            extracted_text: Text extracted by OCR
            reference_text: Ground truth reference text
            
        Returns:
            BLEU score (0.0 to 1.0)
        """
        if not reference_text or not extracted_text:
            return 0.0
        
        try:
            # Tokenize texts
            extracted_tokens = self._tokenize_words(extracted_text)
            reference_tokens = self._tokenize_words(reference_text)
            
            if not reference_tokens or not extracted_tokens:
                return 0.0
            
            # Calculate BLEU score
            smoothing = SmoothingFunction().method1
            bleu_score = sentence_bleu(
                [reference_tokens], 
                extracted_tokens,
                smoothing_function=smoothing
            )
            
            return bleu_score
            
        except Exception as e:
            self.quality_logger.error(f"BLEU score calculation failed: {str(e)}")
            return 0.0
    
    def calculate_edit_distance(self, extracted_text: str, reference_text: str) -> int:
        """
        Calculate Levenshtein edit distance.
        
        Args:
            extracted_text: Text extracted by OCR
            reference_text: Ground truth reference text
            
        Returns:
            Edit distance (number of operations needed)
        """
        try:
            extracted = self._normalize_text(extracted_text)
            reference = self._normalize_text(reference_text)
            
            return Levenshtein.distance(extracted, reference)
            
        except Exception as e:
            self.quality_logger.error(f"Edit distance calculation failed: {str(e)}")
            return max(len(extracted_text), len(reference_text))
    
    def analyze_confidence_correlation(self, results: List[OCRResult], 
                                     reference_texts: List[str]) -> Dict[str, float]:
        """
        Analyze correlation between confidence scores and actual accuracy.
        
        Args:
            results: List of OCR results with confidence scores
            reference_texts: List of reference texts for comparison
            
        Returns:
            Dictionary with correlation analysis
        """
        if len(results) != len(reference_texts):
            self.quality_logger.warning("Mismatch between results and reference texts count")
            return {}
        
        try:
            confidences = []
            accuracies = []
            
            for result, reference in zip(results, reference_texts):
                if reference:  # Only include pages with reference text
                    confidences.append(result.confidence_score)
                    accuracy = self.calculate_character_accuracy(result.text, reference)
                    accuracies.append(accuracy)
            
            if len(confidences) < 2:
                return {'correlation': 0.0, 'sample_size': len(confidences)}
            
            # Calculate Pearson correlation coefficient
            correlation = self._calculate_correlation(confidences, accuracies)
            
            return {
                'correlation': correlation,
                'sample_size': len(confidences),
                'avg_confidence': sum(confidences) / len(confidences),
                'avg_accuracy': sum(accuracies) / len(accuracies),
                'confidence_range': (min(confidences), max(confidences)),
                'accuracy_range': (min(accuracies), max(accuracies))
            }
            
        except Exception as e:
            self.quality_logger.error(f"Confidence correlation analysis failed: {str(e)}")
            return {}
    
    def generate_error_analysis(self, extracted_text: str, reference_text: str) -> Dict[str, any]:
        """
        Generate detailed error analysis.
        
        Args:
            extracted_text: Text extracted by OCR
            reference_text: Ground truth reference text
            
        Returns:
            Dictionary with error analysis
        """
        try:
            analysis = {
                'character_errors': self._analyze_character_errors(extracted_text, reference_text),
                'word_errors': self._analyze_word_errors(extracted_text, reference_text),
                'telugu_specific_errors': self._analyze_telugu_errors(extracted_text, reference_text),
                'structural_errors': self._analyze_structural_errors(extracted_text, reference_text)
            }
            
            return analysis
            
        except Exception as e:
            self.quality_logger.error(f"Error analysis failed: {str(e)}")
            return {}
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize Telugu text (basic normalization)
        # This could be expanded with more sophisticated Telugu normalization
        
        return normalized
    
    def _tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words."""
        if not text:
            return []
        
        # Simple word tokenization
        # For Telugu, this might need more sophisticated tokenization
        words = re.findall(r'\S+', text)
        return [word.strip() for word in words if word.strip()]
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _analyze_character_errors(self, extracted: str, reference: str) -> Dict[str, any]:
        """Analyze character-level errors."""
        if not reference:
            return {}
        
        # Get character-level differences
        extracted_chars = list(self._normalize_text(extracted))
        reference_chars = list(self._normalize_text(reference))
        
        # Count different types of errors
        substitutions = []
        insertions = []
        deletions = []
        
        matcher = difflib.SequenceMatcher(None, reference_chars, extracted_chars)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # Substitution errors
                for ref_char, ext_char in zip(reference_chars[i1:i2], extracted_chars[j1:j2]):
                    substitutions.append((ref_char, ext_char))
            elif tag == 'delete':
                # Deletion errors (missing characters)
                for char in reference_chars[i1:i2]:
                    deletions.append(char)
            elif tag == 'insert':
                # Insertion errors (extra characters)
                for char in extracted_chars[j1:j2]:
                    insertions.append(char)
        
        return {
            'substitutions': Counter(substitutions).most_common(10),
            'deletions': Counter(deletions).most_common(10),
            'insertions': Counter(insertions).most_common(10),
            'total_errors': len(substitutions) + len(deletions) + len(insertions)
        }
    
    def _analyze_word_errors(self, extracted: str, reference: str) -> Dict[str, any]:
        """Analyze word-level errors."""
        extracted_words = self._tokenize_words(extracted)
        reference_words = self._tokenize_words(reference)
        
        # Find word differences
        matcher = difflib.SequenceMatcher(None, reference_words, extracted_words)
        
        word_substitutions = []
        missing_words = []
        extra_words = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                for ref_word, ext_word in zip(reference_words[i1:i2], extracted_words[j1:j2]):
                    word_substitutions.append((ref_word, ext_word))
            elif tag == 'delete':
                missing_words.extend(reference_words[i1:i2])
            elif tag == 'insert':
                extra_words.extend(extracted_words[j1:j2])
        
        return {
            'word_substitutions': Counter(word_substitutions).most_common(10),
            'missing_words': Counter(missing_words).most_common(10),
            'extra_words': Counter(extra_words).most_common(10),
            'total_word_errors': len(word_substitutions) + len(missing_words) + len(extra_words)
        }
    
    def _analyze_telugu_errors(self, extracted: str, reference: str) -> Dict[str, any]:
        """Analyze Telugu-specific errors."""
        # Telugu character ranges
        telugu_range = (0x0C00, 0x0C7F)
        
        # Find Telugu characters in both texts
        extracted_telugu = [c for c in extracted if telugu_range[0] <= ord(c) <= telugu_range[1]]
        reference_telugu = [c for c in reference if telugu_range[0] <= ord(c) <= telugu_range[1]]
        
        # Common Telugu OCR error patterns
        common_confusions = [
            ('ప', 'బ'), ('బ', 'ప'),  # pa/ba confusion
            ('త', 'ద'), ('ద', 'త'),  # ta/da confusion
            ('క', 'గ'), ('గ', 'క'),  # ka/ga confusion
            ('చ', 'జ'), ('జ', 'చ'),  # cha/ja confusion
        ]
        
        confusion_errors = []
        for ref_char, ext_char in common_confusions:
            if ref_char in reference and ext_char in extracted:
                # Count potential confusions
                ref_count = reference.count(ref_char)
                ext_count = extracted.count(ext_char)
                if abs(ref_count - ext_count) > 0:
                    confusion_errors.append((ref_char, ext_char, abs(ref_count - ext_count)))
        
        return {
            'telugu_char_count_reference': len(reference_telugu),
            'telugu_char_count_extracted': len(extracted_telugu),
            'common_confusions': confusion_errors,
            'telugu_accuracy': len(extracted_telugu) / len(reference_telugu) if reference_telugu else 0.0
        }
    
    def _analyze_structural_errors(self, extracted: str, reference: str) -> Dict[str, any]:
        """Analyze structural errors (line breaks, spacing, etc.)."""
        # Line structure analysis
        extracted_lines = extracted.split('\n')
        reference_lines = reference.split('\n')
        
        # Spacing analysis
        extracted_spaces = extracted.count(' ')
        reference_spaces = reference.count(' ')
        
        return {
            'line_count_reference': len(reference_lines),
            'line_count_extracted': len(extracted_lines),
            'line_count_difference': abs(len(extracted_lines) - len(reference_lines)),
            'space_count_reference': reference_spaces,
            'space_count_extracted': extracted_spaces,
            'space_count_difference': abs(extracted_spaces - reference_spaces),
            'avg_line_length_reference': sum(len(line) for line in reference_lines) / len(reference_lines) if reference_lines else 0,
            'avg_line_length_extracted': sum(len(line) for line in extracted_lines) / len(extracted_lines) if extracted_lines else 0
        }
    
    def create_comprehensive_accuracy_report(self, results: List[OCRResult], 
                                           reference_texts: List[str],
                                           engine_name: str) -> AccuracyReport:
        """
        Create comprehensive accuracy report.
        
        Args:
            results: List of OCR results
            reference_texts: List of reference texts
            engine_name: Name of OCR engine
            
        Returns:
            Comprehensive accuracy report
        """
        try:
            if len(results) != len(reference_texts):
                self.quality_logger.warning(f"Mismatch in results/reference count for {engine_name}")
            
            # Calculate overall metrics
            char_accuracies = []
            word_accuracies = []
            bleu_scores = []
            edit_distances = []
            all_corrections = {}
            
            for i, (result, reference) in enumerate(zip(results, reference_texts)):
                if reference:  # Only process pages with reference text
                    char_acc = self.calculate_character_accuracy(result.text, reference)
                    word_acc = self.calculate_word_accuracy(result.text, reference)
                    bleu = self.calculate_bleu_score(result.text, reference)
                    edit_dist = self.calculate_edit_distance(result.text, reference)
                    
                    char_accuracies.append(char_acc)
                    word_accuracies.append(word_acc)
                    bleu_scores.append(bleu)
                    edit_distances.append(edit_dist)
                    
                    # Store corrections needed
                    if result.text != reference:
                        all_corrections[f"page_{result.page_number}"] = reference
            
            # Calculate averages
            avg_char_accuracy = sum(char_accuracies) / len(char_accuracies) if char_accuracies else 0.0
            avg_word_accuracy = sum(word_accuracies) / len(word_accuracies) if word_accuracies else 0.0
            avg_bleu_score = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0
            avg_edit_distance = sum(edit_distances) / len(edit_distances) if edit_distances else 0
            
            # Convert to user rating (1-10 scale)
            user_rating = int(avg_char_accuracy * 10)
            
            return AccuracyReport(
                engine_name=engine_name,
                character_accuracy=avg_char_accuracy,
                word_accuracy=avg_word_accuracy,
                bleu_score=avg_bleu_score,
                edit_distance=int(avg_edit_distance),
                manual_corrections=all_corrections,
                user_rating=user_rating,
                comments=f"Automated accuracy calculation based on {len(char_accuracies)} pages"
            )
            
        except Exception as e:
            self.quality_logger.error(f"Comprehensive accuracy report failed for {engine_name}: {str(e)}")
            return AccuracyReport(
                engine_name=engine_name,
                character_accuracy=0.0,
                word_accuracy=0.0,
                bleu_score=0.0,
                edit_distance=0,
                manual_corrections={},
                user_rating=0,
                comments=f"Accuracy calculation failed: {str(e)}"
            )