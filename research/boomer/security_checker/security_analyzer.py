#!/usr/bin/env python3
"""
Security Analyzer for Prompt-Driven Development

This module analyzes code for security vulnerabilities, best practices violations,
and potential risks in database operations, network access, and file operations.
"""

import os
import re
import ast
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SecurityIssue:
    """Represents a security issue found in code"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # SQL_INJECTION, HARDCODED_SECRETS, etc.
    file_path: str
    line_number: int
    description: str
    recommendation: str
    code_snippet: str


class SecurityAnalyzer:
    def __init__(self, project_path: str, main_program: str):
        self.project_path = Path(project_path)
        self.main_program = main_program
        self.issues: List[SecurityIssue] = []
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Security patterns to detect
        self.security_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'cursor\.execute\s*\(\s*f["\']',
                r'\.format\s*\(',
                r'\+.*["\'].*SELECT.*["\']',
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ],
            'dangerous_operations': [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__\s*\(',
            ],
            'file_operations': [
                r'open\s*\([^)]*["\']w["\']',
                r'\.write\s*\(',
                r'os\.remove\s*\(',
                r'shutil\.rmtree\s*\(',
                r'os\.unlink\s*\(',
            ],
            'network_access': [
                r'requests\.',
                r'urllib\.',
                r'socket\.',
                r'http\.',
                r'psycopg2\.connect',
            ]
        }
    
    def analyze_project(self) -> Dict[str, Any]:
        """Main analysis method"""
        print(f"Starting security analysis of {self.project_path}")
        
        # Find all Python files
        python_files = list(self.project_path.rglob("*.py"))
        
        for file_path in python_files:
            self.analyze_file(file_path)
        
        # Generate report
        report = self.generate_report()
        self.save_report(report)
        
        return report
    
    def analyze_file(self, file_path: Path):
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Pattern-based analysis
            self.check_security_patterns(file_path, content, lines)
            
            # AST-based analysis
            try:
                tree = ast.parse(content)
                self.check_ast_security(file_path, tree, lines)
            except SyntaxError:
                self.add_issue(
                    severity="MEDIUM",
                    category="SYNTAX_ERROR",
                    file_path=str(file_path),
                    line_number=0,
                    description="File has syntax errors",
                    recommendation="Fix syntax errors before deployment",
                    code_snippet=""
                )
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    def check_security_patterns(self, file_path: Path, content: str, lines: List[str]):
        """Check for security patterns using regex"""
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    self.add_security_issue(category, file_path, line_num, match.group(), line_content)
    
    def check_ast_security(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for security issues using AST analysis"""
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in ['eval', 'exec', 'compile']:
                        line_content = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                        self.add_issue(
                            severity="CRITICAL",
                            category="DANGEROUS_FUNCTION",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            description=f"Use of dangerous function: {func_name}",
                            recommendation="Avoid using eval/exec. Use safer alternatives",
                            code_snippet=line_content.strip()
                        )
            
            # Check for hardcoded strings that might be secrets
            if isinstance(node, ast.Str) and len(node.s) > 10:
                if any(keyword in node.s.lower() for keyword in ['password', 'secret', 'key', 'token']):
                    line_content = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                    self.add_issue(
                        severity="HIGH",
                        category="POTENTIAL_SECRET",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        description="Potential hardcoded secret detected",
                        recommendation="Use environment variables or secure config files",
                        code_snippet=line_content.strip()
                    )
    
    def add_security_issue(self, category: str, file_path: Path, line_num: int, match: str, line_content: str):
        """Add a security issue based on pattern matching"""
        severity_map = {
            'sql_injection': 'CRITICAL',
            'hardcoded_secrets': 'HIGH',
            'dangerous_operations': 'CRITICAL',
            'file_operations': 'MEDIUM',
            'network_access': 'LOW'
        }
        
        recommendation_map = {
            'sql_injection': 'Use parameterized queries to prevent SQL injection',
            'hardcoded_secrets': 'Store secrets in environment variables or secure vaults',
            'dangerous_operations': 'Avoid system calls. Use safer alternatives',
            'file_operations': 'Validate file paths and use proper error handling',
            'network_access': 'Validate URLs and use HTTPS. Implement proper error handling'
        }
        
        self.add_issue(
            severity=severity_map.get(category, 'MEDIUM'),
            category=category.upper(),
            file_path=str(file_path),
            line_number=line_num,
            description=f"Detected {category.replace('_', ' ')}: {match}",
            recommendation=recommendation_map.get(category, 'Review this code for security implications'),
            code_snippet=line_content.strip()
        )
    
    def add_issue(self, severity: str, category: str, file_path: str, line_number: int, 
                  description: str, recommendation: str, code_snippet: str):
        """Add a security issue to the list"""
        issue = SecurityIssue(
            severity=severity,
            category=category,
            file_path=file_path,
            line_number=line_number,
            description=description,
            recommendation=recommendation,
            code_snippet=code_snippet
        )
        self.issues.append(issue)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate security analysis report"""
        # Group issues by severity
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        category_counts = {}
        
        for issue in self.issues:
            severity_counts[issue.severity] += 1
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        # Calculate risk score
        risk_score = (
            severity_counts['CRITICAL'] * 10 +
            severity_counts['HIGH'] * 5 +
            severity_counts['MEDIUM'] * 2 +
            severity_counts['LOW'] * 1
        )
        
        report = {
            'timestamp': self.report_timestamp,
            'project_path': str(self.project_path),
            'main_program': self.main_program,
            'total_issues': len(self.issues),
            'risk_score': risk_score,
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'issues': [
                {
                    'severity': issue.severity,
                    'category': issue.category,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'description': issue.description,
                    'recommendation': issue.recommendation,
                    'code_snippet': issue.code_snippet
                }
                for issue in sorted(self.issues, key=lambda x: (x.severity, x.file_path, x.line_number))
            ]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """Save the security report"""
        # Create reports directory
        reports_dir = self.project_path / "security_reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        json_file = reports_dir / f"security_report_{self.report_timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save human-readable report
        txt_file = reports_dir / f"security_report_{self.report_timestamp}.txt"
        with open(txt_file, 'w') as f:
            self.write_human_readable_report(f, report)
        
        print(f"Security reports saved:")
        print(f"  JSON: {json_file}")
        print(f"  Text: {txt_file}")
    
    def write_human_readable_report(self, f, report: Dict[str, Any]):
        """Write human-readable security report"""
        f.write("=" * 80 + "\n")
        f.write("SECURITY ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Project: {report['project_path']}\n")
        f.write(f"Main Program: {report['main_program']}\n")
        f.write(f"Analysis Time: {report['timestamp']}\n")
        f.write(f"Total Issues: {report['total_issues']}\n")
        f.write(f"Risk Score: {report['risk_score']}\n\n")
        
        # Risk assessment
        if report['risk_score'] >= 50:
            risk_level = "CRITICAL - Immediate action required"
        elif report['risk_score'] >= 20:
            risk_level = "HIGH - Address before deployment"
        elif report['risk_score'] >= 10:
            risk_level = "MEDIUM - Review and fix when possible"
        else:
            risk_level = "LOW - Monitor and improve over time"
        
        f.write(f"Risk Level: {risk_level}\n\n")
        
        # Severity breakdown
        f.write("SEVERITY BREAKDOWN:\n")
        f.write("-" * 40 + "\n")
        for severity, count in report['severity_breakdown'].items():
            f.write(f"{severity:10}: {count:3} issues\n")
        f.write("\n")
        
        # Category breakdown
        f.write("CATEGORY BREAKDOWN:\n")
        f.write("-" * 40 + "\n")
        for category, count in report['category_breakdown'].items():
            f.write(f"{category:20}: {count:3} issues\n")
        f.write("\n")
        
        # Detailed issues
        f.write("DETAILED ISSUES:\n")
        f.write("=" * 80 + "\n")
        
        current_severity = None
        for issue in report['issues']:
            if issue['severity'] != current_severity:
                current_severity = issue['severity']
                f.write(f"\n{current_severity} SEVERITY ISSUES:\n")
                f.write("-" * 40 + "\n")
            
            f.write(f"\nFile: {issue['file_path']}\n")
            f.write(f"Line: {issue['line_number']}\n")
            f.write(f"Category: {issue['category']}\n")
            f.write(f"Description: {issue['description']}\n")
            f.write(f"Recommendation: {issue['recommendation']}\n")
            if issue['code_snippet']:
                f.write(f"Code: {issue['code_snippet']}\n")
            f.write("-" * 40 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Security Analyzer for Prompt-Driven Development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python security_analyzer.py /path/to/project main.py
  python security_analyzer.py . db_query_runner.py
  python security_analyzer.py ../myproject app.py
        """
    )
    
    parser.add_argument('project_path', help='Path to the project directory')
    parser.add_argument('main_program', help='Name of the main program file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"Error: Project path '{args.project_path}' does not exist")
        return 1
    
    analyzer = SecurityAnalyzer(args.project_path, args.main_program)
    report = analyzer.analyze_project()
    
    # Print summary
    print("\n" + "=" * 60)
    print("SECURITY ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total Issues: {report['total_issues']}")
    print(f"Risk Score: {report['risk_score']}")
    print("\nSeverity Breakdown:")
    for severity, count in report['severity_breakdown'].items():
        if count > 0:
            print(f"  {severity}: {count}")
    
    if report['risk_score'] >= 20:
        print(f"\n⚠️  HIGH RISK PROJECT - Address critical issues before deployment!")
        return 1
    elif report['risk_score'] >= 10:
        print(f"\n⚠️  MEDIUM RISK - Review and address issues")
        return 0
    else:
        print(f"\n✅ LOW RISK - Good security posture")
        return 0


if __name__ == "__main__":
    exit(main())