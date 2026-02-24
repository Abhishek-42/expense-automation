from fastapi import FastAPI, UploadFile, File , Form, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import get_password_hash, verify_password, create_access_token, UserCreate, Token, get_current_user
from fastapi.middleware.cors import CORSMiddleware
from app.db import s3_client, bucket_name, transactions_table, user_ids, subscriptions_table
from app.engine import detect_subscriptions
import csv
import io
import uuid
import hashlib
from decimal import Decimal as dec

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/transactions")
async def upload_transactions(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Securely uploads a CSV file of transactions for the currently logged-in user."""
    
    # We no longer need to check if user_id exists here, because the JWT token 
    # guarantees they are logged in. The username is inside current_user.
    user_id = current_user
    
    if not file.filename.endswith(".csv"):
        return {"error": "only csv allowed"}
    
    content = await file.read()
    
    if len(content) > 5 * 1024 * 1024:
        return {"error": "file too large"}
    text = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))

    required_cols = {"date", "description", "amount"}

    if not reader.fieldnames or not required_cols.issubset(set(reader.fieldnames)):
        return {"error": "Invalid CSV format"}

    #Creating Python Dictionary
    rows = []
    for row in reader:
        rows.append({
            "date": row["date"],
            "description": row["description"],
            "amount": float(row["amount"])
        })

        # Generate a deterministic hash for deduplication
        # If the same user uploads the same transaction date + desc + amount, it yields the exact same ID
        raw_tx_str = f"{user_id}-{row['date']}-{row['description']}-{row['amount']}"
        tx_id = hashlib.md5(raw_tx_str.encode()).hexdigest()

        #For Dynamo DB value insertion 
        item ={
            "transaction_id" : tx_id,
            "user_id" : user_id,
            "Service_Name" : row["description"],
            "amount" : dec(row["amount"]),
            "date" : row["date"]
        }
        transactions_table.put_item(Item=item)

    

    s3_client.put_object(
        Bucket=bucket_name,
        Key=f"{user_id}/{file.filename}",
        Body=content
    )

    # --- NEW: Run the Subscription Detection Engine ---
    detected_subs = detect_subscriptions(rows)
    
    # Save any found subscriptions to our new DynamoDB table
    for sub in detected_subs:
        # Generate deterministic subscription ID based on user and merchant
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

@app.get("/subscriptions")
def get_subscriptions(current_user: str = Depends(get_current_user)):
    """Fetch all detected subscriptions for the logged-in user."""
    response = subscriptions_table.scan(
        FilterExpression="user_id = :uid",
        ExpressionAttributeValues={
            ":uid": current_user
        }
    )
    return {"subscriptions": response.get("Items", [])}
    #return {"transactions": rows}
    #return {"transaction" : item}

@app.get("/transactions")
def get_transactions(user_id:str):
    response = transactions_table.scan(
        FilterExpression="user_id = :uid",
        ExpressionAttributeValues={
            ":uid": user_id
        }
    )
    return {"items": response["Items"]}

@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/register")
def register_user(user: UserCreate):
    """Register a new user with a hashed password."""
    # Check if user already exists
    response = user_ids.get_item(Key={"user_id": user.username})
    if "Item" in response:
        return {"error": "user already exists"}
    
    # Hash the password and save to DynamoDB
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
    """Login endpoint to authenticate a user and return a JWT token."""
    # Fetch user from DynamoDB
    response = user_ids.get_item(Key={"user_id": form_data.username})
    user_record = response.get("Item")
    
    # Verify user exists and password matches
    if not user_record or not verify_password(form_data.password, user_record.get("hashed_password", "")):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate the JWT token
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
