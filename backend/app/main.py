from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.auth import hash_password, check_password, make_token, UserCreate, Token, get_current_user
from app.db import s3_client, bucket_name, transactions_table, user_ids, subscriptions_table
from app.engine import detect_subscriptions
from app.notifications import check_subs_and_email
from decimal import Decimal as dec
import csv
import io
import hashlib

app = FastAPI()

# allow all origins for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

max_size = 5 * 1024 * 1024
req_cols = {"date", "description", "amount"}

@app.post("/upload/transactions")
async def upload_transactions(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    uid = current_user

    if not file.filename.endswith(".csv"):
        return {"error": "only csv files are allowed"}

    content = await file.read()

    if len(content) > max_size:
        return {"error": "file is too big"}

    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames or not req_cols.issubset(set(reader.fieldnames)):
        return {"error": "bad csv format"}

    rows = []
    
    for row in reader:
        rows.append({
            "date": row["date"],
            "description": row["description"],
            "amount": float(row["amount"])
        })

        raw_str = f"{uid}-{row['date']}-{row['description']}-{row['amount']}"
        t_id = hashlib.sha256(raw_str.encode()).hexdigest()

        t_item = {
            "transaction_id": t_id,
            "user_id": uid,
            "service_name": row["description"],
            "amount": dec(row["amount"]),
            "date": row["date"]
        }
        transactions_table.put_item(Item=t_item)

    # upload the raw file to s3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f"{uid}/{file.filename}",
        Body=content
    )

    subs = detect_subscriptions(rows)

    for s in subs:
        raw_sub = f"sub-{uid}-{s['merchant_name']}"
        s_id = hashlib.sha256(raw_sub.encode()).hexdigest()

        s_item = {
            "user_id": uid,
            "subscription_id": s_id,
            "merchant_name": s["merchant_name"],
            "average_amount": dec(str(s["average_amount"])),
            "billing_cycle_days": dec(str(s["billing_cycle_days"])),
            "last_payment_date": s["last_payment_date"],
            "confidence_based_on_tx_count": s["original_transactions_count"]
        }
        subscriptions_table.put_item(Item=s_item)

    return {
        "msg": "uploaded okay",
        "processed": len(rows),
        "found_subs": len(subs)
    }

@app.get("/subscriptions")
def get_subscriptions(current_user = Depends(get_current_user)):
    res = subscriptions_table.scan(
        FilterExpression="user_id = :u",
        ExpressionAttributeValues={":u": current_user}
    )
    return {"subscriptions": res.get("Items", [])}

@app.get("/transactions")
def get_transactions(current_user = Depends(get_current_user)):
    res = transactions_table.scan(
        FilterExpression="user_id = :u",
        ExpressionAttributeValues={":u": current_user}
    )
    return {"items": res["Items"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/admin/trigger-notifications")
def trigger_notifications():
    res = check_subs_and_email()
    return res

@app.post("/register")
def register_user(user: UserCreate):
    res = user_ids.get_item(Key={"user_id": user.username})
    if "Item" in res:
        return {"error": "user already exists"}

    hashed = hash_password(user.password)
    user_ids.put_item(
        Item={
            "user_id": user.username,
            "email": user.email,
            "hashed_password": hashed
        }
    )
    return {"msg": "Registered ok"}

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    res = user_ids.get_item(Key={"user_id": form_data.username})
    u_rec = res.get("Item")

    if not u_rec or not check_password(form_data.password, u_rec.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = make_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}
