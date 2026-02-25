import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_functions.delete_image import lambda_handler

@pytest.fixture
def sample_metadata():
    return {
        'image_id': 'img123',
        'user_id': 'user123',
        'title': 'Test Image',
        's3_key': 'user123/img123',
        's3_url': 's3://image-storage-bucket/user123/img123'
    }

@patch('lambda_functions.delete_image.dynamodb')
@patch('lambda_functions.delete_image.s3_client')
def test_delete_image_success(mock_s3, mock_dynamodb, sample_metadata):
    """Test successful image deletion"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': sample_metadata}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'Image deleted successfully'
    assert body['image_id'] == 'img123'
    
    # Verify S3 delete was called
    mock_s3.delete_object.assert_called_once_with(
        Bucket='image-storage-bucket',
        Key='user123/img123'
    )
    
    # Verify DynamoDB delete was called
    mock_table.delete_item.assert_called_once_with(Key={'image_id': 'img123'})

def test_delete_image_missing_image_id():
    """Test delete image with missing image_id"""
    event = {
        'pathParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'image_id' in body['error'].lower()

@patch('lambda_functions.delete_image.dynamodb')
def test_delete_image_not_found(mock_dynamodb):
    """Test delete image when image doesn't exist"""
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'pathParameters': {
            'image_id': 'nonexistent'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'not found' in body['error'].lower()

@patch('lambda_functions.delete_image.dynamodb')
@patch('lambda_functions.delete_image.s3_client')
def test_delete_image_s3_error_continues(mock_s3, mock_dynamodb, sample_metadata):
    """Test that S3 errors don't prevent DynamoDB deletion"""
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': sample_metadata}
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock S3 error
    error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}}
    mock_s3.delete_object.side_effect = ClientError(error_response, 'DeleteObject')
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        }
    }
    
    # Should still succeed and delete from DynamoDB
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    
    # Verify DynamoDB delete was still called
    mock_table.delete_item.assert_called_once()

@patch('lambda_functions.delete_image.dynamodb')
@patch('lambda_functions.delete_image.s3_client')
def test_delete_image_no_s3_key(mock_s3, mock_dynamodb):
    """Test delete image when metadata exists but s3_key is missing"""
    metadata_without_key = {
        'image_id': 'img123',
        'user_id': 'user123'
        # Missing s3_key
    }
    
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': metadata_without_key}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    
    # S3 delete should not be called
    mock_s3.delete_object.assert_not_called()
    
    # DynamoDB delete should still be called
    mock_table.delete_item.assert_called_once()

@patch('lambda_functions.delete_image.dynamodb')
@patch('lambda_functions.delete_image.s3_client')
def test_delete_image_dynamodb_error(mock_s3, mock_dynamodb, sample_metadata):
    """Test handling of DynamoDB errors"""
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    mock_table.get_item.return_value = {'Item': sample_metadata}
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}}
    mock_table.delete_item.side_effect = ClientError(error_response, 'DeleteItem')
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'pathParameters': {
            'image_id': 'img123'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body

