# SafeRoute AI Backup Creator (PowerShell)
# Excludes: node_modules, virtual environments, build folders, caches, .git, and existing backups

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = Resolve-Path -Path $scriptDir
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupName = "saferoute-ai-backup-$timestamp.tar.gz"
$backupPath = Join-Path $projectRoot $backupName

Write-Host "Creating SafeRoute AI backup..." -ForegroundColor Green
Write-Host "Project root: $projectRoot"
Write-Host "Backup name: $backupName"
Write-Host ""

# Define exclusions
$exclusions = @(
    "--exclude=node_modules",
    "--exclude=venv",
    "--exclude=.venv",
    "--exclude=__pycache__",
    "--exclude=*.pyc",
    "--exclude=*.pyo",
    "--exclude=*.pyd",
    "--exclude=.next",
    "--exclude=.cache",
    "--exclude=dist",
    "--exclude=build",
    "--exclude=.git",
    "--exclude=saferoute-ai-backup-*.tar.gz"
)

# Build tar command
$tarArgs = @(
    "-czf","`"$backupPath`""
) + $exclusions + @(
    "-C","`"$projectRoot`"","."
)

# Execute tar (requires tar.exe - available in Git Bash or WSL, or install via Chocolatey: choco install tar)
try {
    & tar @tarArgs
    if (Test-Path $backupPath) {
        $size = Get-Item $backupPath | Select-Object -Expand Property Length
        $sizeMB = [math]::Round($size / 1MB, 2)
        Write-Host ""
        Write-Host "✅ Backup created successfully!" -ForegroundColor Green
        Write-Host "📁 Location: $backupPath"
        Write-Host "📦 Size: $sizeMB MB"
        Write-Host ""
        Write-Host "To restore:" -ForegroundColor Yellow
        Write-Host "  1. Extract: tar -xzf $backupName" -ForegroundColor Yellow
        Write-Host "  2. cd saferoute-ai" -ForegroundColor Yellow
        Write-Host "  3. Backend: cd backend && python -m venv venv & .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt" -ForegroundColor Yellow
        Write-Host "  4. Frontend: cd frontend && npm install" -ForegroundColor Yellow
        Write-Host "  5. Set MAPBOX_TOKEN in frontend\.env.local (get free token at https://account.mapbox.com/access-tokens/)" -ForegroundColor Yellow
        Write-Host "  6. Start: docker-compose up --build  OR  (backend: uvicorn app.main:app --reload, frontend: npm run dev)" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Backup creation failed! File not found." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Backup creation failed! Error: $_" -ForegroundColor Red
    Write-Host "Note: This script requires tar.exe. Install via:" -ForegroundColor Yellow
    Write-Host "  Chocolatey: choco install tar" -ForegroundColor Yellow
    Write-Host "  Or use Git Bash / WSL / Windows Subsystem for Linux" -ForegroundColor Yellow
    exit 1
}