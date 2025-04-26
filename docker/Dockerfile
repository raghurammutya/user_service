# 1️⃣ Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 2️⃣ Production stage
FROM python:3.10-slim

WORKDIR /app

# Copy only installed packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy app source code
COPY . .

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
