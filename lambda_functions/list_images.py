import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Get environment variables with defaults for local development
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'image-metadata')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL')

# Initialize boto3 resource
dynamodb_config = {}
if AWS_ENDPOINT_URL:
    dynamodb_config['endpoint_url'] = AWS_ENDPOINT_URL
dynamodb_config['region_name'] = AWS_REGION

dynamodb = boto3.resource('dynamodb', **dynamodb_config)

def lambda_handler(event, context):
    """
    List all images with optional filters
    
    Query parameters:
    - user_id: Filter by user ID
    - tag: Filter by tag
    - limit: Maximum number of results (default: 100)
    - last_evaluated_key: For pagination
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        
        user_id = query_params.get('user_id')
        tag = query_params.get('tag')
        limit = int(query_params.get('limit', 100))
        last_evaluated_key = query_params.get('last_evaluated_key')
        
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        
        # Build filter expression
        filter_expression = None
        key_condition_expression = None
        
        # If filtering by user_id, use it as partition key
        if user_id:
            # Scan with filter if we need to filter by tag as well
            if tag:
                filter_expression = Attr('tags').contains(tag)
                response = table.scan(
                    FilterExpression=Attr('user_id').eq(user_id) & filter_expression,
                    Limit=limit
                )
            else:
                # Use scan for user_id filter (assuming user_id is not the partition key)
                response = table.scan(
                    FilterExpression=Attr('user_id').eq(user_id),
                    Limit=limit
                )
        elif tag:
            # Filter by tag only
            filter_expression = Attr('tags').contains(tag)
            response = table.scan(
                FilterExpression=filter_expression,
                Limit=limit
            )
        else:
            # No filters - scan all items
            scan_kwargs = {'Limit': limit}
            if last_evaluated_key:
                scan_kwargs['ExclusiveStartKey'] = json.loads(last_evaluated_key)
            response = table.scan(**scan_kwargs)
        
        images = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        # Format response
        result = {
            'images': images,
            'count': len(images)
        }
        
        if last_evaluated_key:
            result['last_evaluated_key'] = json.dumps(last_evaluated_key)
            result['has_more'] = True
        else:
            result['has_more'] = False
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
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

