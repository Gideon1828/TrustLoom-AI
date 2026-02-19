# Start Frontend Dev Server
Write-Host "Starting Frontend Dev Server..." -ForegroundColor Green
Write-Host "Location: http://localhost:3000" -ForegroundColor Cyan

Set-Location "D:\GIDEON\Final_year_project\Project\frontend"
$env:BROWSER = 'none'
npm start
