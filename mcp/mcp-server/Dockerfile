FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Set environment variables
ENV GOOGLE_TOKEN_PATH=/app/calendar/token.json
ENV GOOGLE_OAUTH_PATH=/app/calendar/credentials.json

CMD ["python", "mcp/server_calendar.py"]
