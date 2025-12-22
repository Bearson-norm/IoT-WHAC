# PowerShell script to sync users from localhost to Docker database

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Sync Users from Localhost to Docker Database" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Export from localhost
Write-Host "`n[1] Exporting users from localhost database..." -ForegroundColor Yellow

$env:PGPASSWORD = "Admin123"
pg_dump -h localhost -U postgres -d whac_master -t web_users --data-only --column-inserts -f web_users_export.sql

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Export successful" -ForegroundColor Green
} else {
    Write-Host "❌ Export failed" -ForegroundColor Red
    exit 1
}

# Import to Docker
Write-Host "`n[2] Importing users to Docker database..." -ForegroundColor Yellow

Get-Content web_users_export.sql | docker exec -i whac-postgres psql -U postgres -d whac_master

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Import successful" -ForegroundColor Green
} else {
    Write-Host "❌ Import failed" -ForegroundColor Red
    exit 1
}

# Verify
Write-Host "`n[3] Verifying data in Docker database..." -ForegroundColor Yellow
docker exec -i whac-postgres psql -U postgres -d whac_master -c "SELECT id, username, full_name, email, role, is_active FROM web_users ORDER BY created_at DESC;"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Done!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan


























