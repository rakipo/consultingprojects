"""Quality assessment system for OCR results."""

import re
import unicodedata
from typing import List, Dict, Tuple, Optional
from collections import Counter

from ..models.data_models import OCRResult, QualityReport, TableAnalysis
from ..utils.logging_config import get_logger_config


class QualityAssessor:
    """Assesses quality of OCR extraction results."""
    
    def __init__(self, config: Dict = None):
        """Initialize quality assessor."""
        self.config = config or {}
        self.logger_config = get_logger_config()
        self.quality_logger = self.logger_config.get_quality_logger()
        
        # Telugu Unicode ranges
        self.telugu_ranges = [
            (0x0C00, 0x0C7F),  # Telugu block
            (0x0C80, 0x0CFF),  # Kannada block (sometimes used for Telugu)
        ]
        
        # Quality thresholds
        self.min_confidence = self.config.get('minimum_confidence', 0.6)
        self.telugu_threshold = self.config.get('telugu_detection_threshold', 0.7)
        self.table_threshold = self.config.get('table_detection_threshold', 0.5)
    
    def assess_text_quality(self, extracted_text: str, confidence_scores: List[float], 
                           engine_name: str) -> QualityReport:
        """
        Assess overall quality of extracted text.
        
        Args:
            extracted_text: The extracted text
            confidence_scores: List of confidence scores
            engine_name: Name of the OCR engine
            
        Returns:
            QualityReport with quality metrics and recommendations
        """
        try:
            # Calculate individual metrics
            telugu_rate = self.detect_telugu_script(extracted_text)
            confidence_avg = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            table_analysis = self.analyze_table_structure(extracted_text)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                telugu_rate, confidence_avg, table_analysis.confidence
            )
            
            # Generate recommendations
            recommendations = self.generate_improvement_recommendations(
                telugu_rate, confidence_avg, table_analysis, extracted_text
            )
            
            # Detect issues
            issues = self._detect_issues(extracted_text, telugu_rate, confidence_avg)
            
            # Log quality assessment
            self.logger_config.log_quality_assessment(engine_name, overall_score, telugu_rate)
            
            return QualityReport(
                overall_score=overall_score,
                telugu_detection_rate=telugu_rate,
                confidence_average=confidence_avg,
                table_structure_score=table_analysis.confidence,
                recommendations=recommendations,
                issues_detected=issues,
                engine_name=engine_name
            )
            
        except Exception as e:
            self.quality_logger.error(f"Quality assessment failed for {engine_name}: {str(e)}")
            return self._create_fallback_report(engine_name)
    
    def detect_telugu_script(self, text: str) -> float:
        """
        Detect percentage of Telugu script in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Percentage of Telugu characters (0.0 to 1.0)
        """
        if not text:
            return 0.0
        
        try:
            total_chars = 0
            telugu_chars = 0
            
            for char in text:
                # Skip whitespace and punctuation
                if char.isspace() or not char.isalnum():
                    continue
                
                total_chars += 1
                
                # Check if character is in Telugu Unicode ranges
                char_code = ord(char)
                for start, end in self.telugu_ranges:
                    if start <= char_code <= end:
                        telugu_chars += 1
                        break
            
            if total_chars == 0:
                return 0.0
            
            return telugu_chars / total_chars
            
        except Exception as e:
            self.quality_logger.error(f"Telugu detection failed: {str(e)}")
            return 0.0
    
    def analyze_table_structure(self, text: str) -> TableAnalysis:
        """
        Analyze table structure preservation in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            TableAnalysis with table structure information
        """
        try:
            lines = text.split('\n')
            
            # Detect table indicators
            table_indicators = 0
            potential_table_lines = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for table-like patterns
                if self._is_table_line(line):
                    potential_table_lines += 1
                    table_indicators += self._count_table_indicators(line)
            
            # Determine if tables are present
            has_tables = potential_table_lines >= 2 and table_indicators >= 4
            
            # Calculate structure preservation confidence
            if has_tables:
                # Check alignment and consistency
                structure_confidence = self._assess_table_alignment(lines)
            else:
                structure_confidence = 1.0  # No tables to preserve
            
            return TableAnalysis(
                has_tables=has_tables,
                table_count=self._estimate_table_count(lines),
                structure_preserved=structure_confidence > self.table_threshold,
                confidence=structure_confidence
            )
            
        except Exception as e:
            self.quality_logger.error(f"Table analysis failed: {str(e)}")
            return TableAnalysis(False, 0, False, 0.0)
    
    def _is_table_line(self, line: str) -> bool:
        """Check if a line appears to be part of a table."""
        # Common table separators
        separators = ['|', '\t', '  ', ':', '-', '│', '┃']
        
        separator_count = 0
        for sep in separators:
            separator_count += line.count(sep)
        
        # Line with multiple separators likely part of table
        return separator_count >= 2
    
    def _count_table_indicators(self, line: str) -> int:
        """Count table structure indicators in a line."""
        indicators = ['|', '\t', '│', '┃', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']
        
        count = 0
        for indicator in indicators:
            count += line.count(indicator)
        
        return count
    
    def _estimate_table_count(self, lines: List[str]) -> int:
        """Estimate number of tables in text."""
        table_count = 0
        in_table = False
        consecutive_table_lines = 0
        
        for line in lines:
            line = line.strip()
            
            if self._is_table_line(line):
                if not in_table:
                    in_table = True
                    consecutive_table_lines = 1
                else:
                    consecutive_table_lines += 1
            else:
                if in_table and consecutive_table_lines >= 2:
                    table_count += 1
                in_table = False
                consecutive_table_lines = 0
        
        # Check if we ended in a table
        if in_table and consecutive_table_lines >= 2:
            table_count += 1
        
        return table_count
    
    def _assess_table_alignment(self, lines: List[str]) -> float:
        """Assess how well table alignment is preserved."""
        table_lines = [line for line in lines if self._is_table_line(line.strip())]
        
        if len(table_lines) < 2:
            return 1.0
        
        # Check consistency of separator positions
        separator_positions = []
        
        for line in table_lines:
            positions = []
            for i, char in enumerate(line):
                if char in ['|', '\t', '│', '┃']:
                    positions.append(i)
            separator_positions.append(positions)
        
        if not separator_positions:
            return 0.5
        
        # Calculate alignment consistency
        # This is a simplified heuristic
        avg_separators = sum(len(pos) for pos in separator_positions) / len(separator_positions)
        consistency = 1.0 - (abs(len(separator_positions[0]) - avg_separators) / max(avg_separators, 1))
        
        return max(0.0, min(1.0, consistency))
    
    def _calculate_overall_score(self, telugu_rate: float, confidence_avg: float, 
                               table_confidence: float) -> float:
        """Calculate overall quality score."""
        # Weighted average of different quality metrics
        weights = {
            'telugu': 0.4,      # Telugu detection is important
            'confidence': 0.4,   # OCR confidence is important
            'table': 0.2        # Table structure preservation
        }
        
        score = (
            weights['telugu'] * telugu_rate +
            weights['confidence'] * confidence_avg +
            weights['table'] * table_confidence
        )
        
        return max(0.0, min(1.0, score))
    
    def generate_improvement_recommendations(self, telugu_rate: float, confidence_avg: float,
                                           table_analysis: TableAnalysis, text: str) -> List[str]:
        """Generate recommendations for improving OCR quality."""
        recommendations = []
        
        # Telugu detection recommendations
        if telugu_rate < self.telugu_threshold:
            recommendations.append(
                f"Low Telugu script detection ({telugu_rate:.1%}). "
                "Consider using engines with better Telugu support like EasyOCR or Google Vision."
            )
        
        # Confidence recommendations
        if confidence_avg < self.min_confidence:
            recommendations.append(
                f"Low average confidence ({confidence_avg:.1%}). "
                "Try image preprocessing: increase resolution, enhance contrast, or reduce noise."
            )
        
        # Table structure recommendations
        if table_analysis.has_tables and not table_analysis.structure_preserved:
            recommendations.append(
                "Table structure not well preserved. "
                "Consider using engines with better table detection like AWS Textract or ABBYY."
            )
        
        # Text quality recommendations
        if len(text.strip()) < 50:
            recommendations.append(
                "Very little text extracted. Check image quality and ensure text is clearly visible."
            )
        
        # Character quality recommendations
        if self._has_many_special_chars(text):
            recommendations.append(
                "Many special characters detected. This might indicate OCR errors. "
                "Try different preprocessing or OCR engines."
            )
        
        # Generic recommendations if no specific issues found
        if not recommendations:
            if confidence_avg < 0.9:
                recommendations.append(
                    "Consider trying multiple OCR engines and comparing results for best accuracy."
                )
        
        return recommendations
    
    def _detect_issues(self, text: str, telugu_rate: float, confidence_avg: float) -> List[str]:
        """Detect specific issues in the extracted text."""
        issues = []
        
        # Empty or very short text
        if len(text.strip()) < 10:
            issues.append("Very little text extracted")
        
        # Low Telugu content
        if telugu_rate < 0.3:
            issues.append("Low Telugu script content detected")
        
        # Low confidence
        if confidence_avg < 0.5:
            issues.append("Low OCR confidence scores")
        
        # Excessive special characters
        if self._has_many_special_chars(text):
            issues.append("High ratio of special characters (possible OCR errors)")
        
        # Repeated characters (common OCR error)
        if self._has_repeated_chars(text):
            issues.append("Repeated character patterns detected")
        
        # Mixed scripts (might indicate confusion)
        if self._has_mixed_scripts(text):
            issues.append("Mixed scripts detected (might indicate OCR confusion)")
        
        return issues
    
    def _has_many_special_chars(self, text: str) -> bool:
        """Check if text has unusually many special characters."""
        if not text:
            return False
        
        special_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
        total_chars = len(text)
        
        return (special_chars / total_chars) > 0.3 if total_chars > 0 else False
    
    def _has_repeated_chars(self, text: str) -> bool:
        """Check for repeated character patterns."""
        # Look for patterns like "aaaa" or "1111"
        pattern = re.compile(r'(.)\1{3,}')
        return bool(pattern.search(text))
    
    def _has_mixed_scripts(self, text: str) -> bool:
        """Check if text contains mixed scripts."""
        scripts = set()
        
        for char in text:
            if char.isalpha():
                script = unicodedata.name(char, '').split()[0] if unicodedata.name(char, '') else 'UNKNOWN'
                scripts.add(script)
        
        # More than 2 different scripts might indicate confusion
        return len(scripts) > 2
    
    def _create_fallback_report(self, engine_name: str) -> QualityReport:
        """Create a fallback quality report when assessment fails."""
        return QualityReport(
            overall_score=0.0,
            telugu_detection_rate=0.0,
            confidence_average=0.0,
            table_structure_score=0.0,
            recommendations=["Quality assessment failed. Check OCR engine output manually."],
            issues_detected=["Quality assessment error"],
            engine_name=engine_name
        )
    
    def compare_quality_reports(self, reports: List[QualityReport]) -> Dict[str, any]:
        """
        Compare multiple quality reports and provide insights.
        
        Args:
            reports: List of quality reports to compare
            
        Returns:
            Dictionary with comparison insights
        """
        if not reports:
            return {}
        
        try:
            # Sort by overall score
            sorted_reports = sorted(reports, key=lambda r: r.overall_score, reverse=True)
            
            comparison = {
                'best_engine': sorted_reports[0].engine_name,
                'worst_engine': sorted_reports[-1].engine_name,
                'score_range': {
                    'highest': sorted_reports[0].overall_score,
                    'lowest': sorted_reports[-1].overall_score
                },
                'telugu_detection': {
                    'best': max(reports, key=lambda r: r.telugu_detection_rate),
                    'average': sum(r.telugu_detection_rate for r in reports) / len(reports)
                },
                'confidence': {
                    'best': max(reports, key=lambda r: r.confidence_average),
                    'average': sum(r.confidence_average for r in reports) / len(reports)
                },
                'common_issues': self._find_common_issues(reports),
                'recommendations': self._consolidate_recommendations(reports)
            }
            
            return comparison
            
        except Exception as e:
            self.quality_logger.error(f"Quality comparison failed: {str(e)}")
            return {'error': str(e)}
    
    def _find_common_issues(self, reports: List[QualityReport]) -> List[str]:
        """Find issues that appear in multiple reports."""
        all_issues = []
        for report in reports:
            all_issues.extend(report.issues_detected)
        
        # Count issue frequency
        issue_counts = Counter(all_issues)
        
        # Return issues that appear in more than half the reports
        threshold = len(reports) / 2
        common_issues = [issue for issue, count in issue_counts.items() if count > threshold]
        
        return common_issues
    
    def _consolidate_recommendations(self, reports: List[QualityReport]) -> List[str]:
        """Consolidate recommendations from multiple reports."""
        all_recommendations = []
        for report in reports:
            all_recommendations.extend(report.recommendations)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Limit to top 10 recommendations