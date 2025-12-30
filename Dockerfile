# TradingNode Docker Image (T045)
# Production-ready container for NautilusTrader live trading

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install nautilus_trader nightly
RUN pip install --no-cache-dir \
    nautilus_trader \
    python-dotenv \
    pydantic>=2.0

# Copy configuration package
COPY config/ /app/config/

# Copy strategy files (user provides these)
COPY strategies/ /app/strategies/ 2>/dev/null || true

# Create directories
RUN mkdir -p /var/log/nautilus /data/nautilus/catalog

# Set environment defaults
ENV NAUTILUS_LOG_DIRECTORY=/var/log/nautilus
ENV NAUTILUS_CATALOG_PATH=/data/nautilus/catalog
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import nautilus_trader; print('OK')" || exit 1

# Default command (override with your run script)
CMD ["python", "-c", "print('TradingNode container ready. Override CMD to run your strategy.')"]
