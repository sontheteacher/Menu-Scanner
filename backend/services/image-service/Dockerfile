FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Generate gRPC code from proto files
RUN python -m grpc_tools.protoc \
    -I../../proto \
    --python_out=./proto_gen \
    --grpc_python_out=./proto_gen \
    ../../proto/*.proto

# Expose gRPC port
EXPOSE 50052

# Start the service
CMD ["python", "src/server.py"]
