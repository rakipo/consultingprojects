"""Output management system for organized file structure and multiple formats."""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

from ..models.data_models import OCRResult, ComparisonReport
from ..utils.exceptions import OutputGenerationException
from ..utils.logging_config import get_logger_config


class OutputManager:
    """Manages output file generation and organization."""
    
    def __init__(self, base_output_dir: str = "output"):
        """
        Initialize output manager.
        
        Args:
            base_output_dir: Base directory for all outputs
        """
        self.base_output_dir = Path(base_output_dir)
        self.logger_config = get_logger_config()
        self.process_logger = self.logger_config.get_process_logger()
        self.error_logger = self.logger_config.get_error_logger()
        
        # Create base output directory
        self.base_output_dir.mkdir(exist_ok=True)
    
    def create_output_structure(self, timestamp: str = None) -> str:
        """
        Create timestamped output directory structure.
        
        Args:
            timestamp: Custom timestamp string, or None for auto-generation
            
        Returns:
            Path to the created output directory
        """
        try:
            if timestamp is None:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            output_dir = self.base_output_dir / timestamp
            output_dir.mkdir(parents=True, exist_ok=True)
            
            self.process_logger.info(f"Created output directory: {output_dir}")
            return str(output_dir)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to create output structure: {str(e)}")
    
    def create_method_directory(self, base_dir: str, method_name: str) -> str:
        """
        Create method-specific subdirectory.
        
        Args:
            base_dir: Base output directory
            method_name: OCR method/engine name
            
        Returns:
            Path to the method directory
        """
        try:
            method_dir = Path(base_dir) / method_name
            method_dir.mkdir(parents=True, exist_ok=True)
            
            self.process_logger.debug(f"Created method directory: {method_dir}")
            return str(method_dir)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to create method directory: {str(e)}")
    
    def save_page_csv(self, data: List[List[str]], page_num: int, method: str, 
                     output_dir: str, include_metadata: bool = True) -> str:
        """
        Save page data as CSV file.
        
        Args:
            data: List of rows, each row is a list of strings
            page_num: Page number
            method: OCR method name
            output_dir: Output directory path
            include_metadata: Whether to include metadata in CSV
            
        Returns:
            Path to saved CSV file
        """
        try:
            method_dir = self.create_method_directory(output_dir, method)
            csv_path = Path(method_dir) / f"page_{page_num:03d}.csv"
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Add metadata header if requested
                if include_metadata:
                    writer.writerow([f"# Page {page_num} - OCR Method: {method}"])
                    writer.writerow([f"# Generated: {datetime.now().isoformat()}"])
                    writer.writerow([])  # Empty row separator
                
                # Write data
                for row in data:
                    writer.writerow(row)
            
            self.process_logger.info(f"Saved CSV: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to save CSV for page {page_num}: {str(e)}")
    
    def save_page_excel(self, data: List[List[str]], page_num: int, method: str, 
                       output_dir: str, include_metadata: bool = True) -> str:
        """
        Save page data as Excel file.
        
        Args:
            data: List of rows, each row is a list of strings
            page_num: Page number
            method: OCR method name
            output_dir: Output directory path
            include_metadata: Whether to include metadata sheet
            
        Returns:
            Path to saved Excel file
        """
        try:
            method_dir = self.create_method_directory(output_dir, method)
            excel_path = Path(method_dir) / f"page_{page_num:03d}.xlsx"
            
            # Create DataFrame
            df = pd.DataFrame(data)
            
            # Create Excel writer
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Write main data
                df.to_excel(writer, sheet_name=f'Page_{page_num}', index=False, header=False)
                
                # Add metadata sheet if requested
                if include_metadata:
                    metadata = {
                        'Property': ['Page Number', 'OCR Method', 'Generated Time', 'Total Rows'],
                        'Value': [page_num, method, datetime.now().isoformat(), len(data)]
                    }
                    metadata_df = pd.DataFrame(metadata)
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            self.process_logger.info(f"Saved Excel: {excel_path}")
            return str(excel_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to save Excel for page {page_num}: {str(e)}")
    
    def save_consolidated_text(self, all_text: Dict[int, str], method: str, 
                             output_dir: str, include_metadata: bool = True) -> str:
        """
        Save consolidated text from all pages.
        
        Args:
            all_text: Dictionary mapping page numbers to extracted text
            method: OCR method name
            output_dir: Output directory path
            include_metadata: Whether to include metadata in text file
            
        Returns:
            Path to saved text file
        """
        try:
            method_dir = self.create_method_directory(output_dir, method)
            text_path = Path(method_dir) / "consolidated_text.txt"
            
            with open(text_path, 'w', encoding='utf-8') as textfile:
                # Add metadata header if requested
                if include_metadata:
                    textfile.write(f"# Consolidated Text - OCR Method: {method}\n")
                    textfile.write(f"# Generated: {datetime.now().isoformat()}\n")
                    textfile.write(f"# Total Pages: {len(all_text)}\n")
                    textfile.write("=" * 50 + "\n\n")
                
                # Write text for each page
                for page_num in sorted(all_text.keys()):
                    text = all_text[page_num]
                    textfile.write(f"--- Page {page_num} ---\n")
                    textfile.write(text)
                    textfile.write("\n\n")
            
            self.process_logger.info(f"Saved consolidated text: {text_path}")
            return str(text_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to save consolidated text: {str(e)}")
    
    def save_ocr_results(self, results: List[OCRResult], method: str, output_dir: str) -> Dict[str, str]:
        """
        Save OCR results in multiple formats.
        
        Args:
            results: List of OCR results
            method: OCR method name
            output_dir: Output directory path
            
        Returns:
            Dictionary of saved file paths
        """
        saved_files = {}
        
        try:
            # Prepare data for different formats
            all_text = {}
            csv_data_by_page = {}
            
            for result in results:
                page_num = result.page_number
                text = result.text
                
                # Store text for consolidated file
                all_text[page_num] = text
                
                # Prepare CSV data (split text into rows)
                lines = text.split('\n')
                csv_data = [[line.strip()] for line in lines if line.strip()]
                if not csv_data:
                    csv_data = [['[No text detected]']]
                
                csv_data_by_page[page_num] = csv_data
            
            # Save files for each page
            for page_num, csv_data in csv_data_by_page.items():
                # Save CSV
                csv_path = self.save_page_csv(csv_data, page_num, method, output_dir)
                saved_files[f'page_{page_num}_csv'] = csv_path
                
                # Save Excel - COMMENTED OUT due to NumPy compatibility issues
                # excel_path = self.save_page_excel(csv_data, page_num, method, output_dir)
                # saved_files[f'page_{page_num}_excel'] = excel_path
            
            # Save consolidated text
            text_path = self.save_consolidated_text(all_text, method, output_dir)
            saved_files['consolidated_text'] = text_path
            
            # Save detailed results as JSON
            json_path = self.save_detailed_results_json(results, method, output_dir)
            saved_files['detailed_json'] = json_path
            
            return saved_files
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to save OCR results: {str(e)}")
    
    def save_detailed_results_json(self, results: List[OCRResult], method: str, output_dir: str) -> str:
        """
        Save detailed OCR results as JSON.
        
        Args:
            results: List of OCR results
            method: OCR method name
            output_dir: Output directory path
            
        Returns:
            Path to saved JSON file
        """
        try:
            method_dir = self.create_method_directory(output_dir, method)
            json_path = Path(method_dir) / "detailed_results.json"
            
            # Convert results to serializable format
            json_data = {
                'method': method,
                'generated_time': datetime.now().isoformat(),
                'total_pages': len(results),
                'results': []
            }
            
            for result in results:
                result_data = {
                    'page_number': result.page_number,
                    'text': result.text,
                    'confidence_score': result.confidence_score,
                    'processing_time': result.processing_time,
                    'engine_name': result.engine_name,
                    'timestamp': result.timestamp.isoformat() if result.timestamp else None,
                    'bounding_boxes': [
                        {
                            'x': bbox.x,
                            'y': bbox.y,
                            'width': bbox.width,
                            'height': bbox.height
                        }
                        for bbox in result.bounding_boxes
                    ]
                }
                json_data['results'].append(result_data)
            
            # Save JSON
            with open(json_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(json_data, jsonfile, indent=2, ensure_ascii=False)
            
            self.process_logger.info(f"Saved detailed JSON: {json_path}")
            return str(json_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to save detailed JSON: {str(e)}")
    
    def save_comparison_report(self, report: ComparisonReport, output_dir: str) -> str:
        """
        Save comparison report across all engines.
        
        Args:
            report: Comparison report
            output_dir: Output directory path
            
        Returns:
            Path to saved comparison report
        """
        try:
            report_path = Path(output_dir) / "comparison_report.json"
            
            # Convert report to serializable format
            report_data = {
                'generated_time': datetime.now().isoformat(),
                'best_performing_engine': report.best_performing_engine,
                'quality_rankings': report.quality_rankings,
                'processing_times': report.processing_times,
                'cost_analysis': report.cost_analysis,
                'engine_results': {}
            }
            
            # Add engine results
            for engine_name, result in report.engine_results.items():
                report_data['engine_results'][engine_name] = {
                    'confidence_score': result.confidence_score,
                    'processing_time': result.processing_time,
                    'text_length': len(result.text),
                    'bounding_boxes_count': len(result.bounding_boxes)
                }
            
            # Save JSON
            with open(report_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(report_data, jsonfile, indent=2, ensure_ascii=False)
            
            self.process_logger.info(f"Saved comparison report: {report_path}")
            return str(report_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to save comparison report: {str(e)}")
    
    def get_output_summary(self, output_dir: str) -> Dict[str, Any]:
        """
        Get summary of generated output files.
        
        Args:
            output_dir: Output directory path
            
        Returns:
            Dictionary with output summary
        """
        try:
            output_path = Path(output_dir)
            
            summary = {
                'output_directory': str(output_path),
                'created_time': datetime.now().isoformat(),
                'methods': {},
                'total_files': 0
            }
            
            # Scan for method directories
            for method_dir in output_path.iterdir():
                if method_dir.is_dir():
                    method_name = method_dir.name
                    files = list(method_dir.glob('*'))
                    
                    summary['methods'][method_name] = {
                        'directory': str(method_dir),
                        'file_count': len(files),
                        'files': [f.name for f in files]
                    }
                    summary['total_files'] += len(files)
            
            # Check for comparison report
            comparison_report = output_path / "comparison_report.json"
            if comparison_report.exists():
                summary['comparison_report'] = str(comparison_report)
                summary['total_files'] += 1
            
            return summary
            
        except Exception as e:
            self.error_logger.error(f"Failed to generate output summary: {str(e)}")
            return {'error': str(e)}