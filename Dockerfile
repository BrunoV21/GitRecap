# Use the official Python 3.12 image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create the /app/files directory and set full permissions
RUN mkdir -p /app/.files && chmod 777 /app/.files
RUN mkdir -p /app/logs && chmod 777 /app/logs
RUN mkdir -p /app/observability_data && chmod 777 /app/observability_data

# Copy the current repository into the container
COPY app/api /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git-recap==0.1.0 && \
    pip install core-for-ai==0.1.88[all] && \
    pip install -r requirements.txt

EXPOSE 8000

CMD python main.py