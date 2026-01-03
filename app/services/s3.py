import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from io import BytesIO
from datetime import datetime
import uuid
import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class S3Service:
    """AWS S3 service for image storage"""

    def __init__(self):
        settings = get_settings()

        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise ValueError("AWS credentials not configured")

        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(signature_version="s3v4")
        )
        self.bucket = settings.aws_s3_bucket
        self.region = settings.aws_region

    def upload_image(
        self,
        image_bytes: bytes,
        campaign_id: str,
        filename: Optional[str] = None
    ) -> dict:
        """
        Upload image to S3

        Args:
            image_bytes: PNG image bytes
            campaign_id: Campaign ID for organizing files
            filename: Optional custom filename

        Returns:
            dict with s3_key, url, success
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]

        if filename:
            s3_key = f"campaigns/{campaign_id}/{filename}"
        else:
            s3_key = f"campaigns/{campaign_id}/{timestamp}_{unique_id}.png"

        try:
            self.s3.upload_fileobj(
                BytesIO(image_bytes),
                self.bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": "image/png",
                    "CacheControl": "max-age=31536000",
                }
            )

            # Public URL (bucket must have public read policy)
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"

            logger.info(f"Image uploaded to S3: {s3_key}")

            return {
                "success": True,
                "s3_key": s3_key,
                "url": url,
            }

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def delete_image(self, s3_key: str) -> bool:
        """Delete image from S3"""
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"Image deleted from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False

    def get_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for temporary access

        Args:
            s3_key: S3 object key
            expires_in: Expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL
        """
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expires_in
        )

    def check_bucket_exists(self) -> bool:
        """Check if configured bucket exists"""
        try:
            self.s3.head_bucket(Bucket=self.bucket)
            return True
        except ClientError:
            return False


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Get singleton S3Service instance"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
