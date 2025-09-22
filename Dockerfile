FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Fix path issues for Docker environment
RUN sed -i 's|../itemlist_dates.txt|/app/itemlist_dates.txt|g' backend/backend-api.py

# Expose the port the app runs on
EXPOSE 9080

# Command to run the application
CMD ["python", "backend/backend-api.py"]
