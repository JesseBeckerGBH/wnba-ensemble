$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "   SYNDICATE MANUAL EXECUTION PIPELINE    "
Write-Host "=========================================="

# Export predictions to frontend
Write-Host "1. Exporting predictions..."
cd "$PSScriptRoot\node_wnba_engine"
.\.venv\Scripts\Activate.ps1
python scripts\export_predictions.py

# Send email notifications
Write-Host "2. Triggering email notifications..."
python scripts\send_notifications.py

Write-Host "=========================================="
Write-Host " Pipeline Complete! "
Write-Host "=========================================="
