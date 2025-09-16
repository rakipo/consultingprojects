"""OCR engine comparison and reporting framework."""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt

# Optional imports for enhanced visualization
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    sns = None

from ..models.data_models import OCRResult, ComparisonReport, QualityReport
from ..utils.exceptions import OutputGenerationException
from ..utils.logging_config import get_logger_config


class ComparisonReporter:
    """Generates comprehensive comparison reports for OCR engines."""
    
    def __init__(self, output_dir: str = "reports"):
        """Initialize comparison reporter."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger_config = get_logger_config()
        self.process_logger = self.logger_config.get_process_logger()
        self.error_logger = self.logger_config.get_error_logger()
        
        # Set up plotting style
        plt.style.use('default')
        if HAS_SEABORN:
            sns.set_palette("husl")
    
    def generate_performance_dashboard(self, all_results: Dict[str, List[OCRResult]], 
                                     quality_reports: Dict[str, QualityReport] = None,
                                     output_path: str = None) -> str:
        """
        Generate HTML performance dashboard.
        
        Args:
            all_results: Dictionary mapping engine names to OCR results
            quality_reports: Optional quality reports for each engine
            output_path: Optional custom output path
            
        Returns:
            Path to generated HTML dashboard
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.output_dir / f"performance_dashboard_{timestamp}.html"
            
            # Generate comparison data
            comparison_data = self._prepare_comparison_data(all_results, quality_reports)
            
            # Create HTML dashboard
            html_content = self._create_html_dashboard(comparison_data)
            
            # Save HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.process_logger.info(f"Generated performance dashboard: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to generate performance dashboard: {str(e)}")
    
    def create_engine_comparison_table(self, all_results: Dict[str, List[OCRResult]],
                                     quality_reports: Dict[str, QualityReport] = None) -> pd.DataFrame:
        """
        Create detailed engine comparison table.
        
        Args:
            all_results: Dictionary mapping engine names to OCR results
            quality_reports: Optional quality reports for each engine
            
        Returns:
            DataFrame with engine comparison
        """
        try:
            comparison_rows = []
            
            for engine_name, results in all_results.items():
                if not results:
                    continue
                
                # Calculate basic metrics
                avg_confidence = sum(r.confidence_score for r in results) / len(results)
                total_time = sum(r.processing_time for r in results)
                avg_time_per_page = total_time / len(results)
                total_chars = sum(len(r.text) for r in results)
                chars_per_second = total_chars / total_time if total_time > 0 else 0
                
                # Get quality metrics if available
                quality_score = 0.0
                telugu_detection = 0.0
                if quality_reports and engine_name in quality_reports:
                    quality_report = quality_reports[engine_name]
                    quality_score = quality_report.overall_score
                    telugu_detection = quality_report.telugu_detection_rate
                
                # Get cost information
                cost_per_page = 0.0
                if results:
                    # This would need to be implemented in each engine
                    # For now, use placeholder values
                    cost_mapping = {
                        'tesseract': 0.0,
                        'easyocr': 0.0,
                        'paddleocr': 0.0,
                        'trocr': 0.0,
                        'google_vision': 0.0015,
                        'azure_vision': 0.001,
                        'aws_textract': 0.0015,
                        'abbyy': 0.05,
                        'nanonets': 0.02,
                        'mathpix': 0.004
                    }
                    cost_per_page = cost_mapping.get(engine_name, 0.0)
                
                total_cost = cost_per_page * len(results)
                
                comparison_rows.append({
                    'Engine': engine_name,
                    'Pages_Processed': len(results),
                    'Avg_Confidence': f"{avg_confidence:.3f}",
                    'Quality_Score': f"{quality_score:.3f}",
                    'Telugu_Detection': f"{telugu_detection:.3f}",
                    'Total_Time_Seconds': f"{total_time:.2f}",
                    'Avg_Time_Per_Page': f"{avg_time_per_page:.2f}",
                    'Total_Characters': total_chars,
                    'Chars_Per_Second': f"{chars_per_second:.1f}",
                    'Cost_Per_Page': f"${cost_per_page:.4f}",
                    'Total_Cost': f"${total_cost:.4f}",
                    'Telugu_Support': self._get_telugu_support_rating(engine_name),
                    'Free_Tier': 'Yes' if cost_per_page == 0.0 else 'No'
                })
            
            df = pd.DataFrame(comparison_rows)
            
            # Sort by quality score (descending)
            if 'Quality_Score' in df.columns:
                df = df.sort_values('Quality_Score', ascending=False)
            
            return df
            
        except Exception as e:
            self.error_logger.error(f"Failed to create comparison table: {str(e)}")
            return pd.DataFrame()
    
    def generate_performance_charts(self, all_results: Dict[str, List[OCRResult]],
                                  quality_reports: Dict[str, QualityReport] = None) -> List[str]:
        """
        Generate performance visualization charts.
        
        Args:
            all_results: Dictionary mapping engine names to OCR results
            quality_reports: Optional quality reports for each engine
            
        Returns:
            List of paths to generated chart files
        """
        try:
            chart_paths = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Prepare data for charts
            engines = list(all_results.keys())
            confidences = []
            processing_times = []
            quality_scores = []
            telugu_detection_rates = []
            
            for engine_name in engines:
                results = all_results[engine_name]
                if results:
                    avg_confidence = sum(r.confidence_score for r in results) / len(results)
                    avg_time = sum(r.processing_time for r in results) / len(results)
                    confidences.append(avg_confidence)
                    processing_times.append(avg_time)
                    
                    if quality_reports and engine_name in quality_reports:
                        quality_scores.append(quality_reports[engine_name].overall_score)
                        telugu_detection_rates.append(quality_reports[engine_name].telugu_detection_rate)
                    else:
                        quality_scores.append(0.0)
                        telugu_detection_rates.append(0.0)
            
            # Chart 1: Confidence Scores Comparison
            if confidences:
                plt.figure(figsize=(12, 6))
                colors = sns.color_palette("husl", len(engines)) if HAS_SEABORN else None
                bars = plt.bar(engines, confidences, color=colors)
                plt.title('Average Confidence Scores by OCR Engine', fontsize=16, fontweight='bold')
                plt.xlabel('OCR Engine', fontsize=12)
                plt.ylabel('Average Confidence Score', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.ylim(0, 1)
                
                # Add value labels on bars
                for bar, conf in zip(bars, confidences):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                            f'{conf:.3f}', ha='center', va='bottom', fontweight='bold')
                
                plt.tight_layout()
                chart_path = self.output_dir / f"confidence_comparison_{timestamp}.png"
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(str(chart_path))
            
            # Chart 2: Processing Time Comparison
            if processing_times:
                plt.figure(figsize=(12, 6))
                colors = sns.color_palette("viridis", len(engines)) if HAS_SEABORN else None
                bars = plt.bar(engines, processing_times, color=colors)
                plt.title('Average Processing Time by OCR Engine', fontsize=16, fontweight='bold')
                plt.xlabel('OCR Engine', fontsize=12)
                plt.ylabel('Average Time per Page (seconds)', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                
                # Add value labels on bars
                for bar, time_val in zip(bars, processing_times):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(processing_times)*0.01,
                            f'{time_val:.2f}s', ha='center', va='bottom', fontweight='bold')
                
                plt.tight_layout()
                chart_path = self.output_dir / f"processing_time_comparison_{timestamp}.png"
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(str(chart_path))
            
            # Chart 3: Quality vs Speed Scatter Plot
            if quality_scores and processing_times:
                plt.figure(figsize=(10, 8))
                scatter = plt.scatter(processing_times, quality_scores, 
                                    s=100, alpha=0.7, c=range(len(engines)), cmap='tab10')
                
                # Add engine labels
                for i, engine in enumerate(engines):
                    plt.annotate(engine, (processing_times[i], quality_scores[i]),
                               xytext=(5, 5), textcoords='offset points', fontsize=10)
                
                plt.title('Quality vs Processing Speed', fontsize=16, fontweight='bold')
                plt.xlabel('Average Processing Time (seconds)', fontsize=12)
                plt.ylabel('Quality Score', fontsize=12)
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                chart_path = self.output_dir / f"quality_vs_speed_{timestamp}.png"
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(str(chart_path))
            
            # Chart 4: Telugu Detection Rates
            if telugu_detection_rates and any(rate > 0 for rate in telugu_detection_rates):
                plt.figure(figsize=(12, 6))
                colors = sns.color_palette("plasma", len(engines)) if HAS_SEABORN else None
                bars = plt.bar(engines, telugu_detection_rates, color=colors)
                plt.title('Telugu Script Detection Rates by OCR Engine', fontsize=16, fontweight='bold')
                plt.xlabel('OCR Engine', fontsize=12)
                plt.ylabel('Telugu Detection Rate', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.ylim(0, 1)
                
                # Add value labels on bars
                for bar, rate in zip(bars, telugu_detection_rates):
                    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                            f'{rate:.3f}', ha='center', va='bottom', fontweight='bold')
                
                plt.tight_layout()
                chart_path = self.output_dir / f"telugu_detection_rates_{timestamp}.png"
                plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                plt.close()
                chart_paths.append(str(chart_path))
            
            self.process_logger.info(f"Generated {len(chart_paths)} performance charts")
            return chart_paths
            
        except Exception as e:
            self.error_logger.error(f"Failed to generate performance charts: {str(e)}")
            return []
    
    def create_detailed_comparison_report(self, all_results: Dict[str, List[OCRResult]],
                                        quality_reports: Dict[str, QualityReport] = None,
                                        output_path: str = None) -> str:
        """
        Create detailed text-based comparison report.
        
        Args:
            all_results: Dictionary mapping engine names to OCR results
            quality_reports: Optional quality reports for each engine
            output_path: Optional custom output path
            
        Returns:
            Path to generated report file
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.output_dir / f"detailed_comparison_report_{timestamp}.txt"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("TELUGU OCR ENGINE COMPARISON REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Engines Compared: {len(all_results)}\n\n")
                
                # Executive Summary
                f.write("EXECUTIVE SUMMARY\n")
                f.write("-" * 20 + "\n")
                
                # Find best performing engines
                best_confidence = self._find_best_engine_by_metric(all_results, 'confidence')
                best_speed = self._find_fastest_engine(all_results)
                best_quality = self._find_best_engine_by_quality(quality_reports) if quality_reports else None
                
                f.write(f"Best Confidence: {best_confidence[0]} ({best_confidence[1]:.3f})\n")
                f.write(f"Fastest Processing: {best_speed[0]} ({best_speed[1]:.2f}s per page)\n")
                if best_quality:
                    f.write(f"Best Quality: {best_quality[0]} ({best_quality[1]:.3f})\n")
                f.write("\n")
                
                # Detailed Engine Analysis
                f.write("DETAILED ENGINE ANALYSIS\n")
                f.write("-" * 30 + "\n\n")
                
                for engine_name, results in all_results.items():
                    f.write(f"ENGINE: {engine_name.upper()}\n")
                    f.write("=" * (len(engine_name) + 8) + "\n")
                    
                    if not results:
                        f.write("No results available for this engine.\n\n")
                        continue
                    
                    # Basic metrics
                    avg_confidence = sum(r.confidence_score for r in results) / len(results)
                    total_time = sum(r.processing_time for r in results)
                    avg_time = total_time / len(results)
                    total_chars = sum(len(r.text) for r in results)
                    
                    f.write(f"Pages Processed: {len(results)}\n")
                    f.write(f"Average Confidence: {avg_confidence:.3f}\n")
                    f.write(f"Total Processing Time: {total_time:.2f} seconds\n")
                    f.write(f"Average Time per Page: {avg_time:.2f} seconds\n")
                    f.write(f"Total Characters Extracted: {total_chars:,}\n")
                    f.write(f"Characters per Second: {total_chars/total_time:.1f}\n")
                    
                    # Quality metrics if available
                    if quality_reports and engine_name in quality_reports:
                        quality_report = quality_reports[engine_name]
                        f.write(f"Quality Score: {quality_report.overall_score:.3f}\n")
                        f.write(f"Telugu Detection Rate: {quality_report.telugu_detection_rate:.3f}\n")
                        f.write(f"Table Structure Score: {quality_report.table_structure_score:.3f}\n")
                        
                        if quality_report.recommendations:
                            f.write("Recommendations:\n")
                            for rec in quality_report.recommendations[:3]:  # Top 3 recommendations
                                f.write(f"  • {rec}\n")
                    
                    # Telugu support rating
                    telugu_support = self._get_telugu_support_rating(engine_name)
                    f.write(f"Telugu Support Rating: {telugu_support}\n")
                    
                    # Cost analysis
                    cost_info = self._get_cost_analysis(engine_name, len(results))
                    f.write(f"Cost Analysis: {cost_info}\n")
                    
                    f.write("\n")
                
                # Recommendations
                f.write("RECOMMENDATIONS\n")
                f.write("-" * 20 + "\n")
                
                recommendations = self._generate_usage_recommendations(all_results, quality_reports)
                for rec in recommendations:
                    f.write(f"• {rec}\n")
                
                f.write("\n")
                
                # Technical Notes
                f.write("TECHNICAL NOTES\n")
                f.write("-" * 20 + "\n")
                f.write("• Confidence scores are engine-specific and may not be directly comparable\n")
                f.write("• Processing times include image preprocessing and text extraction\n")
                f.write("• Quality scores are based on automated assessment algorithms\n")
                f.write("• Telugu detection rates measure percentage of Telugu script characters\n")
                f.write("• Cost estimates are based on current pricing (subject to change)\n")
            
            self.process_logger.info(f"Generated detailed comparison report: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise OutputGenerationException(f"Failed to create detailed comparison report: {str(e)}")
    
    def _prepare_comparison_data(self, all_results: Dict[str, List[OCRResult]],
                               quality_reports: Dict[str, QualityReport] = None) -> Dict[str, Any]:
        """Prepare data for comparison dashboard."""
        comparison_data = {
            'engines': [],
            'summary_stats': {},
            'performance_metrics': {},
            'quality_metrics': {},
            'cost_analysis': {}
        }
        
        for engine_name, results in all_results.items():
            if not results:
                continue
            
            # Basic metrics
            avg_confidence = sum(r.confidence_score for r in results) / len(results)
            total_time = sum(r.processing_time for r in results)
            avg_time = total_time / len(results)
            total_chars = sum(len(r.text) for r in results)
            
            engine_data = {
                'name': engine_name,
                'pages': len(results),
                'avg_confidence': avg_confidence,
                'total_time': total_time,
                'avg_time_per_page': avg_time,
                'total_characters': total_chars,
                'chars_per_second': total_chars / total_time if total_time > 0 else 0
            }
            
            # Add quality metrics if available
            if quality_reports and engine_name in quality_reports:
                quality_report = quality_reports[engine_name]
                engine_data.update({
                    'quality_score': quality_report.overall_score,
                    'telugu_detection': quality_report.telugu_detection_rate,
                    'table_score': quality_report.table_structure_score
                })
            
            comparison_data['engines'].append(engine_data)
        
        return comparison_data
    
    def _create_html_dashboard(self, comparison_data: Dict[str, Any]) -> str:
        """Create HTML dashboard content."""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telugu OCR Performance Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
        h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .best { background-color: #d5f4e6 !important; font-weight: bold; }
        .good { background-color: #ffeaa7; }
        .poor { background-color: #fab1a0; }
        .footer { text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Telugu OCR Performance Dashboard</h1>
        <p style="text-align: center; color: #7f8c8d;">Generated on {timestamp}</p>
        
        <h2>Engine Comparison Table</h2>
        <table>
            <thead>
                <tr>
                    <th>Engine</th>
                    <th>Pages</th>
                    <th>Avg Confidence</th>
                    <th>Avg Time/Page (s)</th>
                    <th>Total Characters</th>
                    <th>Chars/Second</th>
                    <th>Quality Score</th>
                    <th>Telugu Detection</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <h2>Performance Summary</h2>
        <div class="metrics-grid">
            {summary_cards}
        </div>
        
        <div class="footer">
            <p>Telugu OCR Comparison System | Confidence scores and processing times are engine-specific</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Generate table rows
        table_rows = ""
        for engine in comparison_data['engines']:
            quality_score = engine.get('quality_score', 0.0)
            telugu_detection = engine.get('telugu_detection', 0.0)
            
            # Determine row class based on performance
            row_class = ""
            if quality_score > 0.8:
                row_class = "best"
            elif quality_score > 0.6:
                row_class = "good"
            elif quality_score > 0.0:
                row_class = "poor"
            
            table_rows += f"""
                <tr class="{row_class}">
                    <td>{engine['name']}</td>
                    <td>{engine['pages']}</td>
                    <td>{engine['avg_confidence']:.3f}</td>
                    <td>{engine['avg_time_per_page']:.2f}</td>
                    <td>{engine['total_characters']:,}</td>
                    <td>{engine['chars_per_second']:.1f}</td>
                    <td>{quality_score:.3f}</td>
                    <td>{telugu_detection:.3f}</td>
                </tr>
            """
        
        # Generate summary cards
        if comparison_data['engines']:
            best_confidence = max(comparison_data['engines'], key=lambda x: x['avg_confidence'])
            fastest_engine = min(comparison_data['engines'], key=lambda x: x['avg_time_per_page'])
            most_chars = max(comparison_data['engines'], key=lambda x: x['total_characters'])
            
            summary_cards = f"""
                <div class="metric-card">
                    <div class="metric-value">{best_confidence['name']}</div>
                    <div class="metric-label">Highest Confidence ({best_confidence['avg_confidence']:.3f})</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{fastest_engine['name']}</div>
                    <div class="metric-label">Fastest Processing ({fastest_engine['avg_time_per_page']:.2f}s)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{most_chars['name']}</div>
                    <div class="metric-label">Most Text Extracted ({most_chars['total_characters']:,} chars)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(comparison_data['engines'])}</div>
                    <div class="metric-label">Engines Compared</div>
                </div>
            """
        else:
            summary_cards = "<div class='metric-card'><div class='metric-value'>No Data</div><div class='metric-label'>No engines processed</div></div>"
        
        return html_template.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            table_rows=table_rows,
            summary_cards=summary_cards
        )
    
    def _find_best_engine_by_metric(self, all_results: Dict[str, List[OCRResult]], 
                                   metric: str) -> Tuple[str, float]:
        """Find best engine by specific metric."""
        best_engine = ""
        best_value = 0.0
        
        for engine_name, results in all_results.items():
            if not results:
                continue
            
            if metric == 'confidence':
                value = sum(r.confidence_score for r in results) / len(results)
            elif metric == 'speed':
                value = sum(r.processing_time for r in results) / len(results)
            else:
                continue
            
            if metric == 'confidence' and value > best_value:
                best_engine = engine_name
                best_value = value
            elif metric == 'speed' and (best_value == 0.0 or value < best_value):
                best_engine = engine_name
                best_value = value
        
        return best_engine, best_value
    
    def _find_fastest_engine(self, all_results: Dict[str, List[OCRResult]]) -> Tuple[str, float]:
        """Find fastest engine."""
        return self._find_best_engine_by_metric(all_results, 'speed')
    
    def _find_best_engine_by_quality(self, quality_reports: Dict[str, QualityReport]) -> Tuple[str, float]:
        """Find best engine by quality score."""
        if not quality_reports:
            return "", 0.0
        
        best_engine = max(quality_reports.keys(), key=lambda k: quality_reports[k].overall_score)
        best_score = quality_reports[best_engine].overall_score
        
        return best_engine, best_score
    
    def _get_telugu_support_rating(self, engine_name: str) -> str:
        """Get Telugu support rating for engine."""
        ratings = {
            'tesseract': 'Good',
            'easyocr': 'Excellent',
            'paddleocr': 'Good',
            'trocr': 'Poor',
            'google_vision': 'Excellent',
            'azure_vision': 'Good',
            'aws_textract': 'Poor',
            'abbyy': 'Excellent',
            'nanonets': 'Good (with training)',
            'mathpix': 'Poor'
        }
        return ratings.get(engine_name, 'Unknown')
    
    def _get_cost_analysis(self, engine_name: str, page_count: int) -> str:
        """Get cost analysis for engine."""
        cost_per_page = {
            'tesseract': 0.0,
            'easyocr': 0.0,
            'paddleocr': 0.0,
            'trocr': 0.0,
            'google_vision': 0.0015,
            'azure_vision': 0.001,
            'aws_textract': 0.0015,
            'abbyy': 0.05,
            'nanonets': 0.02,
            'mathpix': 0.004
        }
        
        cost = cost_per_page.get(engine_name, 0.0)
        total_cost = cost * page_count
        
        if cost == 0.0:
            return "Free"
        else:
            return f"${cost:.4f}/page (Total: ${total_cost:.4f})"
    
    def _generate_usage_recommendations(self, all_results: Dict[str, List[OCRResult]],
                                      quality_reports: Dict[str, QualityReport] = None) -> List[str]:
        """Generate usage recommendations based on results."""
        recommendations = []
        
        if not all_results:
            return ["No results available for analysis"]
        
        # Find best performers
        best_confidence = self._find_best_engine_by_metric(all_results, 'confidence')
        fastest = self._find_fastest_engine(all_results)
        
        recommendations.append(f"For highest accuracy: Use {best_confidence[0]} (confidence: {best_confidence[1]:.3f})")
        recommendations.append(f"For fastest processing: Use {fastest[0]} (time: {fastest[1]:.2f}s per page)")
        
        # Free vs paid recommendations
        free_engines = ['tesseract', 'easyocr', 'paddleocr', 'trocr']
        paid_engines = ['google_vision', 'azure_vision', 'aws_textract', 'abbyy', 'nanonets', 'mathpix']
        
        available_free = [e for e in free_engines if e in all_results]
        available_paid = [e for e in paid_engines if e in all_results]
        
        if available_free:
            best_free = max(available_free, key=lambda e: sum(r.confidence_score for r in all_results[e]) / len(all_results[e]))
            recommendations.append(f"Best free option: {best_free}")
        
        if available_paid:
            recommendations.append("Consider paid options for higher accuracy requirements")
        
        # Telugu-specific recommendations
        telugu_engines = ['easyocr', 'google_vision', 'abbyy']
        available_telugu = [e for e in telugu_engines if e in all_results]
        
        if available_telugu:
            recommendations.append(f"For Telugu text: Recommended engines are {', '.join(available_telugu)}")
        
        # General recommendations
        recommendations.append("Test multiple engines and compare results for your specific document types")
        recommendations.append("Consider preprocessing images to improve OCR accuracy")
        
        return recommendations