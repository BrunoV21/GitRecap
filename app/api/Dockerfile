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
RUN mkdir -p /app/.files && chmod 777 /app/.files && \
    mkdir -p /app/logs && chmod 777 /app/logs && \
    mkdir -p /app/observability_data && chmod 777 /app/observability_data && \
    mkdir -p /app/devops_cache && chmod 777 /app/devops_cache

# Copy the current repository into the container
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install git-recap==0.1.4 && \
    pip install git+https://github.com/BrunoV21/AiCore.git#egg=core-for-ai[all]

EXPOSE 7860

CMD python main.py
