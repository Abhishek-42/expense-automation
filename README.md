# Expense Automation System

The Expense Automation System is a cloud-based financial tracking application designed to automatically identify and manage recurring subscriptions and regular bill payments from a user’s bank transaction history.

## Overview

The system allows users to upload a CSV file exported from their bank or credit card provider, which contains detailed transaction records including dates, descriptions, and debit amounts. Once uploaded, the file is securely stored in Amazon S3 and processed by a backend service built using Python and FastAPI.

The application parses the transaction data, filters debit entries, normalizes merchant  names, and applies rule-based pattern recognition to detect recurring payments. A    transaction is classified as a subscription if it shows:    
- Consistent merchant identity   
- Similar transaction amounts within a defined tolerance range    
- A recurring interval (typically between 28 and 31 days across multiple cycles)

Instead of storing complete raw transaction history, the system retains only structured subscription metadata such as:
- Merchant name    
- Average billing amount   
- Billing cycle 
- Last payment date
- Next expected deduction date
- A confidence score indicating detection reliability

This processed data is stored in Amazon DynamoDB, enabling scalable and efficient user-specific data management.

## Automated Notifications

The system also includes an automated notification mechanism that proactively alerts users before upcoming deductions. A scheduled event, triggered using AWS EventBridge, periodically invokes backend logic to evaluate upcoming subscription due dates. If a recurring payment is expected within a predefined window, such as three to five days, the system sends an email reminder using Amazon Simple Email Service (SES), helping users maintain financial awareness and avoid unexpected deductions.

## Architecture & Technology Stack

The backend is implemented using FastAPI to ensure high performance and asynchronous request handling, while DynamoDB provides a flexible NoSQL data model optimized for scalable cloud environments. The overall architecture follows modern cloud-native design principles, emphasizing serverless integration, cost efficiency, data privacy, and modular processing.

By combining automated financial pattern detection with cloud infrastructure services, the Expense Automation System demonstrates practical backend engineering, event-driven design, and real-world problem solving suitable for a robust cloud project.  
