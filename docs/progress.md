# Project Progress Tracker

## Objective
Build a cloud-based financial tracking application to automatically identify and manage recurring subscriptions and regular bill payments from bank transaction history.

## Current Status: Initial Setup & Setup Refinement

---

## Phases & Tasks

### Phase 1: Infrastructure Foundations (AWS CDK)
- [x] Configure AWS CDK project structure
- [x] Provision S3 bucket for CSV uploads (`expense-automation-transactions`)
- [x] Provision DynamoDB Table for Users (`User_IDs`)
- [x] Provision DynamoDB Table for raw/parsed transactions (`transactions`)
- [ ] Provision DynamoDB Table for Subscriptions (Metadata storage)
- [ ] Setup AWS EventBridge for scheduled tasks
- [ ] Setup Amazon SES for email notifications

### Phase 2: Core API & Data Ingestion (FastAPI)
- [x] Initialize FastAPI application
- [x] Implement User Creation Endpoint (`POST /user`)
- [x] Implement Health Check Endpoint (`GET /health`)
- [ ] Implement secure CSV upload endpoint (`POST /upload/transactions`)
  - [x] Basic file validation & S3 upload
  - [x] Raw transaction storage to DynamoDB
  - [ ] **Pending**: Filter debit entries
  - [ ] **Pending**: Normalize merchant names

### Phase 3: Subscription Detection Engine
- [ ] Develop rule-based pattern recognition
  - [ ] Detect consistent merchant identity
  - [ ] Detect similar amounts within tolerance
  - [ ] Detect recurring intervals (e.g., 28-31 days)
- [ ] Extract and store subscription metadata (merchant, average amount, billing cycle, last payment, next expected date, confidence score)
- [ ] Save processed subscriptions to DynamoDB

### Phase 4: Notification System
- [ ] Create AWS Lambda function to evaluate upcoming due dates
- [ ] Query DynamoDB for subscriptions due within 3-5 days
- [ ] Integrate Amazon SES to send email reminders

---

## Known Bugs & Errors
_No critical errors recorded yet._

## Pending Questions / Decisions
- What specific tolerance range should we use for matching "similar amounts" during subscription detection?
- How should we normalize merchant names? (e.g., regex to strip store numbers, dates, or non-alphanumeric chars)
- What email address or domain will we use for Amazon SES, and is it verified in AWS?
