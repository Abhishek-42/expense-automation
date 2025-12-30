import boto3


#S3 Bucket Import

s3_client = boto3.client(
    "s3",
    region_name="ap-south-1"
)

bucket_name = "expense-automation-transactions"


#DynamoDB Import

dynamodb = boto3.resource(
    "dynamodb",
    region_name="ap-south-1"
)

transactions_table = dynamodb.Table("transactions")