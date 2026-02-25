import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_functions.list_images import lambda_handler

@pytest.fixture
def sample_images():
    return [
        {
            'image_id': 'img1',
            'user_id': 'user123',
            'title': 'Image 1',
            'tags': ['nature', 'sunset']
        },
        {
            'image_id': 'img2',
            'user_id': 'user123',
            'title': 'Image 2',
            'tags': ['nature', 'forest']
        },
        {
            'image_id': 'img3',
            'user_id': 'user456',
            'title': 'Image 3',
            'tags': ['city', 'urban']
        }
    ]

@patch('lambda_functions.list_images.dynamodb')
def test_list_all_images(mock_dynamodb, sample_images):
    """Test listing all images without filters"""
    mock_table = MagicMock()
    mock_table.scan.return_value = {'Items': sample_images}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 3
    assert len(body['images']) == 3

@patch('lambda_functions.list_images.dynamodb')
def test_list_images_filter_by_user_id(mock_dynamodb, sample_images):
    """Test filtering images by user_id"""
    mock_table = MagicMock()
    user_images = [img for img in sample_images if img['user_id'] == 'user123']
    mock_table.scan.return_value = {'Items': user_images}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': {
            'user_id': 'user123'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 2
    assert all(img['user_id'] == 'user123' for img in body['images'])

@patch('lambda_functions.list_images.dynamodb')
def test_list_images_filter_by_tag(mock_dynamodb, sample_images):
    """Test filtering images by tag"""
    mock_table = MagicMock()
    nature_images = [img for img in sample_images if 'nature' in img.get('tags', [])]
    mock_table.scan.return_value = {'Items': nature_images}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': {
            'tag': 'nature'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 2
    assert all('nature' in img.get('tags', []) for img in body['images'])

@patch('lambda_functions.list_images.dynamodb')
def test_list_images_filter_by_user_and_tag(mock_dynamodb, sample_images):
    """Test filtering images by both user_id and tag"""
    mock_table = MagicMock()
    filtered_images = [
        img for img in sample_images 
        if img['user_id'] == 'user123' and 'nature' in img.get('tags', [])
    ]
    mock_table.scan.return_value = {'Items': filtered_images}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': {
            'user_id': 'user123',
            'tag': 'nature'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 2

@patch('lambda_functions.list_images.dynamodb')
def test_list_images_with_limit(mock_dynamodb, sample_images):
    """Test listing images with limit"""
    mock_table = MagicMock()
    limited_images = sample_images[:2]
    mock_table.scan.return_value = {'Items': limited_images, 'LastEvaluatedKey': {'image_id': 'img2'}}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': {
            'limit': '2'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 2
    assert body['has_more'] == True
    assert 'last_evaluated_key' in body

@patch('lambda_functions.list_images.dynamodb')
def test_list_images_with_pagination(mock_dynamodb, sample_images):
    """Test listing images with pagination"""
    mock_table = MagicMock()
    mock_table.scan.return_value = {'Items': sample_images[1:]}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': {
            'last_evaluated_key': json.dumps({'image_id': 'img1'})
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 2

@patch('lambda_functions.list_images.dynamodb')
def test_list_images_empty_result(mock_dynamodb):
    """Test listing images when no results found"""
    mock_table = MagicMock()
    mock_table.scan.return_value = {'Items': []}
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': {
            'user_id': 'nonexistent'
        }
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 0
    assert body['has_more'] == False

@patch('lambda_functions.list_images.dynamodb')
def test_list_images_dynamodb_error(mock_dynamodb):
    """Test handling of DynamoDB errors"""
    from botocore.exceptions import ClientError
    
    mock_table = MagicMock()
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}}
    mock_table.scan.side_effect = ClientError(error_response, 'Scan')
    mock_dynamodb.Table.return_value = mock_table
    
    event = {
        'queryStringParameters': None
    }
    
    response = lambda_handler(event, None)
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body

