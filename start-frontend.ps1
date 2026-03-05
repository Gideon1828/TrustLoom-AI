# Start Frontend Dev Server
Write-Host "Starting Frontend Dev Server..." -ForegroundColor Green
Write-Host "Location: http://localhost:3000" -ForegroundColor Cyan

Set-Location "D:\IVth Year Project\TrustLoom-AI\frontend"
$env:BROWSER = 'none'
npm run dev
