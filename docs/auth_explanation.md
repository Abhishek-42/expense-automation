# Understanding the Custom Login System

This document explains the steps we took to replace the simple `?user_id` system with a real, industry-standard **JSON Web Token (JWT)** login system. 

We made changes in primarily two files: `auth.py` and `main.py`.

---

## 1. Creating the Security File (`backend/app/auth.py`)

This is a brand new file we created. Its entire job is to handle the complex math of security so our main application file doesn't get cluttered.

**What we added here:**
1. **Password Hashing (Scrambling):**
   - We imported a tool called `CryptContext` from the `passlib` library.
   - We created a function called `get_password_hash(password)`. This takes a plain password like "apple123" and runs it through an algorithm (bcrypt) to turn it into gibberish like `$2b$12$xYz...`. We save this gibberish in the database to protect users.
   - We created `verify_password(plain, hashed)` to check if a typed password matches the gibberish in the database.

2. **Generating the JWT Token:**
   - We created a function called `create_access_token(data)`.
   - When a user successfully logs in, this function creates a temporary "digital keycard" (a Token). It stamps it with an expiration time (e.g., 30 minutes from now) and signs it using our `SECRET_KEY` so users can't forge fake tokens.

3. **Defining the JSON Shapes (Pydantic Models):**
   - We created a `UserCreate` class. This tells FastAPI: "When someone registers, expect them to send a JSON body that has exactly two text fields: a `username` and a `password`."

### How `main.py` Connects to `auth.py`

To make these two files talk to each other, we used a simple Python `import` statement at the top of `main.py`:

```python
from app.auth import get_password_hash, verify_password, create_access_token, UserCreate, Token
```

- `app.auth` tells Python to look inside the `app` folder and find the `auth.py` file.
- The `import` keyword then pulls in exactly the specific tools (`get_password_hash`, etc.) we just built in `auth.py`. 
- By importing them instead of copying them, our `main.py` file stays clean and only focuses on handling the web traffic (the endpoints).

---

## 2. Updating the Main Endpoints (`backend/app/main.py`)

We deleted the old `@app.post("/user")` endpoint because it was insecure (it just grabbed a `user_id` from the URL). We replaced it with two new, secure endpoints.

### The New Registration Endpoint (`/register`)

```python
@app.post("/register")
def register_user(user: UserCreate):
```
**How it works:**
1. You send a JSON body (e.g., `{"username": "kabir", "password": "mypassword"}`).
2. FastAPI automatically checks that your JSON matches our `UserCreate` rules.
3. The code asks the `User_IDs` DynamoDB table if "kabir" already exists. If yes, it throws an error.
4. If the user is new, it calls our `get_password_hash()` function from `auth.py` to scramble the password.
5. It saves the `user_id` and the `hashed_password` to DynamoDB.

### The New Login Endpoint (`/token`)

```python
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
```
**How it works:**
1. This is a built-in FastAPI pattern. It expects you to send your username and password as standard "form data".
2. It fetches the user record from DynamoDB based on the username.
3. It takes the password you just typed, scrambles it, and uses our `verify_password()` function to see if it perfectly matches the safely stored password in DynamoDB.
4. If it doesn't match, you get an "Incorrect username or password" error.
5. If it does match, it calls `create_access_token()` to mint your new digital keycard (JWT) and hands it back to you.

---

## 3. How to Test the New Endpoints

You can test these endpoints directly in your browser using FastAPI's built-in Swagger UI, or you can use Postman. 

Before testing, make sure your FastAPI server is running (`uvicorn app.main:app --reload` from inside the `backend` folder).

### Option A: Testing via Browser (Easiest)
1. Open your web browser and go to: `http://127.0.0.1:8000/docs`
2. **To Register:**
   - Click on the green `POST /register` box.
   - Click the "Try it out" button.
   - Edit the JSON in the "Request body" box to have a custom `username` and `password`.
   - Click the large blue **Execute** button. You should see a success message.
3. **To Login:**
   - Click on the green `POST /token` box.
   - Click the "Try it out" button.
   - Type the exact same `username` and `password` into the standard text boxes (do *not* use JSON for this one, just standard text).
   - Click the blue **Execute** button.
   - Look at the "Server response". You will see an `"access_token": "eyJhbGciOiJIUzI1..."`. This is your secure digital keycard!

### Option B: Testing via Postman
1. **To Register:**
   - Create a `POST` request to `http://127.0.0.1:8000/register`.
   - Go to the **Body** tab, select **raw**, and choose **JSON** from the dropdown loop.
   - Paste the following exactly as written and click **Send**:
     ```json
     {
         "username": "kabir_test",
         "password": "my_secure_password"
     }
     ```
2. **To Login:**
   - Create a new `POST` request to `http://127.0.0.1:8000/token`.
   - Go to the **Body** tab and select **x-www-form-urlencoded** (FastAPI explicitly requires the password data to be sent as a form, not as JSON).
   - Add a Key called `username` and set the Value to your username (`kabir_test`).
   - Add a Key called `password` and set the Value to your password (`my_secure_password`).
   - Click **Send**. The response body will contain your new JWT Token.
