import json
import boto3
import os
from botocore.exceptions import ClientError
from botocore.config import Config

# Get environment variables with defaults for local development
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'image-storage-bucket')
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'image-metadata')
PRESIGNED_URL_EXPIRATION = int(os.environ.get('PRESIGNED_URL_EXPIRATION', '3600'))
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')

# Initialize boto3 clients
s3_config = {'config': Config(signature_version='s3v4'), 'region_name': AWS_REGION}
dynamodb_config = {'region_name': AWS_REGION}

if AWS_ENDPOINT_URL:
    s3_config['endpoint_url'] = AWS_ENDPOINT_URL
    dynamodb_config['endpoint_url'] = AWS_ENDPOINT_URL

s3_client = boto3.client('s3', **s3_config)
dynamodb = boto3.resource('dynamodb', **dynamodb_config)

def lambda_handler(event, context):
    """
    View/download image by image_id
    
    Path parameters:
    - image_id: The ID of the image to view/download
    
    Query parameters:
    - download: If true, returns presigned URL for download (default: false)
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
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        is_download = query_params.get('download', 'false').lower() == 'true'
        
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
            
            if not s3_key:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'S3 key not found in metadata'
                    })
                }
            
            # Generate presigned URL
            try:
                params = {
                    'Bucket': S3_BUCKET_NAME,
                    'Key': s3_key
                }
                
                if is_download:
                    params['ResponseContentDisposition'] = f'attachment; filename="{metadata.get("title", image_id)}.jpg"'
                
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params=params,
                    ExpiresIn=PRESIGNED_URL_EXPIRATION
                )
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    return {
                        'statusCode': 404,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': 'Image not found in storage'
                        })
                    }
                # For other S3 errors, return 500
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
            
            result = {
                'image_id': image_id,
                'metadata': metadata,
                'presigned_url': presigned_url,
                'expires_in': PRESIGNED_URL_EXPIRATION
            }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Image not found in storage'
                    })
                }
            raise
        
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

