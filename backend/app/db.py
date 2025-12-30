import boto3

s3_client = boto3.client(
    "s3",
    region_name="ap-south-1"
)

bucket_name = "expense-automation-transactions"