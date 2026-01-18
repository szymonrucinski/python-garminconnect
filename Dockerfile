FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install the local garminconnect library
COPY garminconnect/ ./garminconnect/
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application
COPY app.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
