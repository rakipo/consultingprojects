# Telugu Manuscript Reader

A comprehensive Python tool for extracting Telugu text from scanned PDF manuscripts using multiple OCR methods.

## Features

- **Multiple OCR Methods**: Supports Tesseract OCR and Google Cloud Vision API
- **Image Preprocessing**: Advanced image enhancement for better OCR results
- **Telugu Language Support**: Optimized for Telugu script recognition
- **Multiple Output Formats**: Text, PDF, and JSON output
- **Handwritten Text Support**: Specialized for handwritten Telugu manuscripts
- **Debug Images**: Saves processed images for quality assessment

## Setup

### 1. Activate the Conda Environment

```bash
conda activate manuscript_reader
```

### 2. Install System Dependencies

The following are already installed:
- Tesseract OCR with Telugu language support
- Python packages (see requirements.txt)

### 3. Verify Installation

```bash
# Check if Tesseract supports Telugu
tesseract --list-langs | grep tel

# Should output: tel
```

## Usage

### Quick Start

Run the simple extraction script on your test PDF:

```bash
python run_extraction.py
```

### Advanced Usage

Use the main script with custom options:

```bash
# Basic usage
python telugu_manuscript_reader.py test_manu.pdf

# With custom output directory
python telugu_manuscript_reader.py test_manu.pdf -o my_output

# With higher DPI for better quality
python telugu_manuscript_reader.py test_manu.pdf -d 600

# Skip image preprocessing
python telugu_manuscript_reader.py test_manu.pdf --no-preprocessing

# Use specific OCR methods
python telugu_manuscript_reader.py test_manu.pdf --methods tesseract google_vision
```

### Command Line Options

- `pdf_path`: Path to the PDF file (required)
- `-o, --output`: Output directory (default: "Outputs")
- `-d, --dpi`: DPI for PDF conversion (default: 300)
- `--methods`: OCR methods to use (choices: tesseract, google_vision)
- `--no-preprocessing`: Skip image preprocessing

## Output Files

The tool generates organized output files in the following structure:

```
Outputs/
└── YYYYMMDD_HHMMSS/          # Timestamp folder
    ├── tesseract/            # Results from Tesseract OCR
    │   ├── telugu_extraction_tesseract.json
    │   ├── telugu_extraction_tesseract.txt
    │   └── telugu_extraction_tesseract.pdf
    ├── google_vision/        # Results from Google Vision (if used)
    │   ├── telugu_extraction_google_vision.json
    │   ├── telugu_extraction_google_vision.txt
    │   └── telugu_extraction_google_vision.pdf
    ├── extraction_summary.json    # Combined summary
    └── combined_extraction.txt    # All results combined
```

**File Types:**
1. **JSON**: Detailed results with confidence scores and method comparison
2. **TXT**: Plain text file with extracted Telugu text
3. **PDF**: Formatted PDF with Telugu text (if Telugu fonts are available)
4. **Debug Images**: Processed images for each page (saved in main directory)

## OCR Methods

### 1. Tesseract OCR (Default)
- **Pros**: Free, local processing, good for printed text
- **Cons**: Limited accuracy for handwritten text
- **Best for**: Clear printed Telugu text

### 2. Google Cloud Vision API (Optional)
- **Pros**: Excellent for handwritten text, high accuracy
- **Cons**: Requires API key, internet connection, costs money
- **Setup**: 
  ```bash
  # Install Google Cloud SDK
  # Set up authentication
  export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
  ```

## Image Preprocessing

The tool applies several preprocessing steps to improve OCR accuracy:

1. **Denoising**: Removes noise from scanned images
2. **Contrast Enhancement**: Improves text visibility
3. **Sharpening**: Enhances text edges
4. **Binarization**: Converts to black and white for better recognition

## Troubleshooting

### Low OCR Accuracy

1. **Check Image Quality**: Ensure the PDF has high-quality scans
2. **Adjust DPI**: Try higher DPI values (600, 900)
3. **Review Debug Images**: Check the processed images in the current directory
4. **Try Different Methods**: Use Google Cloud Vision for handwritten text

### Telugu Font Issues

If Telugu text doesn't display properly in the output PDF:
1. Install Telugu fonts on your system
2. The tool will fall back to default fonts if Telugu fonts aren't found

### Memory Issues

For large PDFs:
1. Process pages in batches
2. Reduce DPI if memory is limited
3. Use lower resolution for initial testing

## File Structure

```
manuscript_Reader/
├── telugu_manuscript_reader.py  # Main extraction tool
├── run_extraction.py            # Simple usage script
├── requirements.txt             # Python dependencies
├── README.md                   # This file
├── test_manu.pdf              # Your test manuscript
├── output/                    # Generated output files
└── debug_page_*.png          # Debug images (generated)
```

## Example Output

```
🔍 Telugu Manuscript Reader
==================================================
Processing: /path/to/test_manu.pdf

Initializing Telugu Manuscript Reader...
Converting PDF to images and extracting text...
Saving results...

============================================================
✅ EXTRACTION COMPLETE!
============================================================
📄 Total pages processed: 5
📝 Total text extracted: 1,234 characters
🎯 Average confidence: 78.5%
📁 Output files (organized by method):
   TESSERACT_JSON: Outputs/20241201_143022/tesseract/telugu_extraction_tesseract.json
   TESSERACT_TXT: Outputs/20241201_143022/tesseract/telugu_extraction_tesseract.txt
   TESSERACT_PDF: Outputs/20241201_143022/tesseract/telugu_extraction_tesseract.pdf
   SUMMARY: Outputs/20241201_143022/extraction_summary.json
   COMBINED_TXT: Outputs/20241201_143022/combined_extraction.txt

📂 Folder structure:
   Outputs/20241201_143022/
   ├── tesseract/
   │   ├── telugu_extraction_tesseract.json
   │   ├── telugu_extraction_tesseract.txt
   │   └── telugu_extraction_tesseract.pdf
   ├── extraction_summary.json
   └── combined_extraction.txt
```

## Tips for Better Results

1. **High-Quality Scans**: Use at least 300 DPI for scanning
2. **Good Lighting**: Ensure even lighting when photographing manuscripts
3. **Clean Images**: Remove shadows and ensure text is clearly visible
4. **Handwritten Text**: Use Google Cloud Vision API for better handwritten text recognition
5. **Mixed Content**: The tool handles both printed and handwritten Telugu text

## Support

For issues or questions:
1. Check the log file: `telugu_ocr.log`
2. Review debug images to assess preprocessing quality
3. Try different OCR methods and settings
4. Ensure your PDF is not password-protected or corrupted
