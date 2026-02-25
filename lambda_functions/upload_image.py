import json
import boto3
import uuid
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import base64

# Get environment variables with defaults for local development
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'image-storage-bucket')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'image-metadata')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')

# Initialize boto3 clients
s3_config = {}
dynamodb_config = {}

if AWS_ENDPOINT_URL:
    s3_config['endpoint_url'] = AWS_ENDPOINT_URL
    dynamodb_config['endpoint_url'] = AWS_ENDPOINT_URL

s3_config['region_name'] = AWS_REGION
dynamodb_config['region_name'] = AWS_REGION

s3_client = boto3.client('s3', **s3_config)
dynamodb = boto3.resource('dynamodb', **dynamodb_config)

def lambda_handler(event, context):
    """
    Upload image with metadata to S3 and DynamoDB
    
    Expected event body:
    {
        "user_id": "user123",
        "image_data": "base64_encoded_image",
        "title": "My Image",
        "description": "Image description",
        "tags": ["tag1", "tag2"]
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        user_id = body.get('user_id')
        image_data = body.get('image_data')
        title = body.get('title', '')
        description = body.get('description', '')
        tags = body.get('tags', [])
        
        # Validate required fields
        if not user_id or not image_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required fields: user_id and image_data are required'
                })
            }
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Invalid image data: {str(e)}'
                })
            }
        
        # Upload to S3
        s3_key = f"{user_id}/{image_id}"
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=image_bytes,
            ContentType='image/jpeg'
        )
        
        # Get S3 URL
        s3_url = f"s3://{S3_BUCKET_NAME}/{s3_key}"
        
        # Prepare metadata for DynamoDB
        metadata = {
            'image_id': image_id,
            'user_id': user_id,
            'title': title,
            'description': description,
            'tags': tags,
            's3_key': s3_key,
            's3_url': s3_url,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Store metadata in DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        table.put_item(Item=metadata)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Image uploaded successfully',
                'image_id': image_id,
                'metadata': metadata
            })
        }
        
    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'AWS service error: {str(e)}'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }

