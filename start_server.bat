@echo off

echo Activate virtual environment
call .\.venv\Scripts\activate.bat

echo change dir
cd backend

echo Installing Python requirements
python -m pip install -r requirements.txt

echo Starting FastAPI server with Uvicorn
echo Opening Frontend in browser
start "" "..\frontend\index.html"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
