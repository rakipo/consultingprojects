#!/usr/bin/env python3
"""
Unit tests for security analyzer
"""

import pytest
import tempfile
import os
from pathlib import Path
from security_analyzer import SecurityAnalyzer, SecurityIssue


class TestSecurityAnalyzer:
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_project = Path(self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename: str, content: str):
        """Create a test file with given content"""
        file_path = self.test_project / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path
    
    def test_sql_injection_detection(self):
        """Test SQL injection vulnerability detection"""
        vulnerable_code = '''
import psycopg2

def get_user(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    return cursor.fetchone()
        '''
        
        self.create_test_file("vulnerable.py", vulnerable_code)
        analyzer = SecurityAnalyzer(str(self.test_project), "vulnerable.py")
        analyzer.analyze_project()
        
        # Should detect SQL injection
        sql_issues = [issue for issue in analyzer.issues if issue.category == "SQL_INJECTION"]
        assert len(sql_issues) > 0
        assert sql_issues[0].severity == "CRITICAL"
    
    def test_hardcoded_secrets_detection(self):
        """Test hardcoded secrets detection"""
        secret_code = '''
DATABASE_CONFIG = {
    "host": "localhost",
    "password": "secret123",
    "api_key": "sk-1234567890abcdef"
}
        '''
        
        self.create_test_file("secrets.py", secret_code)
        analyzer = SecurityAnalyzer(str(self.test_project), "secrets.py")
        analyzer.analyze_project()
        
        # Should detect hardcoded secrets
        secret_issues = [issue for issue in analyzer.issues if issue.category == "HARDCODED_SECRETS"]
        assert len(secret_issues) > 0
        assert secret_issues[0].severity == "HIGH"
    
    def test_dangerous_operations_detection(self):
        """Test dangerous operations detection"""
        dangerous_code = '''
import os
import subprocess

def run_command(cmd):
    os.system(cmd)
    subprocess.call(cmd, shell=True)
    eval("print('hello')")
        '''
        
        self.create_test_file("dangerous.py", dangerous_code)
        analyzer = SecurityAnalyzer(str(self.test_project), "dangerous.py")
        analyzer.analyze_project()
        
        # Should detect dangerous operations
        dangerous_issues = [issue for issue in analyzer.issues 
                          if issue.category in ["DANGEROUS_OPERATIONS", "DANGEROUS_FUNCTION"]]
        assert len(dangerous_issues) > 0
        assert any(issue.severity == "CRITICAL" for issue in dangerous_issues)
    
    def test_safe_code_no_issues(self):
        """Test that safe code produces no critical issues"""
        safe_code = '''
import os
import psycopg2

def get_user_safe(user_id):
    # Safe parameterized query
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()

def get_config():
    # Safe environment variable usage
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "password": os.getenv("DB_PASSWORD"),
    }
        '''
        
        self.create_test_file("safe.py", safe_code)
        analyzer = SecurityAnalyzer(str(self.test_project), "safe.py")
        analyzer.analyze_project()
        
        # Should have no critical issues
        critical_issues = [issue for issue in analyzer.issues if issue.severity == "CRITICAL"]
        assert len(critical_issues) == 0
    
    def test_report_generation(self):
        """Test security report generation"""
        test_code = '''
import os
password = "hardcoded_secret"
os.system("rm -rf /")
        '''
        
        self.create_test_file("test.py", test_code)
        analyzer = SecurityAnalyzer(str(self.test_project), "test.py")
        report = analyzer.analyze_project()
        
        # Check report structure
        assert "timestamp" in report
        assert "total_issues" in report
        assert "risk_score" in report
        assert "severity_breakdown" in report
        assert "issues" in report
        
        # Should have issues
        assert report["total_issues"] > 0
        assert report["risk_score"] > 0
    
    def test_file_operations_detection(self):
        """Test file operations detection"""
        file_code = '''
import os
import shutil

def cleanup():
    os.remove("temp.txt")
    shutil.rmtree("temp_dir")
    with open("output.txt", "w") as f:
        f.write("data")
        '''
        
        self.create_test_file("fileops.py", file_code)
        analyzer = SecurityAnalyzer(str(self.test_project), "fileops.py")
        analyzer.analyze_project()
        
        # Should detect file operations
        file_issues = [issue for issue in analyzer.issues if issue.category == "FILE_OPERATIONS"]
        assert len(file_issues) > 0
    
    def test_network_access_detection(self):
        """Test network access detection"""
        network_code = '''
import requests
import psycopg2

def fetch_data():
    response = requests.get("https://api.example.com/data")
    return response.json()

def connect_db():
    conn = psycopg2.connect(host="localhost", database="test")
    return conn
        '''
        
        self.create_test_file("network.py", network_code)
        analyzer = SecurityAnalyzer(str(self.test_project), "network.py")
        analyzer.analyze_project()
        
        # Should detect network access
        network_issues = [issue for issue in analyzer.issues if issue.category == "NETWORK_ACCESS"]
        assert len(network_issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])