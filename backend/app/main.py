from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.db import s3_client, bucket_name  , transactions_table , user_ids
import csv
import io
import uuid
from decimal import Decimal as dec

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/transactions")
async def upload_transactions(user_id: str,file: UploadFile = File(...)):
    response = user_ids.get_item(
        Key = {"user_id":user_id}
    )
    if "Item" not in response:
        return {"Error" : "User not found"}
    
    if not file.filename.endswith(".csv"):
        return {"error": "only csv allowed"}
    

    content = await file.read()
    text = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))

    #Creating Python Dictionary
    rows = []
    for row in reader:
        rows.append({
            "date": row["date"],
            "description": row["description"],
            "amount": float(row["amount"])
        })

        #For Dynamo DB value insertion 
        item ={
            "transaction_id" : str(uuid.uuid4()),
            "user_id" : user_id,
            "Service_Name" : row["description"],
            "amount" : dec(row["amount"]),
            "date" : row["date"]
        }
        transactions_table.put_item(Item=item)

    if len(content) > 5 * 1024 * 1024:
        return {"error": "file too large"}

    s3_client.put_object(
        Bucket=bucket_name,
        Key=file.filename,
        Body=content
    )

    return {"message": "file uploaded"}
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

@app.post("/user")
def create_user(user_id:str):
    response = user_ids.get_item(
        Key={"user_id": user_id}
    )
    if "Item" in response:
        return {"error": "user already exists"}
    
    user_ids.put_item(
        Item={"user_id": user_id}
    )

    return{
        "Status": "User Created"
    }


