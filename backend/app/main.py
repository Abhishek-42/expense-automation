from fastapi import FastAPI, UploadFile, File
from app.db import s3_client, bucket_name  , transactions_table
import csv
import io
import uuid
from decimal import Decimal as dec



app=FastAPI()

@app.post("/upload/transactions")
async def upload_transactions(file: UploadFile = File(...)):
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
            "User-id" : "test_user",
            "Name-of-service" : row["description"],
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
def get_transactions():
    response = transactions_table.scan()
    return {"items": response["Items"]}
