# Security Checker for Prompt-Driven Development

A comprehensive security analysis tool designed specifically for prompt-driven development workflows. This tool helps identify security vulnerabilities, enforce best practices, and ensure safe development practices when working with AI-generated code.

## 🚀 Quick Start

### Basic Usage
```bash
# Analyze current directory with main.py
python security_analyzer.py . main.py

# Analyze specific project
python security_analyzer.py /path/to/project app.py

# Run comprehensive security check
./run_security_check.sh /path/to/project main.py
```

### Docker Usage (Recommended)
```bash
# Build and run in isolated container
docker-compose up --build

# Run one-time analysis
docker run --rm -v $(pwd):/app security-analyzer
```

## 📋 Features

### 🔍 Security Analysis
- **SQL Injection Detection** - Identifies vulnerable database queries
- **Secret Detection** - Finds hardcoded passwords, API keys, tokens
- **Dangerous Operations** - Detects risky system calls and eval usage
- **File Operations** - Monitors file system access patterns
- **Network Access** - Tracks external network connections

### 📊 Comprehensive Reporting
- **Risk Scoring** - Quantitative security risk assessment
- **Severity Classification** - CRITICAL, HIGH, MEDIUM, LOW
- **Detailed Recommendations** - Specific remediation guidance
- **Multiple Formats** - JSON and human-readable reports

### 🐳 Docker Integration
- **Isolated Development** - Secure containerized environment
- **Production-Ready** - Security-hardened container configuration
- **Easy Deployment** - Docker Compose setup included

## 🛡️ Security Checks

### Critical Issues
- SQL injection vulnerabilities
- Use of `eval()`, `exec()`, `compile()`
- Unsafe system command execution
- Hardcoded secrets in code

### High Priority Issues
- Potential secret leakage
- Unsafe file operations
- Missing input validation
- Insecure network communications

### Medium Priority Issues
- File system operations without validation
- Missing error handling
- Insufficient logging
- Configuration issues

### Low Priority Issues
- Network access patterns
- Code quality concerns
- Documentation gaps
- Performance implications

## 📁 Project Structure

```
security_checker/
├── security_analyzer.py      # Main security analysis engine
├── test_security.py         # Unit tests for security checks
├── run_security_check.sh    # Comprehensive security runner
├── best_practices_guide.md  # Security best practices guide
├── Dockerfile              # Secure container configuration
├── docker-compose.yml      # Multi-service setup
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Installation

### Local Installation
```bash
# Clone or copy the security_checker directory
cd security_checker

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x run_security_check.sh
```

### Docker Installation
```bash
# Build the container
docker build -t security-analyzer .

# Or use docker-compose
docker-compose build
```

## 📖 Usage Examples

### 1. Basic Security Analysis
```bash
python security_analyzer.py ../my_project main.py
```

### 2. Comprehensive Security Check
```bash
./run_security_check.sh ../my_project main.py
```

### 3. Docker Analysis
```bash
# Analyze project in secure container
docker run --rm \
  -v /path/to/project:/app:ro \
  -v /path/to/reports:/app/security_reports:rw \
  security-analyzer
```

### 4. CI/CD Integration
```bash
# In your CI/CD pipeline
./run_security_check.sh . main.py
if [ $? -ne 0 ]; then
  echo "Security issues found - blocking deployment"
  exit 1
fi
```

## 📊 Report Interpretation

### Risk Scores
- **0-9**: LOW - Monitor and improve over time
- **10-19**: MEDIUM - Review and fix when possible
- **20-49**: HIGH - Address before deployment
- **50+**: CRITICAL - Immediate action required

### Severity Levels
- **CRITICAL**: Security vulnerabilities that could lead to system compromise
- **HIGH**: Significant security risks that should be addressed promptly
- **MEDIUM**: Security concerns that should be reviewed and fixed
- **LOW**: Best practice violations and minor security considerations

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest test_security.py -v
```

### Test with Sample Vulnerable Code
```bash
# Create test file with known vulnerabilities
echo 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")' > test_vuln.py

# Run analysis
python security_analyzer.py . test_vuln.py

# Should detect SQL injection
```

## 🐳 Docker Security Features

### Container Hardening
- Non-root user execution
- Read-only file system
- Minimal attack surface
- Resource limitations
- Security options enabled

### Network Isolation
- Custom bridge network
- Minimal port exposure
- Secure inter-container communication

### Volume Security
- Read-only application mounts
- Restricted write access
- Temporary file cleanup

## 🔒 Best Practices Integration

### Development Workflow
1. **Write Code** - Develop with AI assistance
2. **Security Check** - Run security analysis
3. **Fix Issues** - Address identified vulnerabilities
4. **Test** - Verify fixes with unit tests
5. **Deploy** - Deploy only after security clearance

### Continuous Security
- **Pre-commit hooks** - Run security checks before commits
- **CI/CD integration** - Automated security testing
- **Regular audits** - Scheduled comprehensive reviews
- **Dependency monitoring** - Track vulnerable dependencies

## 🚨 Emergency Response

### Critical Issue Response
1. **Immediate isolation** - Stop affected services
2. **Impact assessment** - Determine scope of vulnerability
3. **Rapid remediation** - Apply security fixes
4. **Verification** - Confirm fix effectiveness
5. **Post-incident review** - Learn and improve

### Incident Documentation
- All security incidents logged
- Remediation steps documented
- Lessons learned captured
- Process improvements implemented

## 🤝 Contributing

### Adding New Security Checks
1. Add pattern to `security_patterns` dictionary
2. Implement detection logic in `check_security_patterns()`
3. Add corresponding test case
4. Update documentation

### Improving Analysis
1. Enhance AST-based detection
2. Add new vulnerability categories
3. Improve risk scoring algorithm
4. Expand reporting capabilities

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.org/dev/security/)
- [Docker Security Guide](https://docs.docker.com/engine/security/)
- [Secure Coding Guidelines](https://wiki.sei.cmu.edu/confluence/display/seccode)

## 🆘 Support

For issues, questions, or contributions:
1. Check existing documentation
2. Review test cases for examples
3. Create detailed issue reports
4. Follow security disclosure practices

---

**Remember**: Security is not a one-time check but an ongoing process. Regular analysis, continuous monitoring, and proactive improvement are key to maintaining a secure development environment.