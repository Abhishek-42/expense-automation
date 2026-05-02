import os
from aws_cdk import Stack, RemovalPolicy, Duration, SecretValue
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_dynamodb as db
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets

from constructs import Construct

class ExpenseAutomationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs , description= "Expense Handler")

        # create s3 bucket for csv files
        s3_b = s3.Bucket(
                self,
                "Transaction-bucket",
                bucket_name="expense-automation-transactions",
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                enforce_ssl=True,
                lifecycle_rules=[
                    s3.LifecycleRule(expiration=Duration.days(365))
                ]
        )
        
        # dynamodb tables
        t_table = db.Table(
            self,
            "Transaction-history-data",
            table_name="transactions",
            partition_key=db.Attribute(name="transaction_id", type=db.AttributeType.STRING),
            billing_mode=db.BillingMode.PAY_PER_REQUEST
        )

        u_table = db.Table(
            self,
            "User_ID_data",
            table_name="User_IDs",
            partition_key=db.Attribute(name="user_id", type=db.AttributeType.STRING),
            billing_mode=db.BillingMode.PAY_PER_REQUEST
        )

        s_table = db.Table(
            self,
            "Subscriptions_data",
            table_name="Subscriptions",
            partition_key=db.Attribute(name="user_id", type=db.AttributeType.STRING),
            sort_key=db.Attribute(name="subscription_id", type=db.AttributeType.STRING),
            billing_mode=db.BillingMode.PAY_PER_REQUEST
        )

        # setup eventbridge for daily email triggers
        base_url = os.environ.get("BACKEND_PUBLIC_URL", "http://0.0.0.0:8000")
        target_endpoint = f"{base_url}/admin/trigger-notifications"

        # need a connection for api destinations 
        eb_connection = events.Connection(self, "BackendConnection",
            authorization=events.Authorization.api_key(
                "x-api-key", 
                SecretValue.unsafe_plain_text("dev-secret-key") # TODO: move to secrets manager later
            )
        )

        destination = events.ApiDestination(self, "NotifyEndpoint",
            connection=eb_connection,
            endpoint=target_endpoint,
            http_method=events.HttpMethod.POST
        )

        # run at 9am everyday
        daily_rule = events.Rule(self, "DailyTriggerRule",
            schedule=events.Schedule.cron(minute="0", hour="9")
        )

        daily_rule.add_target(targets.ApiDestination(destination))
