# Start Backend API Server
Write-Host "Starting Backend API Server..." -ForegroundColor Green
Write-Host "Location: http://localhost:8000" -ForegroundColor Cyan

Set-Location "D:\GIDEON\Final_year_project\Project\api"
& "D:/GIDEON/Final_year_project/Project/.venv/Scripts/python.exe" main.py
