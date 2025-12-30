import aws_cdk as core
import aws_cdk.assertions as assertions

from expense_automation.expense_automation_stack import ExpenseAutomationStack

# example tests. To run these tests, uncomment this file along with the example
# resource in expense_automation/expense_automation_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ExpenseAutomationStack(app, "expense-automation")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
