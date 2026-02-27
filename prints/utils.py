import boto3
from django.conf import settings
import uuid
import os
from pypdf import PdfReader
import io

def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )

def upload_file_to_r2(file_obj, file_name, content_type=None):
    """
    Upload a single file to R2.
    Returns the public URL of the file.
    """
    client = get_r2_client()
    
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type

    # Generate a unique file name to avoid collisions
    ext = os.path.splitext(file_name)[1]
    unique_name = f"{uuid.uuid4()}{ext}"

    client.upload_fileobj(
        file_obj,
        settings.R2_BUCKET_NAME,
        unique_name,
        ExtraArgs=extra_args if extra_args else None,
    )
    
    # Construct public URL
    # If R2_PUBLIC_URL_BASE is set, use it. Otherwise, return the name/path.
    if settings.R2_PUBLIC_URL_BASE:
        return f"{settings.R2_PUBLIC_URL_BASE.rstrip('/')}/{unique_name}"
    
    return unique_name

def get_pdf_page_count(file_obj):
    """
    Returns the number of pages in a PDF file.
    """
    try:
        # Seek to beginning in case it was read before
        file_obj.seek(0)
        reader = PdfReader(file_obj)
        count = len(reader.pages)
        # Seek back to beginning for next operation (like upload)
        file_obj.seek(0)
        return count
    except Exception as e:
        print(f"Error counting PDF pages: {e}")
        return 0
