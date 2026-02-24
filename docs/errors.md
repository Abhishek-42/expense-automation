# Project Error Log

This document serves as a tracking log for the bugs and errors we encounter while building the Expense Automation System. Each error is broken down in simple terms so we understand exactly *why* it happened, *what* it broke, and *how* we fixed it.

---

## 1. The Missing "Form Data" Reader Error 
**Date Encountered:** During initial test of the `/token` login endpoint.

### What the Error Looked Like
```text
RuntimeError: Form data requires "python-multipart" to be installed.
```

### What It Was Doing
FastAPI is an incredible tool that automatically reads JSON data for us (like when we use the `/register` endpoint). However, the `/token` endpoint doesn't use JSON. It forces you to send your username and password the exact same way old-school HTML websites do: as **"Form Data"**. 

FastAPI actually does *not* know how to read Form Data by default. It relies on a hidden helper library called `python-multipart` to translate the Form Data so our Python code can understand it. Because we didn't have that helper library installed in our virtual environment, FastAPI crashed and threw its hands up in the air the second we clicked "Login".

### How We Fixed It
1. We installed the missing helper library directly into our hidden Python bubble (the `.venv`) by running: `pip install python-multipart`.
2. We used the command `pip freeze > requirements.txt` to safely write down the exact name of this helper library into our master list of dependencies.
3. Because our `start_server.bat` file is programmed to automatically read the `requirements.txt` file every single time the server boots up, we guaranteed that this helper library will never be missing again, even if we move the code to a new computer.

---

## 2. The Password Scrambler Compatibility Crash
**Date Encountered:** During initial test of the `/register` endpoint.

### What the Error Looked Like
```text
AttributeError: module 'bcrypt' has no attribute '__about__'
```

### What It Was Doing
This is a classic "Supply Chain" bug in modern software development—where two different pieces of software you rely on stop talking to one another correctly.

Here is the chain of events:
- To scramble passwords, we use a library called `passlib`.
- But `passlib` is kind of lazy. It doesn't actually do the scrambling itself; it asks a different, lower-level library called `bcrypt` to do the heavy math.
- Recently, the creators of `bcrypt` released a brand new version (v4.1.0). In this new version, they decided to delete an old, useless line of code called `__about__`.
- The problem is that the creators of `passlib` haven't updated their code in a few years. `passlib` is still hard-coded to look for that `__about__` line. The second it asks the new `bcrypt` to scramble our password, it realizes `__about__` is missing, panics, and crashes our entire registration process with a `500 Internal Server Error`.

### How We Fixed It
The easiest way to fix a conflict like this is to simply "downgrade" the problematic library back to a version where it still worked perfectly. 

1. We told our virtual environment to forcefully install an older version of the math library (specifically version `4.0.1` because that was the last version that still included the `__about__` line). We did this by running: `pip install "bcrypt<4.1.0"`.
2. To ensure Python never accidentally updates `bcrypt` to the newer, broken version in the future, we ran `pip freeze > requirements.txt`. This hard-coded the exact safe version (`bcrypt==4.0.1`) into our project's DNA.

## 3. The "Failed to connect" vs "Incorrect Password" Error
**Date Encountered:** During initial test of the frontend Login form.

### What the Error Looked Like
Instead of telling the user they typed the wrong password, the UI popped up a red box saying: `Failed to connect to server`.

### What It Was Doing
This was a miscommunication between how our `/token` backend endpoint sends "Bad Password" errors and how our JavaScript frontend expects to read them.

Usually, when we write API endpoints in FastAPI, we return custom JSON dictionaries like `{"error": "user already exists"}`. Our JavaScript frontend was explicitly programmed to look for this `data.error` key and show its message to the user.

However, the `/token` endpoint is special. It uses FastAPI's built-in `OAuth2PasswordRequestForm` security tool. When this security tool detects a bad password, it doesn't return `{"error": ...}`. Instead, it throws an official HTTP 400 error containing a `detail` key:
```json
{"detail": "Incorrect username or password"}
```

Because our JavaScript couldn't find `data.error` in that JSON response, its logic fell apart, causing it to trigger the final `catch(err)` block—which is only meant to be used when the server is completely offline!

### How We Fixed It
We updated the JavaScript `fetch` code in `app.js` to look for *both* types of error keys. 
We changed `showNotification(data.error)` to:
```javascript
showNotification(data.detail || data.error || 'Incorrect username or password');
```
Now, if FastAPI sends a security `detail` message, the frontend will prioritize showing that specific message before falling back to generic errors.

## 4. The "ResponseValidationError" Crash
**Date Encountered:** During testing of incorrect passwords on the `/token` endpoint.

### What the Error Looked Like
```text
fastapi.exceptions.ResponseValidationError: 2 validation errors:
  {'type': 'missing', 'loc': ('response', 'access_token'), 'msg': 'Field required'}
  {'type': 'missing', 'loc': ('response', 'token_type'), 'msg': 'Field required'}
```

### What It Was Doing
This is an amazing example of FastAPI's strictness acting as a double-edged sword!

When we created the login endpoint, we wrote this specific line of code at the top of the function:
```python
@app.post("/token", response_model=Token)
```
The `response_model=Token` acts like a bouncer at a club. It mathematically *guarantees* that whatever leaves this function *must* be structured exactly like our standard JWT "Token" dictionary (meaning it *must* have an `access_token` string and a `token_type` string).

Inside the function, when someone typed a bad password, our old code did this:
```python
return {"error": "Incorrect username or password"}
```
The moment Python tried to `return` that dictionary, FastAPI's bouncer stepped in, looked at the dictionary, realized it was missing the required `access_token` and `token_type` strings, and immediately crashed the server with a `ResponseValidationError`. It completely refused to send the error message to the user!

### How We Fixed It
When writing FastAPI endpoints with strict `response_model` definitions, you are **not allowed** to `return` normal dictionaries if something goes wrong. Instead, you must **raise an HTTP Exception**. 

We replaced the normal `return` statement with an official FastAPI Exception:
```python
from fastapi import HTTPException, status
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)
```
Because it is technically an `Exception` (an alarm bell) rather than a normal `return` value, FastAPI's bouncer bypasses the strict `response_model` validation check and successfully sends the 401 Unauthorized error message straight to our JavaScript frontend.

## 5. The "KeyError: 'Service_Name'" Engine Crash
**Date Encountered:** During the first test of the Subscription Detection Engine.

### What the Error Looked Like
```text
    merchant = normalize_merchant_name(tx['Service_Name'])
                                       ~~^^^^^^^^^^^^^^^^
KeyError: 'Service_Name'
```

### What It Was Doing
A `KeyError` always means that Python is trying to open a dictionary and pull out a value using a specific label ("Key"), but that label doesn't actually exist in the dictionary.

When we wrote the `/upload/transactions` endpoint in `main.py`, we created a Clean Dictionary of the CSV rows that looked exactly like this:
```python
{
    "date": "2023-08-01",
    "description": "NETFLIX.COM",
    "amount": 15.49
}
```

However, when we wrote the Engine logic (`engine.py`), we accidentally told it to look for a key named `Service_Name`:
```python
merchant = normalize_merchant_name(tx['Service_Name'])
```
Because the dictionary only contained `date`, `description`, and `amount`, Python couldn't find `Service_Name`, threw a `KeyError`, and completely crashed the file upload process. 

### How We Fixed It
The fix was as simple as changing the label the Engine was looking for to match the label we actually created from the CSV file. 

We opened `/backend/app/engine.py` and changed `tx['Service_Name']` to `tx['description']`.

## 6. The "Decimal vs Float" Mathematics Crash
**Date Encountered:** During math calculations in the Subscription Detection Engine.

### What the Error Looked Like
```text
    total_amount += curr_tx['amount']
TypeError: unsupported operand type(s) for +=: 'decimal.Decimal' and 'float'
```

### What It Was Doing
Python is a very safe language when it comes to money.

When we parsed the CSV file, we told Python to treat the amount column as a `float` (a normal decimal number, like `15.49`).

However, inside our Subscription Detection Engine, we wanted to track the total sum of all payments to find the average. We created our tracking variable as a strict `Decimal` object:
```python
total_amount = Decimal(0)
```
When Python looped over the transactions and attempted to do: `Decimal(0) + 15.49 (float)`, it panicked. Python refuses to do math between a strict `Decimal` accounting object and a normal floating-point number, because floats can sometimes have weird microscopic inaccuracies (like `15.49000000000001`). 

### How We Fixed It
Because the Engine is just looking for a rough average to show the user, we don't need strict bank-level precision for `total_amount` here. 

We simply changed the tracking variable in `engine.py` from `Decimal(0)` to a standard float `0.0`. We also changed our tolerance check from `Decimal('5.00')` to simply `5.00`. This allows Python to add the CSV amounts together gracefully without crashing!

---
_Additional errors will be added below as the project progresses._
