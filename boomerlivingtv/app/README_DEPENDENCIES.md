# Consolidated Dependencies Management

All dependencies for the Boomer Living TV App are now managed through a single `requirements.txt` file at the app folder level.

## 📦 Consolidated Requirements

### Single Source of Truth
- **Location**: `boomerlivingtv/app/requirements.txt`
- **Scope**: All components (MCP servers, data modeling, trending analysis, etc.)
- **Benefits**: No duplicate dependencies, easier maintenance, consistent versions

### Dependency Categories

#### Core Python Libraries
- `pyyaml>=6.0.0` - YAML configuration files
- `typing-extensions>=4.0.0` - Enhanced type hints

#### Database Drivers
- `psycopg2-binary>=2.9.7` - PostgreSQL database driver
- `neo4j>=5.15.0` - Neo4j graph database driver

#### Data Processing
- `pandas>=2.0.0` - Data manipulation and analysis
- `requests>=2.31.0` - HTTP requests

#### MCP Framework
- `mcp>=1.0.0` - Model Context Protocol framework

#### AI/ML Components
- `langgraph>=0.0.40` - Graph-based AI workflows
- `langchain>=0.1.0` - LangChain framework
- `langchain-openai>=0.1.0` - OpenAI integration
- `langchain-anthropic>=0.1.0` - Anthropic integration
- `langchain-core>=0.1.0` - LangChain core components
- `tiktoken>=0.5.0` - Token counting for LLMs

#### Web Framework
- `fastapi>=0.104.0` - Modern web framework
- `uvicorn>=0.24.0` - ASGI server
- `pydantic>=2.5.0` - Data validation

#### Utilities
- `python-dotenv>=1.0.0` - Environment variable management
- `asyncio-mqtt>=0.13.0` - Async MQTT client
- `python-dateutil>=2.8.0` - Date/time utilities
- `pytz>=2023.0` - Timezone handling
- `jsonschema>=4.0.0` - JSON schema validation

#### Development Tools (Optional)
- `pytest>=7.0.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async testing support
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Code linting

## 🚀 Installation

### Quick Installation
```bash
cd boomerlivingtv/app
python install_dependencies.py
```

### Manual Installation
```bash
cd boomerlivingtv/app
pip install -r requirements.txt
```

### Development Installation
```bash
cd boomerlivingtv/app
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8  # Optional dev tools
```

## 🔍 Dependency Management

### Installation Script
The `install_dependencies.py` script provides:
- Python version compatibility check
- Automatic pip upgrade
- Dependency installation
- Import verification
- Installation summary

### Dependency Checker
The `check_dependencies.py` script provides:
- Compatibility checking
- Version mismatch detection
- Conflict identification
- Import health testing

### Usage Examples

#### Check Current Status
```bash
python check_dependencies.py
```

#### Install/Update Dependencies
```bash
python install_dependencies.py
```

#### Verify Specific Module
```python
import psycopg2  # PostgreSQL
import neo4j     # Neo4j
import pandas    # Data processing
import yaml      # Configuration
```

## 📊 Dependency Tree

```
boomerlivingtv/app/
├── requirements.txt (CONSOLIDATED)
├── install_dependencies.py
├── check_dependencies.py
├── mcp-servers/
│   ├── data-modeling/
│   │   └── (no individual requirements.txt)
│   └── cypher/
│       └── (no individual requirements.txt)
└── other components...
```

## 🔧 Version Management

### Version Pinning Strategy
- **Minimum versions** (`>=`) for flexibility
- **Major version compatibility** maintained
- **Security updates** encouraged
- **Breaking changes** avoided

### Updating Dependencies
1. Update `requirements.txt`
2. Run `python install_dependencies.py`
3. Run `python check_dependencies.py`
4. Test all components

### Adding New Dependencies
1. Add to `requirements.txt` with minimum version
2. Update this documentation
3. Test compatibility
4. Update installation scripts if needed

## 🚨 Common Issues

### PostgreSQL Driver Issues
```bash
# If psycopg2-binary fails, try:
pip install psycopg2-binary --no-cache-dir
# Or install system dependencies first (Linux):
sudo apt-get install libpq-dev python3-dev
```

### Neo4j Connection Issues
```bash
# Ensure Neo4j server is running
# Check connection settings in env_config.yaml
```

### LangChain Version Conflicts
```bash
# Ensure all langchain packages are compatible versions
pip install --upgrade langchain langchain-core langchain-openai langchain-anthropic
```

### MCP Framework Issues
```bash
# MCP is relatively new, ensure latest version
pip install --upgrade mcp
```

## 📋 Maintenance Checklist

- [ ] All dependencies in single requirements.txt
- [ ] No duplicate requirements files
- [ ] Version compatibility verified
- [ ] Installation script works
- [ ] Dependency checker passes
- [ ] All imports successful
- [ ] Documentation updated

## 🔄 Migration from Multiple Files

### Before (Multiple Files)
```
boomerlivingtv/
├── trending/requirements.txt
├── app/requirements.txt
├── app/mcp-servers/data-modeling/requirements.txt
└── app/mcp-servers/cypher/requirements.txt
```

### After (Consolidated)
```
boomerlivingtv/
└── app/requirements.txt (ALL DEPENDENCIES)
```

### Benefits of Consolidation
1. **Single source of truth** - No version conflicts
2. **Easier maintenance** - Update once, apply everywhere
3. **Consistent environment** - Same versions across components
4. **Simplified deployment** - One installation command
5. **Better dependency resolution** - pip can optimize better

## 🎯 Best Practices

1. **Always use the consolidated requirements.txt**
2. **Test after adding new dependencies**
3. **Keep versions up to date for security**
4. **Use virtual environments**
5. **Document any special installation requirements**

---

This consolidated approach ensures consistent, maintainable, and conflict-free dependency management across the entire Boomer Living TV App.