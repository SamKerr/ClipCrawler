# Use Python 3.12 slim image
FROM python:3.12-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your source code
COPY src/ /app/src/

# Run the script
CMD ["python", "src/main.py"]