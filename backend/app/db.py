import boto3
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "expense-automation-transactions")

# s3 client for file uploads
s3_client = boto3.client("s3", region_name=AWS_REGION)
bucket_name = BUCKET_NAME

# ses client for sending emails
ses_client = boto3.client("ses", region_name=AWS_REGION)

# dynamodb setup
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

transactions_table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE_TRANSACTIONS", "transactions"))
user_ids = dynamodb.Table(os.environ.get("DYNAMODB_TABLE_USERS", "User_IDs"))
subscriptions_table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE_SUBSCRIPTIONS", "Subscriptions"))