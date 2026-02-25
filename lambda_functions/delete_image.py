import json
import boto3
import os
from botocore.exceptions import ClientError

# Get environment variables with defaults for local development
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'image-storage-bucket')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'image-metadata')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')

# Initialize boto3 clients
s3_config = {'region_name': AWS_REGION}
dynamodb_config = {'region_name': AWS_REGION}

if AWS_ENDPOINT_URL:
    s3_config['endpoint_url'] = AWS_ENDPOINT_URL
    dynamodb_config['endpoint_url'] = AWS_ENDPOINT_URL

s3_client = boto3.client('s3', **s3_config)
dynamodb = boto3.resource('dynamodb', **dynamodb_config)

def lambda_handler(event, context):
    """
    Delete image by image_id
    
    Path parameters:
    - image_id: The ID of the image to delete
    """
    try:
        # Get path parameters
        path_params = event.get('pathParameters') or {}
        image_id = path_params.get('image_id')
        
        if not image_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing required parameter: image_id'
                })
            }
        
        # Get metadata from DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        try:
            response = table.get_item(Key={'image_id': image_id})
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Image not found'
                    })
                }
            
            metadata = response['Item']
            s3_key = metadata.get('s3_key')
            
            # Delete from S3
            if s3_key:
                try:
                    s3_client.delete_object(
                        Bucket=S3_BUCKET_NAME,
                        Key=s3_key
                    )
                except ClientError as e:
                    # Log error but continue with DynamoDB deletion
                    print(f"Error deleting from S3: {str(e)}")
            
            # Delete from DynamoDB
            table.delete_item(Key={'image_id': image_id})
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Image deleted successfully',
                    'image_id': image_id
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

