FROM ghcr.io/raghurammutya/base-image:latest

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY user_service/docker/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY user_service/app /app/app

# Set Python path
ENV PYTHONPATH=/app

# Copy and set up entrypoint
COPY user_service/docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
