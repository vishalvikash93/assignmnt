# Image Storage Service

A scalable image upload and storage service built with AWS Lambda, API Gateway, S3, and DynamoDB. This service supports image uploads with metadata, listing with filters, viewing/downloading, and deletion.

## Architecture

- **API Gateway**: RESTful API endpoints
- **Lambda Functions**: Serverless compute for business logic
- **S3**: Image storage
- **DynamoDB**: Metadata storage (NoSQL)
- **LocalStack**: Local AWS services for development

## Project Structure

```
.
├── lambda_functions/          # Lambda function handlers
│   ├── upload_image.py        # Upload image with metadata
│   ├── list_images.py         # List images with filters
│   ├── view_image.py          # View/download image
│   └── delete_image.py        # Delete image
├── tests/                      # Unit tests
│   ├── test_upload_image.py
│   ├── test_list_images.py
│   ├── test_view_image.py
│   └── test_delete_image.py
├── docker-compose.yml          # LocalStack configuration
├── setup_localstack.sh         # Setup script for LocalStack
├── serverless.yml              # Serverless Framework configuration
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
└── README.md                   # This file
```

## Prerequisites

- Python 3.7+
- Docker and Docker Compose
- AWS CLI (for LocalStack setup)
- pip

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start LocalStack

```bash
docker-compose up -d
```

Wait for LocalStack to be ready (about 10-15 seconds).

### 3. Setup LocalStack Resources

```bash
chmod +x setup_localstack.sh
./setup_localstack.sh
```

This creates:
- S3 bucket: `image-storage-bucket`
- DynamoDB table: `image-metadata`

## API Endpoints

### 1. Upload Image

Upload an image with metadata to S3 and store metadata in DynamoDB.

**Endpoint:** `POST /images`

**Request Body:**
```json
{
  "user_id": "user123",
  "image_data": "base64_encoded_image_string",
  "title": "My Beautiful Image",
  "description": "A description of the image",
  "tags": ["nature", "sunset", "photography"]
}
```

**Required Fields:**
- `user_id`: User identifier
- `image_data`: Base64-encoded image data

**Optional Fields:**
- `title`: Image title
- `description`: Image description
- `tags`: Array of tags

**Response (201 Created):**
```json
{
  "message": "Image uploaded successfully",
  "image_id": "uuid-generated-id",
  "metadata": {
    "image_id": "uuid-generated-id",
    "user_id": "user123",
    "title": "My Beautiful Image",
    "description": "A description of the image",
    "tags": ["nature", "sunset", "photography"],
    "s3_key": "user123/uuid-generated-id",
    "s3_url": "s3://image-storage-bucket/user123/uuid-generated-id",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

### 2. List Images

List all images with optional filters.

**Endpoint:** `GET /images`

**Query Parameters:**
- `user_id` (optional): Filter by user ID
- `tag` (optional): Filter by tag
- `limit` (optional): Maximum number of results (default: 100)
- `last_evaluated_key` (optional): For pagination

**Examples:**
- List all images: `GET /images`
- Filter by user: `GET /images?user_id=user123`
- Filter by tag: `GET /images?tag=nature`
- Combined filters: `GET /images?user_id=user123&tag=sunset`
- With pagination: `GET /images?limit=10&last_evaluated_key=...`

**Response (200 OK):**
```json
{
  "images": [
    {
      "image_id": "img1",
      "user_id": "user123",
      "title": "Image 1",
      "description": "Description",
      "tags": ["nature", "sunset"],
      "s3_key": "user123/img1",
      "s3_url": "s3://image-storage-bucket/user123/img1",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "count": 1,
  "has_more": false
}
```

### 3. View/Download Image

Get a presigned URL to view or download an image.

**Endpoint:** `GET /images/{image_id}`

**Query Parameters:**
- `download` (optional): Set to `true` for download (default: `false`)

**Examples:**
- View image: `GET /images/img123`
- Download image: `GET /images/img123?download=true`

**Response (200 OK):**
```json
{
  "image_id": "img123",
  "metadata": {
    "image_id": "img123",
    "user_id": "user123",
    "title": "My Image",
    "description": "Description",
    "tags": ["nature"],
    "s3_key": "user123/img123",
    "s3_url": "s3://image-storage-bucket/user123/img123",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  },
  "presigned_url": "https://presigned-url.com/image?signature=...",
  "expires_in": 3600
}
```

### 4. Delete Image

Delete an image from both S3 and DynamoDB.

**Endpoint:** `DELETE /images/{image_id}`

**Response (200 OK):**
```json
{
  "message": "Image deleted successfully",
  "image_id": "img123"
}
```

## Testing

### Unit Tests

Run all unit tests:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_upload_image.py
```

Run a specific test:

```bash
pytest tests/test_upload_image.py::test_upload_image_success
```

### Integration Testing with LocalStack

To test the APIs with LocalStack:

1. Start LocalStack:
```bash
docker-compose up -d
```

2. Set up LocalStack resources:
```bash
./setup_localstack.sh
```

3. Run the integration test script:
```bash
python test_api_localstack.py
```

This script will test all API endpoints:
- Upload image
- List images (with filters)
- View image
- Delete image

## LocalStack Configuration

The service uses LocalStack for local development. LocalStack provides local implementations of AWS services.

### Environment Variables

When running Lambda functions locally with LocalStack, set these environment variables:

```bash
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET_NAME=image-storage-bucket
export DYNAMODB_TABLE_NAME=image-metadata
```

The Lambda functions will automatically use these environment variables if set, otherwise they will use defaults suitable for LocalStack development.

### LocalStack Services

- **S3**: `http://localhost:4566`
- **DynamoDB**: `http://localhost:4566`
- **Lambda**: `http://localhost:4566`
- **API Gateway**: `http://localhost:4566`

## DynamoDB Schema

**Table:** `image-metadata`

**Primary Key:**
- `image_id` (String) - Partition key

**Attributes:**
- `user_id` (String)
- `title` (String)
- `description` (String)
- `tags` (List of Strings)
- `s3_key` (String)
- `s3_url` (String)
- `created_at` (String - ISO 8601)
- `updated_at` (String - ISO 8601)

## S3 Structure

Images are stored in S3 with the following structure:
```
s3://image-storage-bucket/
  └── {user_id}/
      └── {image_id}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses follow this format:
```json
{
  "error": "Error message description"
}
```

## Scalability Considerations

1. **DynamoDB**: Uses on-demand billing mode for automatic scaling
2. **S3**: Automatically scales to handle any amount of data
3. **Lambda**: Automatically scales based on request volume
4. **API Gateway**: Handles high throughput automatically

For production, consider:
- Adding caching (CloudFront for S3, ElastiCache for metadata)
- Implementing rate limiting
- Adding authentication/authorization
- Using DynamoDB Global Secondary Indexes (GSI) for efficient queries by `user_id` or `tags`
- Implementing image resizing/optimization
- Adding CloudWatch monitoring and alarms

## Production Deployment

### Option 1: Using Serverless Framework

The project includes a `serverless.yml` configuration file for easy deployment.

1. Install Serverless Framework:
```bash
npm install -g serverless
```

2. Configure AWS credentials:
```bash
aws configure
```

3. Deploy to AWS:
```bash
serverless deploy
```

This will automatically:
- Create the S3 bucket
- Create the DynamoDB table
- Deploy all Lambda functions
- Create API Gateway endpoints
- Set up IAM roles with proper permissions

4. Get the API endpoint:
```bash
serverless info
```

### Option 2: Manual Deployment

For manual deployment to AWS:

1. Package Lambda functions:
```bash
zip -r lambda_function.zip lambda_functions/
```

2. Create Lambda functions in AWS Console or using AWS CLI

3. Set environment variables:
   - `S3_BUCKET_NAME`: Your S3 bucket name
   - `DYNAMODB_TABLE_NAME`: Your DynamoDB table name
   - `PRESIGNED_URL_EXPIRATION`: URL expiration time in seconds (default: 3600)

4. Create API Gateway REST API and connect to Lambda functions

5. Set up IAM roles with appropriate permissions:
   - S3: PutObject, GetObject, DeleteObject
   - DynamoDB: PutItem, GetItem, Scan, DeleteItem

## License

This project is provided as-is for educational purposes.

