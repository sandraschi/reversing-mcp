# Start Reversing MCP WebApp
# This script starts both the FastAPI backend and Next.js frontend

Write-Host "🚀 Starting Reversing MCP WebApp" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan

# Check if Python is available
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check if Node.js is available
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

# Function to start backend
function Start-Backend {
    Write-Host "📡 Starting FastAPI Backend..." -ForegroundColor Yellow

    # Change to webapp directory
    Push-Location "reversing-webapp\api"

    try {
        # Install dependencies if needed
        if (!(Test-Path "venv")) {
            Write-Host "📦 Creating virtual environment..." -ForegroundColor Blue
            python -m venv venv
        }

        # Activate venv and install requirements
        & ".\venv\Scripts\Activate.ps1"
        pip install -r requirements.txt

        # Start the backend
        Write-Host "🔧 Starting API server on http://localhost:11112" -ForegroundColor Green
        Start-Job -ScriptBlock {
            param($path)
            Push-Location $path
            & ".\venv\Scripts\Activate.ps1"
            python main.py
        } -ArgumentList (Get-Location) -Name "ReversingAPI"

    } catch {
        Write-Host "❌ Failed to start backend: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        Pop-Location
    }
}

# Function to start frontend
function Start-Frontend {
    Write-Host "🌐 Starting Next.js Frontend..." -ForegroundColor Yellow

    Push-Location "reversing-webapp"

    try {
        # Install dependencies if needed
        if (!(Test-Path "node_modules")) {
            Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Blue
            npm install
        }

        # Start the frontend
        Write-Host "⚛️  Starting Next.js dev server on http://localhost:11111" -ForegroundColor Green
        Start-Job -ScriptBlock {
            param($path)
            Push-Location $path
            npm run dev
        } -ArgumentList (Get-Location) -Name "ReversingFrontend"

    } catch {
        Write-Host "❌ Failed to start frontend: $($_.Exception.Message)" -ForegroundColor Red
    } finally {
        Pop-Location
    }
}

# Start both services
Start-Backend
Start-Frontend

# Wait a moment for services to start
Start-Sleep -Seconds 3

# Check if services are running
Write-Host "`n📋 Service Status:" -ForegroundColor Cyan
$backendJob = Get-Job -Name "ReversingAPI" -ErrorAction SilentlyContinue
$frontendJob = Get-Job -Name "ReversingFrontend" -ErrorAction SilentlyContinue

if ($backendJob -and $backendJob.State -eq "Running") {
    Write-Host "✅ Backend API: Running (PID: $($backendJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Backend API: Failed to start" -ForegroundColor Red
}

if ($frontendJob -and $frontendJob.State -eq "Running") {
    Write-Host "✅ Frontend: Running (PID: $($frontendJob.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend: Failed to start" -ForegroundColor Red
}

Write-Host "`n🎯 Access the webapp at:" -ForegroundColor Green
Write-Host "   Frontend: http://localhost:11111" -ForegroundColor White
Write-Host "   Backend API: http://localhost:11112" -ForegroundColor White
Write-Host "   API Docs: http://localhost:11112/docs" -ForegroundColor White

Write-Host "`n💡 To stop services, run: Get-Job | Stop-Job" -ForegroundColor Yellow
Write-Host "💡 To check status: Get-Job" -ForegroundColor Yellow

# Keep the script running to show status
Write-Host "`n🔄 Services are starting up... Press Ctrl+C to exit" -ForegroundColor Cyan
try {
    while ($true) {
        Start-Sleep -Seconds 10
        $runningJobs = Get-Job | Where-Object { $_.State -eq "Running" }
        if ($runningJobs.Count -eq 0) {
            Write-Host "❌ All services have stopped" -ForegroundColor Red
            break
        }
    }
} finally {
    # Cleanup on exit
    Get-Job | Stop-Job -ErrorAction SilentlyContinue
    Get-Job | Remove-Job -ErrorAction SilentlyContinue
    Write-Host "`n👋 Services stopped. Goodbye!" -ForegroundColor Cyan
}