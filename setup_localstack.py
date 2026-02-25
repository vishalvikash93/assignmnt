#!/usr/bin/env python3
"""
Python-based setup script for LocalStack environment.
This script creates the necessary S3 bucket and DynamoDB table using boto3.
Use this if AWS CLI is not installed.
"""

import boto3
import time
import sys
import requests

# LocalStack endpoint
ENDPOINT_URL = 'http://localhost:4566'
S3_BUCKET_NAME = 'image-storage-bucket'
DYNAMODB_TABLE_NAME = 'image-metadata'

def check_localstack_ready():
    """Check if LocalStack is running and ready"""
    try:
        response = requests.get(f'{ENDPOINT_URL}/_localstack/health', timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def setup_s3_bucket(s3_client):
    """Create S3 bucket if it doesn't exist"""
    try:
        s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
        print(f"✓ S3 bucket '{S3_BUCKET_NAME}' created successfully")
        return True
    except s3_client.exceptions.BucketAlreadyExists:
        print(f"⚠ S3 bucket '{S3_BUCKET_NAME}' already exists (this is okay)")
        return True
    except Exception as e:
        print(f"✗ Error creating S3 bucket: {e}")
        return False

def setup_dynamodb_table(dynamodb_client):
    """Create DynamoDB table if it doesn't exist"""
    try:
        dynamodb_client.create_table(
            TableName=DYNAMODB_TABLE_NAME,
            AttributeDefinitions=[
                {
                    'AttributeName': 'image_id',
                    'AttributeType': 'S'
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'image_id',
                    'KeyType': 'HASH'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✓ DynamoDB table '{DYNAMODB_TABLE_NAME}' created successfully")
        return True
    except dynamodb_client.exceptions.ResourceInUseException:
        print(f"⚠ DynamoDB table '{DYNAMODB_TABLE_NAME}' already exists (this is okay)")
        return True
    except Exception as e:
        print(f"✗ Error creating DynamoDB table: {e}")
        return False

def main():
    print("Setting up LocalStack environment...")
    print("")
    
    # Check if LocalStack is running
    print("Checking if LocalStack is ready...")
    if not check_localstack_ready():
        print("ERROR: LocalStack is not running!")
        print("Please start LocalStack first:")
        print("  docker compose up -d")
        print("  OR")
        print("  docker-compose up -d")
        sys.exit(1)
    print("✓ LocalStack is ready")
    print("")
    
    # Wait a bit for services to be fully ready
    print("Waiting for services to be ready...")
    time.sleep(3)
    
    # Initialize boto3 clients
    s3_client = boto3.client(
        's3',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    dynamodb_client = boto3.client(
        'dynamodb',
        endpoint_url=ENDPOINT_URL,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    # Create S3 bucket
    print("Creating S3 bucket...")
    setup_s3_bucket(s3_client)
    
    # Create DynamoDB table
    print("Creating DynamoDB table...")
    setup_dynamodb_table(dynamodb_client)
    
    print("")
    print("LocalStack setup complete!")
    print(f"S3 bucket: {S3_BUCKET_NAME}")
    print(f"DynamoDB table: {DYNAMODB_TABLE_NAME}")

if __name__ == '__main__':
    main()

