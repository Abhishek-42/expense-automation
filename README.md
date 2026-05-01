# Expense Automation System

This is a backend project I built to help track and automatically detect recurring subscriptions from bank statements. 

## Overview

You can upload a CSV of your bank or credit card transactions. The backend (built with FastAPI) processes the CSV, cleans up the merchant names, and runs some logic to figure out which payments are recurring subscriptions. It looks for:
- Same merchant names
- Similar amounts
- A repeating time gap (like every 30 days)

The raw CSV is stored in an S3 bucket, but we only save the actual subscription data (like merchant name, amount, cycle days, and next payment date) into DynamoDB.

## Email Alerts

I also set up a notification system. Using AWS EventBridge and SES, the backend checks every day to see if any subscriptions are coming up in the next 3 days. If it finds one, it sends you an email reminder so you don't get charged unexpectedly.

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** DynamoDB
- **Storage:** Amazon S3
- **Emails:** Amazon SES
- **Infra:** AWS CDK

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Deploy the CDK stack: `cdk deploy`
3. Run the FastAPI server: `uvicorn app.main:app --reload`

