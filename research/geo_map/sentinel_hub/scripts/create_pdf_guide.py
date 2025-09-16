#!/usr/bin/env python3
"""
Create PDF Guide for Batch Analysis Output Interpretation
Converts the markdown guide to a comprehensive PDF document
"""

import markdown
from weasyprint import HTML, CSS
import os
from datetime import datetime

def create_pdf_guide():
    """Create a comprehensive PDF guide for batch analysis interpretation"""
    
    # Read the markdown content
    with open('BATCH_ANALYSIS_OUTPUT_INTERPRETATION_GUIDE.md', 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['tables', 'fenced_code'])
    
    # Create styled HTML
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Batch Analysis Output Interpretation Guide</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                margin: 40px;
                color: #333;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                font-size: 28px;
            }}
            
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 5px;
                margin-top: 30px;
                font-size: 22px;
            }}
            
            h3 {{
                color: #2980b9;
                margin-top: 25px;
                font-size: 18px;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-size: 12px;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
                color: #2c3e50;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            code {{
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }}
            
            pre {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 15px;
                overflow-x: auto;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
            }}
            
            .example {{
                background-color: #e8f4fd;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 15px 0;
            }}
            
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 15px 0;
            }}
            
            .success {{
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin: 15px 0;
            }}
            
            .info {{
                background-color: #d1ecf1;
                border-left: 4px solid #17a2b8;
                padding: 15px;
                margin: 15px 0;
            }}
            
            ul, ol {{
                margin: 15px 0;
                padding-left: 30px;
            }}
            
            li {{
                margin: 5px 0;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏠 Batch Analysis Output Interpretation Guide</h1>
            <p><strong>Sentinel Hub Land Monitoring System</strong></p>
            <p>Comprehensive Guide for Interpreting CSV Analysis Results</p>
            <p><em>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</em></p>
        </div>
        
        {html_content}
        
        <div class="footer">
            <p><strong>Sentinel Hub Batch Property Analyzer</strong></p>
            <p>This guide provides detailed instructions for interpreting land cover change analysis results.</p>
            <p>For technical support or questions, refer to the main README.md file.</p>
        </div>
    </body>
    </html>
    """
    
    # Create PDF
    try:
        # Generate PDF filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"Batch_Analysis_Interpretation_Guide_{timestamp}.pdf"
        
        # Convert HTML to PDF
        HTML(string=styled_html).write_pdf(pdf_filename)
        
        print(f"✅ PDF Guide created successfully: {pdf_filename}")
        print(f"📄 File size: {os.path.getsize(pdf_filename) / 1024:.1f} KB")
        
        return pdf_filename
        
    except Exception as e:
        print(f"❌ Error creating PDF: {str(e)}")
        print("💡 Make sure you have weasyprint installed: pip install weasyprint")
        return None

def create_simple_pdf_guide():
    """Create a simple PDF guide using basic HTML"""
    
    # Create a simplified HTML version
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Batch Analysis Output Interpretation Guide</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; }
            h2 { color: #34495e; margin-top: 30px; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f8f9fa; font-weight: bold; }
            code { background-color: #f4f4f4; padding: 2px 4px; }
            pre { background-color: #f8f9fa; padding: 15px; border: 1px solid #e9ecef; }
        </style>
    </head>
    <body>
        <h1>Batch Analysis Output Interpretation Guide</h1>
        
        <h2>Overview</h2>
        <p>This guide explains how to interpret the comprehensive CSV output generated by the Sentinel Hub Batch Property Analyzer.</p>
        
        <h2>File Naming Convention</h2>
        <p><strong>Example:</strong> 20250810_153259_batch_analysis_before2022-11-01-2023-01-31_after2025-01-01-2025-03-31.csv</p>
        
        <h2>CSV Structure</h2>
        <p>The CSV contains the following column groups:</p>
        <ul>
            <li><strong>Property Identification:</strong> lp_no, extent_ac, POINT_ID, coordinates</li>
            <li><strong>Time Periods:</strong> Before and after period dates</li>
            <li><strong>Vegetation Analysis (NDVI):</strong> Before, after, difference, interpretation, significance</li>
            <li><strong>Built-up Area Analysis (NDBI):</strong> Before, after, difference, interpretation, significance</li>
            <li><strong>Water/Moisture Analysis (NDWI):</strong> Before, after, difference, interpretation, significance</li>
        </ul>
        
        <h2>Understanding the Indices</h2>
        
        <h3>NDVI (Vegetation Index)</h3>
        <ul>
            <li><strong>Range:</strong> 0-255 (higher = more vegetation)</li>
            <li><strong>Interpretations:</strong> "Vegetation growth or improvement", "Vegetation loss or degradation", "No significant vegetation change"</li>
            <li><strong>Significance:</strong> Yes/No (based on threshold)</li>
        </ul>
        
        <h3>NDBI (Built-up Index)</h3>
        <ul>
            <li><strong>Range:</strong> 0-255 (higher = more built-up areas)</li>
            <li><strong>Interpretations:</strong> "Construction or development increase", "Demolition or clearing", "No significant built-up area change"</li>
            <li><strong>Significance:</strong> Yes/No (based on threshold)</li>
        </ul>
        
        <h3>NDWI (Water Index)</h3>
        <ul>
            <li><strong>Range:</strong> 0-255 (higher = more water/moisture)</li>
            <li><strong>Interpretations:</strong> "Water increase or flooding", "Water decrease or drying", "No significant water change"</li>
            <li><strong>Significance:</strong> Yes/No (based on threshold)</li>
        </ul>
        
        <h2>Sample Analysis</h2>
        <p><strong>Property 1:</strong></p>
        <ul>
            <li>NDVI: 102.5 → 118.25 (+15.75) = "Vegetation growth or improvement" (Yes)</li>
            <li>NDBI: 0.0 → 11.5 (+11.5) = "Construction or development increase" (Yes)</li>
            <li>NDWI: 0.0 → 0.0 (0.0) = "No significant water change" (No)</li>
        </ul>
        <p><strong>Summary:</strong> This property shows significant vegetation growth and new construction activity.</p>
        
        <h2>Statistical Significance</h2>
        <ul>
            <li><strong>Threshold:</strong> 0.1 (10% change)</li>
            <li><strong>Yes:</strong> Change above threshold (requires attention)</li>
            <li><strong>No:</strong> Change below threshold (normal variation)</li>
        </ul>
        
        <h2>Common Scenarios</h2>
        <ul>
            <li><strong>Agricultural Development:</strong> Vegetation increase, moderate built-up increase</li>
            <li><strong>Urban Development:</strong> Vegetation decrease, built-up increase</li>
            <li><strong>Natural Disaster:</strong> Vegetation decrease, built-up decrease</li>
            <li><strong>Seasonal Changes:</strong> Moderate vegetation variations, no built-up change</li>
        </ul>
        
        <h2>Actionable Insights</h2>
        <ul>
            <li><strong>Focus on "Yes" significance</strong> - these require attention</li>
            <li><strong>Consider all three indices</strong> for complete picture</li>
            <li><strong>Validate with ground truth</strong> when possible</li>
            <li><strong>Monitor trends</strong> across multiple time periods</li>
        </ul>
        
        <p><em>Generated on: """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """</em></p>
    </body>
    </html>
    """
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"Batch_Analysis_Guide_Simple_{timestamp}.pdf"
        
        HTML(string=html_content).write_pdf(pdf_filename)
        
        print(f"✅ Simple PDF Guide created: {pdf_filename}")
        return pdf_filename
        
    except Exception as e:
        print(f"❌ Error creating PDF: {str(e)}")
        return None

if __name__ == "__main__":
    print("📄 Creating Batch Analysis Output Interpretation Guide PDF...")
    
    # Try to create the comprehensive PDF first
    pdf_file = create_pdf_guide()
    
    if not pdf_file:
        print("🔄 Trying simple PDF version...")
        pdf_file = create_simple_pdf_guide()
    
    if pdf_file:
        print(f"🎉 PDF guide successfully created: {pdf_file}")
        print("📖 You can now open this PDF to view the complete interpretation guide.")
    else:
        print("❌ Could not create PDF. Please check if weasyprint is installed:")
        print("   pip install weasyprint")
