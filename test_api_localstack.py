#!/usr/bin/env python3
"""
Script to test the Image Storage Service APIs with LocalStack.
This script demonstrates how to use all the API endpoints.

Prerequisites:
1. LocalStack must be running (docker-compose up -d)
2. LocalStack resources must be set up (./setup_localstack.sh)
3. Environment variables must be set for LocalStack
"""

import json
import base64
import os
import sys
import requests
from io import BytesIO
from PIL import Image

# Set up environment for LocalStack
os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['S3_BUCKET_NAME'] = 'image-storage-bucket'
os.environ['DYNAMODB_TABLE_NAME'] = 'image-metadata'

# Import Lambda functions
sys.path.insert(0, os.path.dirname(__file__))
from lambda_functions.upload_image import lambda_handler as upload_handler
from lambda_functions.list_images import lambda_handler as list_handler
from lambda_functions.view_image import lambda_handler as view_handler
from lambda_functions.delete_image import lambda_handler as delete_handler


def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def test_upload_image():
    """Test uploading an image"""
    print("\n=== Testing Upload Image ===")
    
    image_data = create_test_image()
    event = {
        'body': json.dumps({
            'user_id': 'test_user_123',
            'image_data': image_data,
            'title': 'Test Image',
            'description': 'This is a test image uploaded via API',
            'tags': ['test', 'red', 'sample']
        })
    }
    
    response = upload_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response['body'])
    print(f"Response: {json.dumps(body, indent=2)}")
    
    if response['statusCode'] == 201:
        return body.get('image_id')
    return None


def test_list_images(user_id=None, tag=None):
    """Test listing images"""
    print("\n=== Testing List Images ===")
    
    query_params = {}
    if user_id:
        query_params['user_id'] = user_id
    if tag:
        query_params['tag'] = tag
    
    event = {
        'queryStringParameters': query_params if query_params else None
    }
    
    response = list_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response['body'])
    print(f"Response: {json.dumps(body, indent=2)}")
    
    return body.get('images', [])


def test_view_image(image_id, download=False):
    """Test viewing an image"""
    print("\n=== Testing View Image ===")
    
    query_params = {'download': 'true'} if download else None
    event = {
        'pathParameters': {
            'image_id': image_id
        },
        'queryStringParameters': query_params
    }
    
    response = view_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response['body'])
    print(f"Response: {json.dumps(body, indent=2)}")
    
    if response['statusCode'] == 200:
        print(f"\nPresigned URL: {body.get('presigned_url')}")
        print(f"URL expires in: {body.get('expires_in')} seconds")


def test_delete_image(image_id):
    """Test deleting an image"""
    print("\n=== Testing Delete Image ===")
    
    event = {
        'pathParameters': {
            'image_id': image_id
        }
    }
    
    response = delete_handler(event, None)
    print(f"Status Code: {response['statusCode']}")
    body = json.loads(response['body'])
    print(f"Response: {json.dumps(body, indent=2)}")


def main():
    """Run all API tests"""
    print("=" * 50)
    print("Image Storage Service API Test Suite")
    print("=" * 50)
    
    # Test 1: Upload an image
    image_id = test_upload_image()
    if not image_id:
        print("Failed to upload image. Exiting.")
        return
    
    # Test 2: List all images
    test_list_images()
    
    # Test 3: List images filtered by user
    test_list_images(user_id='test_user_123')
    
    # Test 4: List images filtered by tag
    test_list_images(tag='test')
    
    # Test 5: View image
    test_view_image(image_id)
    
    # Test 6: View image with download
    test_view_image(image_id, download=True)
    
    # Test 7: Delete image
    test_delete_image(image_id)
    
    # Test 8: Verify deletion (should return 404)
    print("\n=== Verifying Deletion ===")
    test_view_image(image_id)  # Should return 404
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == '__main__':
    main()


