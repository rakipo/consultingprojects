# Design Document

## Overview

The Telugu Document OCR system is designed as a modular Python application that evaluates and utilizes multiple OCR engines to extract text from scanned Telugu documents. The system follows a plugin-based architecture where different OCR methods can be tested and compared systematically. The application processes PDF inputs, converts them to images, applies various OCR techniques, and outputs results in multiple formats with quality assessment.

## Architecture

The system follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           Main Controller               │
├─────────────────────────────────────────┤
│         OCR Engine Manager             │
├─────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Engine1 │ │ Engine2 │ │ Engine3 │   │
│  └─────────┘ └─────────┘ └─────────┘   │
├─────────────────────────────────────────┤
│      Document Processor                 │
├─────────────────────────────────────────┤
│       Output Manager                    │
├─────────────────────────────────────────┤
│      Quality Assessor                   │
└─────────────────────────────────────────┘
```

### Key Components:

1. **Document Processor**: Handles PDF to image conversion and preprocessing
2. **OCR Engine Manager**: Coordinates multiple OCR engines and manages their execution
3. **Individual OCR Engines**: Wrapper classes for different OCR solutions
4. **Output Manager**: Handles file output in multiple formats with organized directory structure
5. **Quality Assessor**: Evaluates extraction quality and provides improvement recommendations

## Components and Interfaces

### 1. Document Processor (`document_processor.py`)

**Purpose**: Convert PDF to images and apply preprocessing for better OCR results

**Key Methods**:
- `convert_pdf_to_images(pdf_path: str) -> List[PIL.Image]`
- `preprocess_image(image: PIL.Image) -> PIL.Image`
- `enhance_for_telugu(image: PIL.Image) -> PIL.Image`

**Dependencies**: 
- `pdf2image` for PDF conversion
- `PIL/Pillow` for image processing
- `opencv-python` for advanced preprocessing

### 2. OCR Engine Manager (`ocr_manager.py`)

**Purpose**: Coordinate multiple OCR engines and manage their execution

**Key Methods**:
- `register_engine(engine: OCREngine) -> None`
- `process_with_all_engines(images: List[PIL.Image]) -> Dict[str, OCRResult]`
- `get_engine_comparison() -> ComparisonReport`

### 3. OCR Engine Interface (`ocr_engines/base_engine.py`)

**Purpose**: Abstract base class for all OCR implementations

```python
class OCREngine(ABC):
    @abstractmethod
    def extract_text(self, image: PIL.Image) -> OCRResult
    
    @abstractmethod
    def get_engine_name(self) -> str
    
    @abstractmethod
    def get_confidence_score(self) -> float
    
    @abstractmethod
    def supports_telugu(self) -> bool
```

### 4. Specific OCR Engine Implementations

Based on research, the following OCR engines will be implemented:

#### Free/Open Source Engines:
- **Tesseract OCR** (`tesseract_engine.py`): With Telugu language pack
- **EasyOCR** (`easyocr_engine.py`): Supports Telugu out of the box
- **PaddleOCR** (`paddleocr_engine.py`): Multi-language including Telugu
- **TrOCR** (`trocr_engine.py`): Transformer-based OCR from Microsoft

#### Cloud-based Free Tier Engines:
- **Google Cloud Vision API** (`google_vision_engine.py`): Free tier available
- **Azure Computer Vision** (`azure_vision_engine.py`): Free tier available
- **AWS Textract** (`aws_textract_engine.py`): Free tier available

#### Paid/Premium Engines:
- **ABBYY Cloud OCR** (`abbyy_engine.py`): High accuracy for complex documents
- **Nanonets OCR** (`nanonets_engine.py`): Specialized for handwritten text
- **Mathpix OCR** (`mathpix_engine.py`): Good for structured documents

### 5. Output Manager (`output_manager.py`)

**Purpose**: Handle all output operations with organized file structure

**Key Methods**:
- `create_output_structure(timestamp: str) -> str`
- `save_page_csv(data: List[List[str]], page_num: int, method: str, output_dir: str)`
- `save_page_excel(data: List[List[str]], page_num: int, method: str, output_dir: str)`
- `save_consolidated_text(all_text: Dict[int, str], method: str, output_dir: str)`

**Output Structure**:
```
output/
└── 2024-01-15_14-30-25/
    ├── tesseract/
    │   ├── page_1.csv
    │   ├── page_1.xlsx
    │   ├── page_2.csv
    │   ├── page_2.xlsx
    │   └── consolidated_text.txt
    ├── easyocr/
    │   └── ...
    └── comparison_report.json
```

### 6. Quality Assessor (`quality_assessor.py`)

**Purpose**: Evaluate extraction quality and provide improvement recommendations

**Key Methods**:
- `assess_text_quality(extracted_text: str, confidence_scores: List[float]) -> QualityReport`
- `detect_telugu_script(text: str) -> float`
- `analyze_table_structure(text: str) -> TableAnalysis`
- `generate_improvement_recommendations(quality_report: QualityReport) -> List[str]`

**Quality Metrics**:
- Telugu script detection percentage
- Confidence score analysis
- Table structure preservation
- Character recognition accuracy estimation

## Data Models

### OCRResult
```python
@dataclass
class OCRResult:
    text: str
    confidence_score: float
    bounding_boxes: List[BoundingBox]
    processing_time: float
    engine_name: str
    page_number: int
```

### QualityReport
```python
@dataclass
class QualityReport:
    overall_score: float
    telugu_detection_rate: float
    confidence_average: float
    table_structure_score: float
    recommendations: List[str]
    issues_detected: List[str]
```

### ComparisonReport
```python
@dataclass
class ComparisonReport:
    engine_results: Dict[str, OCRResult]
    best_performing_engine: str
    quality_rankings: List[Tuple[str, float]]
    processing_times: Dict[str, float]
    cost_analysis: Dict[str, float]
```

## Error Handling

### Exception Hierarchy
- `OCRException`: Base exception for all OCR-related errors
- `EngineNotAvailableException`: When an OCR engine is not properly configured
- `UnsupportedFormatException`: When input format is not supported
- `APILimitExceededException`: When cloud API limits are reached
- `QualityThresholdException`: When extraction quality is below acceptable levels
- `PreprocessingException`: When image preprocessing fails
- `OutputGenerationException`: When output file creation fails

### Error Recovery Strategies
1. **Engine Fallback**: If one OCR engine fails, continue with others
2. **Preprocessing Retry**: Apply different preprocessing techniques on failure
3. **Partial Results**: Save partial results even if some pages fail
4. **Graceful Degradation**: Continue processing with available engines
5. **Detailed Error Logging**: Log all exceptions with context for debugging

### Exception Handling Implementation
- Try-catch blocks around each OCR engine execution
- Comprehensive error logging with timestamps and context
- Graceful handling of API timeouts and rate limits
- Recovery mechanisms for temporary failures

## Testing Strategy

### Unit Tests
- Test each OCR engine wrapper independently
- Test document preprocessing functions
- Test output formatting and file operations
- Test quality assessment algorithms

### Integration Tests
- Test complete workflow from PDF input to final output
- Test error handling and recovery mechanisms
- Test output directory structure creation
- Test comparison report generation

### Performance Tests
- Benchmark processing time for different document sizes
- Memory usage analysis for large PDF files
- API rate limiting and timeout handling
- Concurrent processing capabilities

### Quality Tests
- Test with known Telugu documents for accuracy validation
- Compare results against manually verified ground truth
- Test with different document types (printed vs handwritten)
- Validate table structure preservation

## Configuration Management

### Engine Configuration (`config/engines.yaml`)
```yaml
engines:
  tesseract:
    enabled: true
    language: "tel"
    config: "--psm 6"
  
  easyocr:
    enabled: true
    languages: ["te", "en"]
    gpu: false
  
  google_vision:
    enabled: false
    api_key_path: "credentials/google_vision_key.json"
    
  azure_vision:
    enabled: false
    subscription_key: "env:AZURE_VISION_KEY"
    endpoint: "env:AZURE_VISION_ENDPOINT"
```

### Processing Configuration (`config/processing.yaml`)
```yaml
preprocessing:
  resize_factor: 2.0
  noise_reduction: true
  contrast_enhancement: true
  
output:
  formats: ["csv", "xlsx", "txt"]
  include_confidence: true
  
quality:
  minimum_confidence: 0.6
  telugu_detection_threshold: 0.7
```

## Logging System

### Logging Configuration (`logging_config.py`)
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Format**: `[TIMESTAMP] [LEVEL] [MODULE] - MESSAGE`
- **Log Files**: 
  - `logs/ocr_processing.log` - Main processing logs
  - `logs/engine_performance.log` - OCR engine performance metrics
  - `logs/errors.log` - Error-specific logs

### Logging Components
- **Process Logger**: Tracks overall processing flow and timing
- **Engine Logger**: Records individual OCR engine execution details
- **Quality Logger**: Logs quality assessment results and recommendations
- **Error Logger**: Captures all exceptions and error recovery attempts

## Manual Evaluation and Feedback System

### Evaluation Interface (`evaluation_manager.py`)

**Purpose**: Provide manual evaluation interface for accuracy assessment

**Key Methods**:
- `generate_evaluation_form(ocr_results: Dict[str, OCRResult]) -> str`
- `create_feedback_csv(original_images: List, extracted_texts: Dict) -> str`
- `process_manual_feedback(feedback_file: str) -> AccuracyReport`
- `update_engine_accuracy_scores(feedback_data: Dict) -> None`

### Evaluation Output Files

#### 1. Manual Evaluation CSV (`evaluation_form.csv`)
```csv
Page,Engine,Extracted_Text,Correct_Text,Accuracy_Score,Comments,Issues_Found
1,tesseract,"తెలుగు టెక్స్ట్","[USER_INPUT]","[USER_SCORE]","[USER_COMMENTS]","[ISSUES]"
1,easyocr,"తెలుగు టెక్స్ట్","[USER_INPUT]","[USER_SCORE]","[USER_COMMENTS]","[ISSUES]"
```

#### 2. Feedback Form Template (`feedback_form.docx`)
- Side-by-side comparison of original image and extracted text
- Rating scale (1-10) for each extraction
- Text correction fields
- Issue categorization (character errors, word errors, table structure, etc.)
- Overall engine ranking section

### Feedback Collection Framework

**Feedback Categories**:
1. **Character-level Accuracy**: Individual Telugu character recognition
2. **Word-level Accuracy**: Complete word recognition
3. **Table Structure**: Preservation of table layout and data
4. **Handwriting Recognition**: Accuracy for handwritten Telugu text
5. **Overall Readability**: General quality of extracted text

**Feedback Questions**:
1. Rate the overall accuracy of text extraction (1-10)
2. Which specific characters were incorrectly recognized?
3. Were table structures properly preserved?
4. How well did the engine handle handwritten text?
5. What preprocessing improvements would help?
6. Which engine performed best for your document type?

## Accuracy Reporting and Model Performance

### Accuracy Metrics (`accuracy_calculator.py`)

**Key Metrics**:
- **Character-level Accuracy**: `(Correct_Characters / Total_Characters) * 100`
- **Word-level Accuracy**: `(Correct_Words / Total_Words) * 100`
- **BLEU Score**: For overall text similarity comparison
- **Edit Distance**: Levenshtein distance between extracted and correct text
- **Confidence Correlation**: How well confidence scores predict accuracy

### Performance Dashboard (`performance_report.html`)

**Generated Report Includes**:
1. **Engine Comparison Table**:
   ```
   Engine Name    | Avg Accuracy | Processing Time | Cost | Telugu Support
   Tesseract      | 78.5%       | 2.3s           | Free | Good
   EasyOCR        | 82.1%       | 4.1s           | Free | Excellent
   Google Vision  | 85.7%       | 1.8s           | $1.50| Excellent
   ```

2. **Accuracy Breakdown by Document Type**:
   - Printed text accuracy
   - Handwritten text accuracy  
   - Table extraction accuracy
   - Mixed content accuracy

3. **Performance Trends**:
   - Accuracy improvement over time with feedback
   - Processing speed comparisons
   - Cost-effectiveness analysis

### Continuous Learning System

**Feedback Integration**:
- Store manual corrections in `feedback_database.json`
- Track accuracy improvements after preprocessing adjustments
- Maintain engine performance history
- Generate recommendations based on accumulated feedback

**Adaptive Preprocessing**:
- Adjust preprocessing parameters based on feedback
- Learn optimal settings for different document types
- Implement feedback-driven preprocessing pipelines

This enhanced design provides comprehensive logging, manual evaluation capabilities, and detailed accuracy reporting to continuously improve the Telugu OCR system performance.