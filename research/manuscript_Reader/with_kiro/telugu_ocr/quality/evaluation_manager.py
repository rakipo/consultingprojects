"""Manual evaluation interface for OCR accuracy assessment."""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from PIL import Image
import pandas as pd

from ..models.data_models import OCRResult, AccuracyReport
from ..utils.exceptions import OutputGenerationException
from ..utils.logging_config import get_logger_config


class EvaluationManager:
    """Manages manual evaluation interface and feedback collection."""
    
    def __init__(self, output_dir: str = "evaluation"):
        """Initialize evaluation manager."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger_config = get_logger_config()
        self.process_logger = self.logger_config.get_process_logger()
        self.error_logger = self.logger_config.get_error_logger()
    
    def generate_evaluation_form(self, ocr_results: Dict[str, List[OCRResult]], 
                                original_images: List[Image.Image] = None) -> str:
        """
        Generate evaluation CSV form for manual correction.
        
        Args:
            ocr_results: Dictionary mapping engine names to OCR results
            original_images: Optional list of original images
            
        Returns:
            Path to generated evaluation CSV file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = self.output_dir / f"evaluation_form_{timestamp}.csv"
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                header = [
                    'Page', 'Engine', 'Extracted_Text', 'Correct_Text', 
                    'Accuracy_Score', 'Comments', 'Issues_Found', 'Confidence_Score'
                ]
                writer.writerow(header)
                
                # Write instructions
                writer.writerow([])
                writer.writerow(['# INSTRUCTIONS:'])
                writer.writerow(['# 1. Review the Extracted_Text column'])
                writer.writerow(['# 2. Enter the correct text in Correct_Text column'])
                writer.writerow(['# 3. Rate accuracy from 1-10 in Accuracy_Score column'])
                writer.writerow(['# 4. Add comments about errors in Comments column'])
                writer.writerow(['# 5. List specific issues in Issues_Found column'])
                writer.writerow([])
                
                # Get all pages
                all_pages = set()
                for results in ocr_results.values():
                    all_pages.update(r.page_number for r in results)
                
                # Write data for each page and engine
                for page_num in sorted(all_pages):
                    for engine_name, results in ocr_results.items():
                        # Find result for this page
                        page_result = next(
                            (r for r in results if r.page_number == page_num), 
                            None
                        )
                        
                        if page_result:
                            # Truncate very long text for readability
                            extracted_text = page_result.text
                            if len(extracted_text) > 500:
                                extracted_text = extracted_text[:500] + "... [TRUNCATED]"
                            
                            writer.writerow([
                                page_num,
                                engine_name,
                                extracted_text.replace('\n', ' | '),  # Replace newlines for CSV
                                '[ENTER_CORRECT_TEXT]',
                                '[1-10]',
                                '[ENTER_COMMENTS]',
                                '[LIST_ISSUES]',
                                f"{page_result.confidence_score:.3f}"
                            ])
                        else:
                            writer.writerow([
                                page_num,
                                engine_name,
                                '[NO_RESULT]',
                                '[ENTER_CORRECT_TEXT]',
                                '0',
                                'No result from this engine',
                                'Engine failed',
                                '0.000'
                            ])
            
            self.process_logger.info(f"Generated evaluation form: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to generate evaluation form: {str(e)}")
    
    def create_feedback_csv(self, original_images: List[Image.Image], 
                           extracted_texts: Dict[str, List[str]]) -> str:
        """
        Create detailed feedback CSV with image references.
        
        Args:
            original_images: List of original images
            extracted_texts: Dictionary mapping engine names to extracted texts
            
        Returns:
            Path to created feedback CSV
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = self.output_dir / f"feedback_form_{timestamp}.csv"
            
            # Save images for reference
            image_dir = self.output_dir / f"images_{timestamp}"
            image_dir.mkdir(exist_ok=True)
            
            image_paths = []
            for i, image in enumerate(original_images, 1):
                image_path = image_dir / f"page_{i:03d}.png"
                image.save(image_path)
                image_paths.append(str(image_path))
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write detailed header
                header = [
                    'Page_Number', 'Image_Path', 'Engine_Name', 'Extracted_Text',
                    'Correct_Text', 'Character_Accuracy', 'Word_Accuracy', 
                    'Overall_Rating', 'Telugu_Quality', 'Table_Quality',
                    'Specific_Errors', 'Improvement_Suggestions', 'Notes'
                ]
                writer.writerow(header)
                
                # Write detailed instructions
                writer.writerow([])
                writer.writerow(['# DETAILED EVALUATION INSTRUCTIONS:'])
                writer.writerow(['# Character_Accuracy: % of characters correctly recognized (0-100)'])
                writer.writerow(['# Word_Accuracy: % of words correctly recognized (0-100)'])
                writer.writerow(['# Overall_Rating: Overall quality rating (1-10)'])
                writer.writerow(['# Telugu_Quality: How well Telugu script was recognized (1-10)'])
                writer.writerow(['# Table_Quality: How well table structure was preserved (1-10, N/A if no tables)'])
                writer.writerow(['# Specific_Errors: List specific types of errors (e.g., "confused ప with బ")'])
                writer.writerow(['# Improvement_Suggestions: What could improve this result'])
                writer.writerow([])
                
                # Write data
                for page_num in range(1, len(original_images) + 1):
                    image_path = image_paths[page_num - 1] if page_num <= len(image_paths) else ""
                    
                    for engine_name, texts in extracted_texts.items():
                        text = texts[page_num - 1] if page_num <= len(texts) else ""
                        
                        writer.writerow([
                            page_num,
                            image_path,
                            engine_name,
                            text.replace('\n', ' | ') if text else '[NO_TEXT]',
                            '[ENTER_CORRECT_TEXT]',
                            '[0-100]',
                            '[0-100]',
                            '[1-10]',
                            '[1-10]',
                            '[1-10 or N/A]',
                            '[LIST_SPECIFIC_ERRORS]',
                            '[IMPROVEMENT_SUGGESTIONS]',
                            '[ADDITIONAL_NOTES]'
                        ])
            
            self.process_logger.info(f"Created feedback CSV: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to create feedback CSV: {str(e)}")
    
    def process_manual_feedback(self, feedback_file: str) -> Dict[str, AccuracyReport]:
        """
        Process manual feedback from CSV file.
        
        Args:
            feedback_file: Path to feedback CSV file
            
        Returns:
            Dictionary mapping engine names to accuracy reports
        """
        try:
            feedback_path = Path(feedback_file)
            if not feedback_path.exists():
                raise FileNotFoundError(f"Feedback file not found: {feedback_file}")
            
            # Read feedback CSV
            df = pd.read_csv(feedback_path, comment='#')
            
            # Group by engine
            accuracy_reports = {}
            
            for engine_name in df['Engine'].unique():
                if pd.isna(engine_name):
                    continue
                
                engine_data = df[df['Engine'] == engine_name]
                
                # Calculate metrics
                accuracy_scores = []
                corrections = {}
                ratings = []
                comments = []
                
                for _, row in engine_data.iterrows():
                    # Skip instruction rows
                    if str(row['Accuracy_Score']).startswith('[') or pd.isna(row['Accuracy_Score']):
                        continue
                    
                    try:
                        accuracy = float(row['Accuracy_Score'])
                        accuracy_scores.append(accuracy)
                        ratings.append(accuracy)
                        
                        # Store corrections
                        if not pd.isna(row['Correct_Text']) and not str(row['Correct_Text']).startswith('['):
                            corrections[f"page_{row['Page']}"] = str(row['Correct_Text'])
                        
                        # Store comments
                        if not pd.isna(row['Comments']) and not str(row['Comments']).startswith('['):
                            comments.append(str(row['Comments']))
                            
                    except (ValueError, TypeError):
                        continue
                
                if accuracy_scores:
                    # Create accuracy report
                    avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
                    avg_rating = sum(ratings) / len(ratings)
                    
                    report = AccuracyReport(
                        engine_name=engine_name,
                        character_accuracy=avg_accuracy / 10.0,  # Convert to 0-1 scale
                        word_accuracy=avg_accuracy / 10.0,  # Simplified
                        bleu_score=0.0,  # Would need reference text to calculate
                        edit_distance=0,  # Would need reference text to calculate
                        manual_corrections=corrections,
                        user_rating=int(avg_rating),
                        comments='; '.join(comments)
                    )
                    
                    accuracy_reports[engine_name] = report
            
            self.process_logger.info(f"Processed feedback for {len(accuracy_reports)} engines")
            return accuracy_reports
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to process manual feedback: {str(e)}")
    
    def update_engine_accuracy_scores(self, feedback_data: Dict[str, AccuracyReport]) -> str:
        """
        Update engine accuracy scores based on feedback.
        
        Args:
            feedback_data: Dictionary of accuracy reports
            
        Returns:
            Path to saved accuracy database
        """
        try:
            accuracy_db_path = self.output_dir / "accuracy_database.json"
            
            # Load existing data if available
            if accuracy_db_path.exists():
                with open(accuracy_db_path, 'r', encoding='utf-8') as f:
                    accuracy_db = json.load(f)
            else:
                accuracy_db = {
                    'created': datetime.now().isoformat(),
                    'engines': {}
                }
            
            # Update with new feedback
            for engine_name, report in feedback_data.items():
                if engine_name not in accuracy_db['engines']:
                    accuracy_db['engines'][engine_name] = {
                        'evaluations': [],
                        'average_accuracy': 0.0,
                        'total_evaluations': 0
                    }
                
                # Add new evaluation
                evaluation = {
                    'timestamp': datetime.now().isoformat(),
                    'character_accuracy': report.character_accuracy,
                    'word_accuracy': report.word_accuracy,
                    'user_rating': report.user_rating,
                    'comments': report.comments
                }
                
                accuracy_db['engines'][engine_name]['evaluations'].append(evaluation)
                accuracy_db['engines'][engine_name]['total_evaluations'] += 1
                
                # Update average
                all_ratings = [e['user_rating'] for e in accuracy_db['engines'][engine_name]['evaluations']]
                accuracy_db['engines'][engine_name]['average_accuracy'] = sum(all_ratings) / len(all_ratings)
            
            # Update timestamp
            accuracy_db['last_updated'] = datetime.now().isoformat()
            
            # Save updated database
            with open(accuracy_db_path, 'w', encoding='utf-8') as f:
                json.dump(accuracy_db, f, indent=2, ensure_ascii=False)
            
            self.process_logger.info(f"Updated accuracy database: {accuracy_db_path}")
            return str(accuracy_db_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to update accuracy scores: {str(e)}")
    
    def create_feedback_questions_template(self) -> str:
        """
        Create a template with feedback questions.
        
        Returns:
            Path to created template file
        """
        try:
            template_path = self.output_dir / "feedback_questions_template.txt"
            
            questions = """
TELUGU OCR EVALUATION FEEDBACK QUESTIONS

Please answer the following questions for each OCR engine result:

1. OVERALL ACCURACY (Rate 1-10):
   How accurately did the engine extract the text overall?
   
2. TELUGU SCRIPT RECOGNITION (Rate 1-10):
   How well did the engine recognize Telugu characters?
   
3. HANDWRITTEN TEXT (Rate 1-10, N/A if not applicable):
   How well did the engine handle handwritten Telugu text?
   
4. TABLE STRUCTURE (Rate 1-10, N/A if not applicable):
   How well was the table structure preserved?
   
5. SPECIFIC CHARACTER ERRORS:
   List any specific Telugu characters that were consistently misrecognized.
   Example: "Confused ప with బ", "Missed మాత్రలు (vowel marks)"
   
6. WORD-LEVEL ERRORS:
   List any complete words that were incorrectly recognized.
   
7. PREPROCESSING SUGGESTIONS:
   What image preprocessing might improve results?
   Options: Higher resolution, Better contrast, Noise reduction, Deskewing
   
8. ENGINE COMPARISON:
   If you evaluated multiple engines, rank them from best to worst.
   
9. DOCUMENT TYPE SUITABILITY:
   Rate how suitable this engine is for your document type (1-10):
   - Printed text
   - Handwritten text
   - Mixed content
   - Tables/structured data
   
10. IMPROVEMENT RECOMMENDATIONS:
    What specific improvements would you suggest for this engine?
    
11. WOULD YOU USE THIS ENGINE AGAIN?
    Yes/No and why?
    
12. ADDITIONAL COMMENTS:
    Any other observations or feedback?

---

INSTRUCTIONS FOR FILLING OUT EVALUATION:
1. Save this template with a new name
2. Answer questions for each engine you tested
3. Be specific about errors and improvements
4. Include examples where possible
5. Rate consistently across all engines
"""
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(questions)
            
            self.process_logger.info(f"Created feedback questions template: {template_path}")
            return str(template_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to create feedback template: {str(e)}")
    
    def generate_evaluation_summary(self, accuracy_reports: Dict[str, AccuracyReport]) -> str:
        """
        Generate summary of evaluation results.
        
        Args:
            accuracy_reports: Dictionary of accuracy reports
            
        Returns:
            Path to generated summary file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_path = self.output_dir / f"evaluation_summary_{timestamp}.txt"
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("TELUGU OCR EVALUATION SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Engines Evaluated: {len(accuracy_reports)}\n\n")
                
                # Sort engines by user rating
                sorted_engines = sorted(
                    accuracy_reports.items(),
                    key=lambda x: x[1].user_rating,
                    reverse=True
                )
                
                f.write("ENGINE RANKINGS:\n")
                f.write("-" * 20 + "\n")
                for i, (engine_name, report) in enumerate(sorted_engines, 1):
                    f.write(f"{i}. {engine_name}: {report.user_rating}/10\n")
                
                f.write("\nDETAILED RESULTS:\n")
                f.write("-" * 20 + "\n\n")
                
                for engine_name, report in sorted_engines:
                    f.write(f"ENGINE: {engine_name}\n")
                    f.write(f"User Rating: {report.user_rating}/10\n")
                    f.write(f"Character Accuracy: {report.character_accuracy:.1%}\n")
                    f.write(f"Word Accuracy: {report.word_accuracy:.1%}\n")
                    f.write(f"Manual Corrections: {len(report.manual_corrections)}\n")
                    
                    if report.comments:
                        f.write(f"Comments: {report.comments}\n")
                    
                    f.write("\n")
                
                # Add recommendations
                f.write("RECOMMENDATIONS:\n")
                f.write("-" * 20 + "\n")
                
                if sorted_engines:
                    best_engine = sorted_engines[0][0]
                    f.write(f"• Best performing engine: {best_engine}\n")
                    
                    if len(sorted_engines) > 1:
                        worst_engine = sorted_engines[-1][0]
                        f.write(f"• Lowest performing engine: {worst_engine}\n")
                    
                    avg_rating = sum(report.user_rating for _, report in sorted_engines) / len(sorted_engines)
                    f.write(f"• Average rating across all engines: {avg_rating:.1f}/10\n")
                    
                    if avg_rating < 7:
                        f.write("• Consider trying additional preprocessing or different engines\n")
                    
                    f.write("• Review individual comments for specific improvement suggestions\n")
            
            self.process_logger.info(f"Generated evaluation summary: {summary_path}")
            return str(summary_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to generate evaluation summary: {str(e)}")