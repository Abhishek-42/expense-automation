from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.auth import get_password_hash, verify_password, create_access_token, UserCreate, Token, get_current_user
from app.db import s3_client, bucket_name, transactions_table, user_ids, subscriptions_table
from app.engine import detect_subscriptions
from decimal import Decimal as dec
import csv
import io
import hashlib


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hardcoded test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "password123"

MAX_FILE_SIZE = 5 * 1024 * 1024
REQUIRED_COLUMNS = {"date", "description", "amount"}


# ──────────────────────────────────────────────
#  TRANSACTION UPLOAD & SUBSCRIPTION DETECTION
# ──────────────────────────────────────────────

@app.post("/upload/transactions")
async def upload_transactions(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    user_id = current_user

    if not file.filename.endswith(".csv"):
        return {"error": "only csv allowed"}

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        return {"error": "file too large"}

    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        return {"error": "Invalid CSV format"}

    #Creating Python Dictionary
    rows = []
    for row in reader:
        rows.append({
            "date": row["date"],
            "description": row["description"],
            "amount": float(row["amount"])
        })

        # Deterministic hash for deduplication
        raw_tx_str = f"{user_id}-{row['date']}-{row['description']}-{row['amount']}"
        tx_id = hashlib.md5(raw_tx_str.encode()).hexdigest()

        #For Dynamo DB value insertion
        item = {
            "transaction_id": tx_id,
            "user_id": user_id,
            "Service_Name": row["description"],
            "amount": dec(row["amount"]),
            "date": row["date"]
        }
        transactions_table.put_item(Item=item)

    # Store raw CSV in S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f"{user_id}/{file.filename}",
        Body=content
    )

    # Run subscription detection engine
    detected_subs = detect_subscriptions(rows)

    for sub in detected_subs:
        raw_sub_str = f"sub-{user_id}-{sub['merchant_name']}"
        sub_id = hashlib.md5(raw_sub_str.encode()).hexdigest()

        sub_item = {
            "user_id": user_id,
            "subscription_id": sub_id,
            "merchant_name": sub["merchant_name"],
            "average_amount": dec(str(sub["average_amount"])),
            "billing_cycle_days": dec(str(sub["billing_cycle_days"])),
            "last_payment_date": sub["last_payment_date"],
            "confidence_based_on_tx_count": sub["original_transactions_count"]
        }
        subscriptions_table.put_item(Item=sub_item)

    return {
        "message": "file uploaded",
        "transactions_processed": len(rows),
        "subscriptions_detected": len(detected_subs)
    }


# ──────────────────────────────────────────────
#  DATA RETRIEVAL ENDPOINTS
# ──────────────────────────────────────────────

@app.get("/subscriptions")
def get_subscriptions(current_user: str = Depends(get_current_user)):
    response = subscriptions_table.scan(
        FilterExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": current_user}
    )
    return {"subscriptions": response.get("Items", [])}


@app.get("/transactions")
def get_transactions(user_id: str):
    response = transactions_table.scan(
        FilterExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id}
    )
    return {"items": response["Items"]}


@app.get("/health")
def health():
    return {"status": "ok"}


# ──────────────────────────────────────────────
#  AUTH ENDPOINTS
# ──────────────────────────────────────────────

@app.post("/register")
def register_user(user: UserCreate):
    response = user_ids.get_item(Key={"user_id": user.username})
    if "Item" in response:
        return {"error": "user already exists"}

    hashed_password = get_password_hash(user.password)
    user_ids.put_item(
        Item={
            "user_id": user.username,
            "hashed_password": hashed_password
        }
    )
    return {"message": "User registered successfully"}


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Hardcoded test bypass
    if form_data.username == TEST_USERNAME and form_data.password == TEST_PASSWORD:
        access_token = create_access_token(data={"sub": TEST_USERNAME})
        return {"access_token": access_token, "token_type": "bearer"}

    response = user_ids.get_item(Key={"user_id": form_data.username})
    user_record = response.get("Item")

    if not user_record or not verify_password(form_data.password, user_record.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
