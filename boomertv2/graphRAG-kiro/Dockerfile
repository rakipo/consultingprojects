# GraphRAG Retrieval Agent Docker Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r graphrag && useradd -r -g graphrag graphrag

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && \
    chown -R graphrag:graphrag /app/logs

# Create config directory if it doesn't exist
RUN mkdir -p /app/config && \
    chown -R graphrag:graphrag /app/config

# Set proper permissions for the application
RUN chown -R graphrag:graphrag /app

# Switch to non-root user
USER graphrag

# Create volume mount point for logs
VOLUME ["/app/logs"]

# Expose port for potential HTTP interface (future use)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from modules.config import load_config; from modules.logging_config import setup_logging; setup_logging(); print('Health check passed')" || exit 1

# Default command - run MCP server
CMD ["python", "mcp_server.py"]

# Alternative commands can be specified:
# For CLI usage: docker run graphrag-agent python main.py status
# For tests: docker run graphrag-agent python tests/test_runner.py