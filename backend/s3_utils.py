import boto3
from botocore.exceptions import ClientError
from backend import config


def upload_fileobj(file_obj, key, bucket_name=None, region=None):
    bucket_name = bucket_name or config.AWS_S3_BUCKET
    if not bucket_name:
        raise RuntimeError("S3 bucket name is not configured (AWS_S3_BUCKET)")

    # Build a boto3 session/client using configured credentials if present
    region = region or config.AWS_DEFAULT_REGION
    if config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY:
        session = boto3.session.Session(
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=region,
        )
        s3 = session.client('s3')
    else:
        # Let boto3 use its default credential resolution (env, shared config, IAM role)
        s3 = boto3.client('s3', region_name=region) if region else boto3.client('s3')
    try:
        try:
            file_obj.seek(0)
        except Exception:
            pass
        try:
            s3.upload_fileobj(file_obj, bucket_name, key, ExtraArgs={'ContentType': 'text/csv'})
        except TypeError:
            # Fallback for older botocore that doesn't support ExtraArgs on upload_fileobj
            file_obj.seek(0)
            s3.put_object(Bucket=bucket_name, Key=key, Body=file_obj.read(), ContentType='text/csv')

        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key}, ExpiresIn=3600)
        return {"key": key, "url": url}
    except ClientError as e:
        err = e.response.get('Error', {}).get('Message', str(e))
        raise RuntimeError(f"S3 ClientError: {err}")
