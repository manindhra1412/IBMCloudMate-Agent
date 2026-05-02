import ibm_boto3
from ibm_botocore.client import Config, ClientError
import os
from datetime import datetime
from langchain.tools import Tool
from pathlib import Path

def get_cos_client():
    """Initialize and return a COS client"""
    cos_client = ibm_boto3.client(
        "s3",
        ibm_api_key_id=os.getenv("COS_API_KEY"),
        ibm_service_instance_id=os.getenv("COS_SERVICE_INSTANCE_ID"),
        config=Config(signature_version="oauth"),
        endpoint_url=os.getenv("COS_ENDPOINT_URL"),
        ibm_auth_endpoint=os.getenv("COS_IAM_ENDPOINT", "https://iam.test.cloud.ibm.com/identity/token")
    )
    print(f"Connected to COS Service ✅")
    return cos_client

def cos_list_buckets(query: str = "") -> str:
    """List all buckets in the account"""
    try:
        client = get_cos_client()
        buckets = client.list_buckets()
        if not buckets.get("Buckets"):
            return "No buckets found in the account"
        
        bucket_list = [bucket["Name"] for bucket in buckets["Buckets"]]
        return f"Available buckets:\n{', '.join(bucket_list)}"
    except ClientError as be:
        return f"Error listing buckets: {str(be)}"
    except Exception as e:
        return f"Error: {str(e)}"

def cos_create_bucket(query: str) -> str:
    """Create a new bucket"""
    try:
        bucket_name = query.strip()
        if not bucket_name:
            return "Error: Bucket name not provided"
            
        client = get_cos_client()
        try:
            client.create_bucket(Bucket=bucket_name)
            return f'Successfully created bucket "{bucket_name}"'
        except ClientError as be:
            if be.response['Error']['Code'] == 'BucketAlreadyExists':
                return f'Bucket "{bucket_name}" already exists'
            return f"Error creating bucket: {str(be)}"
    except Exception as e:
        return f"Error: {str(e)}"

def cos_list_objects(query: str) -> str:
    """List all objects in a bucket"""
    try:
        bucket_name = query.strip()
        if not bucket_name:
            return "Error: Bucket name not provided"
            
        client = get_cos_client()
        try:
            response = client.list_objects_v2(Bucket=bucket_name)
            if not response.get('Contents'):
                return f'No objects found in bucket "{bucket_name}"'
            
            objects = [f"{obj['Key']} (Size: {obj['Size']} bytes)" for obj in response['Contents']]
            return f'Objects in bucket "{bucket_name}":\n' + '\n'.join(objects)
        except ClientError as be:
            if be.response['Error']['Code'] == 'NoSuchBucket':
                return f'Bucket "{bucket_name}" does not exist'
            return f"Error listing objects: {str(be)}"
    except Exception as e:
        return f"Error: {str(e)}"

def cos_upload_from_uploads(query: str) -> str:
    """Upload a file from the uploads directory to a bucket"""
    try:
        parts = query.strip().split(' ', 1)
        if len(parts) != 2:
            return "Error: Please provide bucket name and file name"
            
        bucket_name, file_name = parts
        uploads_dir = Path("uploads")
        file_path = uploads_dir / file_name
        
        if not file_path.exists():
            return f"Error: File '{file_name}' not found in uploads directory"
            
        client = get_cos_client()
        try:
            client.upload_file(str(file_path), bucket_name, file_name)
            return f'Successfully uploaded "{file_name}" to bucket "{bucket_name}"'
        except ClientError as be:
            if be.response['Error']['Code'] == 'NoSuchBucket':
                return f'Bucket "{bucket_name}" does not exist'
            return f"Error uploading file: {str(be)}"
    except Exception as e:
        return f"Error: {str(e)}"

def cos_download_file(query: str) -> str:
    """Download a file from a bucket"""
    try:
        parts = query.strip().split(' ', 1)
        if len(parts) != 2:
            return "Error: Please provide bucket name and object name"
            
        bucket_name, object_name = parts
        client = get_cos_client()
        try:
            client.download_file(bucket_name, object_name, object_name)
            return f'Successfully downloaded "{object_name}" from bucket "{bucket_name}"'
        except ClientError as be:
            if be.response['Error']['Code'] == 'NoSuchBucket':
                return f'Bucket "{bucket_name}" does not exist'
            if be.response['Error']['Code'] == 'NoSuchKey':
                return f'Object "{object_name}" not found in bucket "{bucket_name}"'
            return f"Error generating download URL: {str(be)}"
    except Exception as e:
        return f"Error: {str(e)}"

def cos_delete_object(query: str) -> str:
    """Delete an object from a bucket"""
    try:
        parts = query.strip().split(' ', 1)
        if len(parts) != 2:
            return "Error: Please provide bucket name and object name"
            
        bucket_name, object_name = parts
        client = get_cos_client()
        try:
            client.delete_object(Bucket=bucket_name, Key=object_name)
            return f'Successfully deleted object "{object_name}" from bucket "{bucket_name}"'
        except ClientError as be:
            if be.response['Error']['Code'] == 'NoSuchBucket':
                return f'Bucket "{bucket_name}" does not exist'
            if be.response['Error']['Code'] == 'NoSuchKey':
                return f'Object "{object_name}" not found in bucket "{bucket_name}"'
            return f"Error deleting object: {str(be)}"
    except Exception as e:
        return f"Error: {str(e)}"

def cos_delete_bucket(query: str) -> str:
    """Delete a bucket (must be empty)"""
    try:
        bucket_name = query.strip()
        if not bucket_name:
            return "Error: Bucket name not provided"
            
        client = get_cos_client()
        try:
            client.delete_bucket(Bucket=bucket_name)
            return f'Successfully deleted bucket "{bucket_name}"'
        except ClientError as be:
            if be.response['Error']['Code'] == 'NoSuchBucket':
                return f'Bucket "{bucket_name}" does not exist'
            if be.response['Error']['Code'] == 'BucketNotEmpty':
                return f'Cannot delete bucket "{bucket_name}" because it is not empty'
            return f"Error deleting bucket: {str(be)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Create Tool instances
cos_tools = [
    Tool(
        name="cos_list_buckets",
        func=cos_list_buckets,
        description="List all buckets in the account"
    ),
    Tool(
        name="cos_create_bucket",
        func=cos_create_bucket,
        description="Create a new bucket. Input format: 'bucket_name'"
    ),
    Tool(
        name="cos_list_objects",
        func=cos_list_objects,
        description="List all objects in a bucket. Input format: 'bucket_name'"
    ),
    Tool(
        name="cos_upload_from_uploads",
        func=cos_upload_from_uploads,
        description="Upload a file from the uploads directory to a bucket. Input format: 'bucket_name file_name'"
    ),
    Tool(
        name="cos_download_file",
        func=cos_download_file,
        description="Download a file from a bucket. Input format: 'bucket_name object_name'"
    ),
    Tool(
        name="cos_delete_object",
        func=cos_delete_object,
        description="Delete an object from a bucket. Input format: 'bucket_name object_name'"
    ),
    Tool(
        name="cos_delete_bucket",
        func=cos_delete_bucket,
        description="Delete a bucket (must be empty). Input format: 'bucket_name'"
    )
] 