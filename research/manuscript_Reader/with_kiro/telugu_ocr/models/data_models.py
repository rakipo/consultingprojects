"""Core data models for the Telugu OCR system."""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime


@dataclass
class BoundingBox:
    """Represents a bounding box for detected text."""
    x: int
    y: int
    width: int
    height: int


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence_score: float
    bounding_boxes: List[BoundingBox]
    processing_time: float
    engine_name: str
    page_number: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class QualityReport:
    """Quality assessment report for OCR results."""
    overall_score: float
    telugu_detection_rate: float
    confidence_average: float
    table_structure_score: float
    recommendations: List[str]
    issues_detected: List[str]
    engine_name: str


@dataclass
class ComparisonReport:
    """Comparison report across multiple OCR engines."""
    engine_results: Dict[str, OCRResult]
    best_performing_engine: str
    quality_rankings: List[Tuple[str, float]]
    processing_times: Dict[str, float]
    cost_analysis: Dict[str, float]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TableAnalysis:
    """Analysis of table structure in extracted text."""
    has_tables: bool
    table_count: int
    structure_preserved: bool
    confidence: float


@dataclass
class AccuracyReport:
    """Manual accuracy evaluation report."""
    engine_name: str
    character_accuracy: float
    word_accuracy: float
    bleu_score: float
    edit_distance: int
    manual_corrections: Dict[str, str]
    user_rating: int  # 1-10 scale
    comments: str