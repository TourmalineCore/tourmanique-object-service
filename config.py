"""Сonfiguration
Use env var to override
"""
import os

s3_endpoint = os.getenv('S3_ENDPOINT')
if s3_endpoint is None:
    raise ValueError('You should specify S3_ENDPOINT environment variable to be able to connect to S3 bucket.')

s3_access_key_id = os.getenv('S3_ACCESS_KEY_ID')
if s3_access_key_id is None:
    raise ValueError('You should specify S3_ACCESS_KEY_ID environment variable to be able to connect to S3 bucket.')

s3_secret_access_key = os.getenv('S3_SECRET_ACCESS_KEY')
if s3_secret_access_key is None:
    raise ValueError('You should specify S3_SECRET_ACCESS_KEY environment variable to be able to connect to S3 bucket.')

s3_bucket_name = os.getenv('S3_BUCKET_NAME')
if s3_bucket_name is None:
    raise ValueError('You should specify S3_BUCKET_NAME environment variable to be able to connect to S3 bucket.')

s3_prefix = os.getenv('S3_PREFIX', default='')

s3_use_ssl = os.getenv('S3_USE_SSL', default='true').lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup']
