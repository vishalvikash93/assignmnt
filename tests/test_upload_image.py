import json
import base64
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_functions.upload_image import lambda_handler

@pytest.fixture
def sample_image_data():
    """Create a sample base64 encoded image"""
    # Create a minimal valid JPEG image (1x1 pixel)
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb'
    return base64.b64encode(jpeg_header + b'\x00' * 100).decode('utf-8')

@pytest.fixture
def valid_event(sample_image_data):
    return {
        'body': json.dumps({
            'user_id': 'user123',
            'image_data': sample_image_data,
            'title': 'Test Image',
            'description': 'Test Description',
            'tags': ['test', 'sample']
        })
    }

@patch('lambda_functions.upload_image.dynamodb')
@patch('lambda_functions.upload_image.s3_client')
def test_upload_image_success(mock_s3, mock_dynamodb, valid_event, sample_image_data):
    """Test successful image upload"""
    # Setup mocks
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Call handler
    response = lambda_handler(valid_event, None)
    
    # Assertions
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['message'] == 'Image uploaded successfully'
    assert 'image_id' in body
    assert 'metadata' in body
    
    # Verify S3 upload was called
    mock_s3.put_object.assert_called_once()
    call_args = mock_s3.put_object.call_args
    assert call_args[1]['Bucket'] == 'image-storage-bucket'
    assert 'user123' in call_args[1]['Key']
    
    # Verify DynamoDB put_item was called
    mock_table.put_item.assert_called_once()

def test_upload_image_missing_user_id(sample_image_data):
    """Test upload with missing user_id"""
    event = {
        'body': json.dumps({
            'image_data': sample_image_data
        })
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'user_id' in body['error'].lower()

def test_upload_image_missing_image_data():
    """Test upload with missing image_data"""
    event = {
        'body': json.dumps({
            'user_id': 'user123'
        })
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body

def test_upload_image_invalid_base64():
    """Test upload with invalid base64 data"""
    event = {
        'body': json.dumps({
            'user_id': 'user123',
            'image_data': 'invalid_base64!!!'
        })
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body

@patch('lambda_functions.upload_image.dynamodb')
@patch('lambda_functions.upload_image.s3_client')
def test_upload_image_s3_error(mock_s3, mock_dynamodb, valid_event):
    """Test handling of S3 errors"""
    from botocore.exceptions import ClientError
    
    # Mock S3 error
    error_response = {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}}
    mock_s3.put_object.side_effect = ClientError(error_response, 'PutObject')
    
    response = lambda_handler(valid_event, None)
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body

@patch('lambda_functions.upload_image.dynamodb')
@patch('lambda_functions.upload_image.s3_client')
def test_upload_image_optional_fields(mock_s3, mock_dynamodb, sample_image_data):
    """Test upload with only required fields"""
    event = {
        'body': json.dumps({
            'user_id': 'user123',
            'image_data': sample_image_data
        })
    }
    
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['metadata']['title'] == ''
    assert body['metadata']['description'] == ''
    assert body['metadata']['tags'] == []

