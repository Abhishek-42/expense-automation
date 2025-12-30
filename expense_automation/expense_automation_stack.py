from aws_cdk import Stack
from aws_cdk import aws_s3 as s3

from constructs import Construct

class ExpenseAutomationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_b= s3.Bucket(
                self , 
                "Transaction-bucket" , 
                bucket_name= "expense-automation-transactions",
                block_public_access= s3.BlockPublicAccess.BLOCK_ALL
                )
        
        

