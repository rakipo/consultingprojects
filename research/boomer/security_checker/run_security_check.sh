#!/bin/bash

# Security Check Runner Script
# This script runs comprehensive security checks on your project

set -e  # Exit on any error

PROJECT_PATH=${1:-.}
MAIN_PROGRAM=${2:-"main.py"}

echo "🔒 Starting Security Analysis for Prompt-Driven Development"
echo "=================================================="
echo "Project Path: $PROJECT_PATH"
echo "Main Program: $MAIN_PROGRAM"
echo ""

# Create reports directory
mkdir -p "$PROJECT_PATH/security_reports"

# 1. Run custom security analyzer
echo "🔍 Running Custom Security Analyzer..."
python security_analyzer.py "$PROJECT_PATH" "$MAIN_PROGRAM"

# 2. Run Bandit (Python security linter)
echo ""
echo "🔍 Running Bandit Security Scan..."
if command -v bandit &> /dev/null; then
    bandit -r "$PROJECT_PATH" -f json -o "$PROJECT_PATH/security_reports/bandit_report.json" || true
    bandit -r "$PROJECT_PATH" -f txt -o "$PROJECT_PATH/security_reports/bandit_report.txt" || true
    echo "✅ Bandit scan completed"
else
    echo "⚠️  Bandit not installed. Install with: pip install bandit"
fi

# 3. Run Safety (dependency vulnerability check)
echo ""
echo "🔍 Running Safety Dependency Check..."
if command -v safety &> /dev/null; then
    safety check --json --output "$PROJECT_PATH/security_reports/safety_report.json" || true
    safety check --output "$PROJECT_PATH/security_reports/safety_report.txt" || true
    echo "✅ Safety check completed"
else
    echo "⚠️  Safety not installed. Install with: pip install safety"
fi

# 4. Run Semgrep (static analysis)
echo ""
echo "🔍 Running Semgrep Static Analysis..."
if command -v semgrep &> /dev/null; then
    semgrep --config=auto "$PROJECT_PATH" --json --output="$PROJECT_PATH/security_reports/semgrep_report.json" || true
    semgrep --config=auto "$PROJECT_PATH" --output="$PROJECT_PATH/security_reports/semgrep_report.txt" || true
    echo "✅ Semgrep analysis completed"
else
    echo "⚠️  Semgrep not installed. Install with: pip install semgrep"
fi

# 5. Check for secrets in git history (if git repo)
echo ""
echo "🔍 Checking for Secrets in Git History..."
if [ -d "$PROJECT_PATH/.git" ]; then
    echo "Git repository detected. Checking for potential secrets..."
    
    # Check for common secret patterns in git history
    git log --all --full-history --grep="password\|secret\|key\|token" --oneline > "$PROJECT_PATH/security_reports/git_secrets_check.txt" 2>/dev/null || true
    
    # Check current files for secrets
    grep -r -i "password\|secret\|api_key\|token" "$PROJECT_PATH" --exclude-dir=.git --exclude-dir=security_reports > "$PROJECT_PATH/security_reports/current_secrets_check.txt" 2>/dev/null || true
    
    echo "✅ Git secrets check completed"
else
    echo "ℹ️  Not a git repository, skipping git history check"
fi

# 6. Docker security check (if Dockerfile exists)
echo ""
echo "🔍 Docker Security Check..."
if [ -f "$PROJECT_PATH/Dockerfile" ]; then
    echo "Dockerfile found. Checking for security best practices..."
    
    # Basic Dockerfile security checks
    {
        echo "=== Dockerfile Security Analysis ==="
        echo ""
        
        if grep -q "^USER root" "$PROJECT_PATH/Dockerfile"; then
            echo "⚠️  WARNING: Running as root user detected"
        fi
        
        if ! grep -q "^USER " "$PROJECT_PATH/Dockerfile"; then
            echo "⚠️  WARNING: No USER directive found - container may run as root"
        fi
        
        if grep -q "ADD http" "$PROJECT_PATH/Dockerfile"; then
            echo "⚠️  WARNING: Using ADD with URLs - prefer COPY or RUN wget/curl"
        fi
        
        if grep -q ":latest" "$PROJECT_PATH/Dockerfile"; then
            echo "⚠️  WARNING: Using 'latest' tag - prefer specific versions"
        fi
        
        echo "✅ Dockerfile security check completed"
    } > "$PROJECT_PATH/security_reports/dockerfile_security.txt"
else
    echo "ℹ️  No Dockerfile found"
fi

# 7. Generate summary report
echo ""
echo "📊 Generating Security Summary..."
{
    echo "SECURITY ANALYSIS SUMMARY"
    echo "========================="
    echo "Analysis Date: $(date)"
    echo "Project: $PROJECT_PATH"
    echo "Main Program: $MAIN_PROGRAM"
    echo ""
    
    echo "Reports Generated:"
    ls -la "$PROJECT_PATH/security_reports/" | grep -E "\.(json|txt)$" | awk '{print "  - " $9}'
    echo ""
    
    echo "Next Steps:"
    echo "1. Review all generated reports in security_reports/ directory"
    echo "2. Address CRITICAL and HIGH severity issues immediately"
    echo "3. Plan remediation for MEDIUM severity issues"
    echo "4. Monitor LOW severity issues for future improvement"
    echo ""
    
    echo "Security Best Practices:"
    echo "- Use environment variables for secrets"
    echo "- Implement parameterized queries for database operations"
    echo "- Validate all user inputs"
    echo "- Use HTTPS for all network communications"
    echo "- Keep dependencies updated"
    echo "- Run security checks regularly"
    
} > "$PROJECT_PATH/security_reports/security_summary.txt"

echo ""
echo "🎉 Security Analysis Complete!"
echo "📁 Reports saved in: $PROJECT_PATH/security_reports/"
echo ""
echo "Key files to review:"
echo "  - security_summary.txt (overview)"
echo "  - security_report_*.txt (detailed custom analysis)"
echo "  - bandit_report.txt (Python security issues)"
echo "  - safety_report.txt (dependency vulnerabilities)"
echo ""

# Check if any critical issues were found
if [ -f "$PROJECT_PATH/security_reports/security_report_"*".json" ]; then
    CRITICAL_COUNT=$(grep -o '"severity": "CRITICAL"' "$PROJECT_PATH/security_reports/security_report_"*".json" | wc -l)
    if [ "$CRITICAL_COUNT" -gt 0 ]; then
        echo "🚨 CRITICAL ISSUES FOUND: $CRITICAL_COUNT"
        echo "   Please address these issues before deployment!"
        exit 1
    fi
fi

echo "✅ No critical security issues detected"
exit 0