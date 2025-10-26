FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project structure
COPY config/ config/
COPY src/ src/
COPY templates/ templates/
COPY Training-Data/ Training-Data/
COPY web_server.py .
COPY .env.example .env.example

# Create directories for runtime data
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH

# Health check - verify bot can import modules
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '.'); from src import bot; print('OK')" || exit 1

# Expose port for web server
EXPOSE 5000

# Run bot (web server runs in separate container or via docker-compose)
CMD ["python", "src/bot.py"]
