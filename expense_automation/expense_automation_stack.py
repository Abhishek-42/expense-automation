from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_dynamodb as db


from constructs import Construct

class ExpenseAutomationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs , description= "Expense Handler")

        s3_b= s3.Bucket(
                self , 
                "Transaction-bucket" , 
                bucket_name= "expense-automation-transactions",
                block_public_access= s3.BlockPublicAccess.BLOCK_ALL
                )
        
        db.Table(
            self,
            "Transaction-history-data",
            table_name= "transactions",
            partition_key= db.Attribute(
                name="transaction_id",
                type=db.AttributeType.STRING
            )
        )

        db.Table(
            self,
            "User_ID_data",
            table_name= "User_IDs",
            partition_key= db.Attribute(
                name="user_id",
                type=db.AttributeType.STRING
            )
        )


