# Connecting the Frontend to the Backend

This document explains how our basic HTML, CSS, and JS frontend communicates with our FastAPI backend. It's built specifically to work with the secure JWT authentication system we created earlier.

## The Overall Flow

Because the frontend is running completely locally (just opening an HTML file on your computer) and the backend is running on a local development server (`http://127.0.0.1:8000`), the frontend uses JavaScript's built-in `fetch()` tool to send messages over the internet (or in this case, your local network) to the backend.

---

## 1. Registration Flow (`POST /register`)

When a user typing their information clicks "Sign Up", JavaScript catches the form submission:

1. **Extract Data:** It pulls the `username` and `password` out of the text boxes.
2. **Format as JSON:** It uses `JSON.stringify()` to turn those two variables into a standard JSON string.
3. **Send to Backend:** It sends a `POST` request to `http://127.0.0.1:8000/register`, telling the server `Content-Type: application/json` so FastAPI knows how to read it.
4. **Handle Response:** If the backend creates the user, the frontend shows a green success box and automatically switches over to the Login tab.

---

## 2. Login Flow (`POST /token`)

When a user clicks "Log In", a slightly different process happens because our FastAPI `/token` endpoint strictly requires "Form Data", not JSON.

1. **Extract Data:** It grabs the `username` and `password`.
2. **Format as Form Data:** Instead of JSON, JavaScript builds a special url-encoded string using `new URLSearchParams()`, mimicking how an old HTML `<form>` submits data.
3. **Send to Backend:** It sends a `POST` request to `http://127.0.0.1:8000/token`.
4. **Save the Token:** If the password is correct, the backend hands back the secure JWT Token. Our JavaScript immediately saves this token into the browser's hidden vault called **`localStorage`**. 
   - `localStorage.setItem('token', data.access_token);`
   - This prevents the user from having to log in every single time they refresh the page.
5. **Show Dashboard:** It hides the Login screen and reveals the Dashboard.

---

## 3. Secure File Upload Flow (`POST /upload/transactions`)

This is where the magic happens. We need to upload a CSV file, but we also must prove we are logged in.

1. **Get the File:** JavaScript grabs the raw CSV file the user selected.
2. **Build a Multipart Form:** It puts the file into a special `FormData` object. This allows us to transmit raw file bytes over the network.
3. **Retrieve the Keycard:** Before sending the request, JavaScript reaches back into `localStorage` and grabs the JWT Token it saved during step 2.
4. **Attach the Authorization Header:** It sends the `POST` request to `http://127.0.0.1:8000/upload/transactions`. Crucially, it adds a special instruction to the envelope:
   ```javascript
   headers: {
       'Authorization': `Bearer ${token}` 
   }
   ```
5. **Backend Verification:** The FastAPI backend receives the request. Before looking at the file, it reads the `Authorization` header, mathematically verifies the Token is real using its `SECRET_KEY`, and extracts the `username` from inside the token. If it matches, it processes the CSV and saves it to S3 under that user's name!
