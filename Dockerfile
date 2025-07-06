# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Poppler utilities for PDF processing
RUN apt-get update && apt-get install -y poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin -c "Docker image user" appuser

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create directories for data and temporary files and set permissions
RUN mkdir -p data pdf_images && \
    chown -R appuser:appuser data pdf_images && \
    chmod -R 755 data pdf_images

# Switch to the non-root user
USER appuser

# Expose the port for the health check server
EXPOSE 8001

# Run main.py when the container launches
CMD ["python", "main.py"]