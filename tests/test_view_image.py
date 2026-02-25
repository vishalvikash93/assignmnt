import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_functions.view_image import lambda_handler

@pytest.fixture
def sample_metadata():
    return {
        'image_id': 'img123',
        'user_id': 'user123',
        'title': 'Test Image',
        'description': 'Test Description',
        'tags': ['test'],
        's3_key': 'user123/img123',
        's3_url': 's3://image-storage-bucket/user123/img123',
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-01T00:00:00'
    }

@patch('lambda_functions.view_image.dynamodb')
@patch('lambda_functions.view_image.s3_client')
def test_view_image_success(mock_s3, mock_dynamodb, sample_metadata):
    """Test successful image view"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': sample_metadata}
    mock_dynamodb.Table.return_value = mock_table
    mock_s3.generate_presigned_url.return_value = 'https://presigned-url.com/image'
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        },
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['image_id'] == 'img123'
    assert 'presigned_url' in body
    assert 'metadata' in body
    assert body['expires_in'] == 3600
    
    # Verify presigned URL generation
    mock_s3.generate_presigned_url.assert_called_once()
    call_args = mock_s3.generate_presigned_url.call_args
    assert call_args[0][0] == 'get_object'
    assert call_args[1]['Params']['Bucket'] == 'image-storage-bucket'
    assert call_args[1]['Params']['Key'] == 'user123/img123'
    assert call_args[1]['ExpiresIn'] == 3600

@patch('lambda_functions.view_image.dynamodb')
@patch('lambda_functions.view_image.s3_client')
def test_view_image_download_mode(mock_s3, mock_dynamodb, sample_metadata):
    """Test image view with download parameter"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': sample_metadata}
    mock_dynamodb.Table.return_value = mock_table
    mock_s3.generate_presigned_url.return_value = 'https://presigned-url.com/image'
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        },
        'queryStringParameters': {
            'download': 'true'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    
    # Verify download parameter was used
    call_args = mock_s3.generate_presigned_url.call_args
    assert 'ResponseContentDisposition' in call_args[1]['Params']
    assert 'attachment' in call_args[1]['Params']['ResponseContentDisposition']

def test_view_image_missing_image_id():
    """Test view image with missing image_id"""
    event = {
        'pathParameters': None,
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'image_id' in body['error'].lower()

@patch('lambda_functions.view_image.dynamodb')
def test_view_image_not_found(mock_dynamodb):
    """Test view image when image doesn't exist"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'pathParameters': {
            'image_id': 'nonexistent'
        },
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'not found' in body['error'].lower()

@patch('lambda_functions.view_image.dynamodb')
def test_view_image_missing_s3_key(mock_dynamodb):
    """Test view image when metadata exists but s3_key is missing"""
    metadata_without_key = {
        'image_id': 'img123',
        'user_id': 'user123',
        'title': 'Test Image'
        # Missing s3_key
    }
    
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': metadata_without_key}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        },
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert 's3 key' in body['error'].lower()

@patch('lambda_functions.view_image.dynamodb')
@patch('lambda_functions.view_image.s3_client')
def test_view_image_s3_error(mock_s3, mock_dynamodb, sample_metadata):
    """Test handling of S3 errors"""
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': sample_metadata}
    mock_dynamodb.Table.return_value = mock_table
    
    # Use a different error code that would result in 500 (not NoSuchKey which returns 404)
    error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
    mock_s3.generate_presigned_url.side_effect = ClientError(error_response, 'GetObject')
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        },
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body

