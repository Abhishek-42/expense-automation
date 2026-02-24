@echo off

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo Changing to backend directory...
cd backend

echo Installing Python requirements...
python -m pip install -r requirements.txt

echo Starting FastAPI server with Uvicorn...
echo Opening Frontend in browser...
start "" "..\frontend\index.html"
python -m uvicorn app.main:app --reload

pause
