#!/usr/bin/env python3
"""
Example script demonstrating how to use the Image Storage Service APIs.
This script shows how to interact with the Lambda functions directly.
"""

import json
import base64
import os
from pathlib import Path

# Example event structures for testing Lambda functions

def create_upload_event(image_path, user_id="user123", title="Test Image", description="", tags=None):
    """Create an upload event with image data"""
    if tags is None:
        tags = ["test", "example"]
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    return {
        'body': json.dumps({
            'user_id': user_id,
            'image_data': image_data,
            'title': title,
            'description': description,
            'tags': tags
        })
    }

def create_list_event(user_id=None, tag=None, limit=100):
    """Create a list event with optional filters"""
    params = {}
    if user_id:
        params['user_id'] = user_id
    if tag:
        params['tag'] = tag
    if limit:
        params['limit'] = str(limit)
    
    return {
        'queryStringParameters': params if params else None
    }

def create_view_event(image_id, download=False):
    """Create a view event"""
    params = {'download': 'true'} if download else None
    return {
        'pathParameters': {
            'image_id': image_id
        },
        'queryStringParameters': params
    }

def create_delete_event(image_id):
    """Create a delete event"""
    return {
        'pathParameters': {
            'image_id': image_id
        }
    }

# Example usage
if __name__ == "__main__":
    print("Example event structures for Lambda functions:")
    print("\n1. Upload Event:")
    print(json.dumps(create_upload_event("example.jpg", "user123", "My Image"), indent=2))
    
    print("\n2. List Event (all images):")
    print(json.dumps(create_list_event(), indent=2))
    
    print("\n3. List Event (filtered by user):")
    print(json.dumps(create_list_event(user_id="user123"), indent=2))
    
    print("\n4. View Event:")
    print(json.dumps(create_view_event("img123"), indent=2))
    
    print("\n5. Delete Event:")
    print(json.dumps(create_delete_event("img123"), indent=2))

