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
    git \
    curl \
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
COPY setup_web.py .

# Create directories for runtime data
RUN mkdir -p logs

# Initialize git repository and configure it
# First fetch from GitHub, then reset to match remote exactly
RUN git init && \
    git remote add origin https://github.com/Ethan0892/Anti-Ad-Discord-Bot.git && \
    git config --global --add safe.directory /app && \
    git config --global user.email "bot@anti-ad.local" && \
    git config --global user.name "Anti-Ad Bot" && \
    git config pull.ff only && \
    echo "Training-Data/" > .gitignore && \
    echo "*.log" >> .gitignore && \
    echo "data.json" >> .gitignore && \
    echo ".env" >> .gitignore && \
    git add .gitignore && \
    git commit -m "Initial gitignore" && \
    git fetch origin main && \
    git reset --hard origin/main

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
