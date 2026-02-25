#!/bin/bash

# Setup script for LocalStack environment
# This script creates the necessary S3 bucket and DynamoDB table

echo "Setting up LocalStack environment..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed."
    echo ""
    echo "Please install AWS CLI using one of these methods:"
    echo "  1. Using Homebrew: brew install awscli"
    echo "  2. Using pip: pip install awscli"
    echo "  3. Download from: https://aws.amazon.com/cli/"
    echo ""
    echo "Alternatively, you can use the Python setup script:"
    echo "  python setup_localstack.py"
    echo ""
    exit 1
fi

# Set LocalStack endpoint
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 5

# Check if LocalStack is running
if ! curl -s http://localhost:4566/_localstack/health > /dev/null 2>&1; then
    echo "ERROR: LocalStack is not running!"
    echo "Please start LocalStack first:"
    echo "  docker compose up -d"
    echo "  OR"
    echo "  docker-compose up -d"
    exit 1
fi

# Create S3 bucket
echo "Creating S3 bucket..."
if aws --endpoint-url=$AWS_ENDPOINT_URL s3 mb s3://image-storage-bucket 2>/dev/null; then
    echo "✓ S3 bucket created successfully"
else
    echo "⚠ S3 bucket may already exist (this is okay)"
fi

# Create DynamoDB table
echo "Creating DynamoDB table..."
if aws --endpoint-url=$AWS_ENDPOINT_URL dynamodb create-table \
    --table-name image-metadata \
    --attribute-definitions \
        AttributeName=image_id,AttributeType=S \
    --key-schema \
        AttributeName=image_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST 2>/dev/null; then
    echo "✓ DynamoDB table created successfully"
else
    echo "⚠ DynamoDB table may already exist (this is okay)"
fi

echo ""
echo "LocalStack setup complete!"
echo "S3 bucket: image-storage-bucket"
echo "DynamoDB table: image-metadata"

