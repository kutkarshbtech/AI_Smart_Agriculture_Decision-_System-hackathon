"""
AWS service clients - centralized boto3 session management.
"""
import boto3
from botocore.config import Config
from functools import lru_cache
from app.core.config import settings


@lru_cache()
def get_boto3_session():
    """Create a reusable boto3 session."""
    return boto3.Session(
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )


def get_s3_client(region_name: str = None):
    if region_name:
        return get_boto3_session().client("s3", region_name=region_name)
    return get_boto3_session().client("s3")


def get_dynamodb_resource():
    return get_boto3_session().resource("dynamodb")


def get_sagemaker_runtime():
    return get_boto3_session().client(
        "sagemaker-runtime",
        config=Config(
            read_timeout=60,
            connect_timeout=10,
            retries={"max_attempts": 1},
        ),
    )


def get_bedrock_runtime():
    return get_boto3_session().client(
        "bedrock-runtime", region_name=settings.BEDROCK_REGION
    )


def get_rekognition_client():
    return get_boto3_session().client("rekognition")


def get_sns_client():
    return get_boto3_session().client("sns")


def get_ses_client():
    return get_boto3_session().client("ses")


def get_transcribe_client():
    return get_boto3_session().client(
        "transcribe", region_name=settings.TRANSCRIBE_REGION
    )


def get_polly_client():
    return get_boto3_session().client(
        "polly", region_name=settings.POLLY_REGION
    )


def get_location_client():
    return get_boto3_session().client("location")


def get_lambda_client():
    return get_boto3_session().client("lambda")


def get_stepfunctions_client():
    return get_boto3_session().client("stepfunctions")
