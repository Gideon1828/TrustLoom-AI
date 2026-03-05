# Start Backend API Server
Write-Host "Starting Backend API Server..." -ForegroundColor Green
Write-Host "Location: http://localhost:8000" -ForegroundColor Cyan

Set-Location "D:\IVth Year Project\TrustLoom-AI\api"
& "C:\Users\acer\AppData\Local\Programs\Python\Python311\python.exe" main.py


cd "D:\IVth Year Project\TrustLoom-AI" ; python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload 