from fastapi import FastAPI, UploadFile, File
from app.db import s3_client, bucket_name
import csv
import io


app=FastAPI()

@app.post("/upload/transactions")
async def upload_transactions(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        return {"error": "only csv allowed"}

    content = await file.read()
    text = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))

    rows = []
    for row in reader:
        rows.append({
            "date": row["date"],
            "description": row["description"],
            "amount": float(row["amount"])
        })

    if len(content) > 5 * 1024 * 1024:
        return {"error": "file too large"}

    s3_client.put_object(
        Bucket=bucket_name,
        Key=file.filename,
        Body=content
    )

    #return {"message": "file uploaded"}
    return {"transactions": rows}

