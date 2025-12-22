# =====================================================
# Script untuk Menjalankan Database Fixes
# =====================================================
# Script ini akan:
# 1. Backup database terlebih dahulu
# 2. Menjalankan fix_database_foreign_keys.sql
# 3. Menjalankan remove_username_redundancy.sql
# =====================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Database Fix Script - WHAC Master Database" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Konfigurasi
$CONTAINER_NAME = "whac-postgres"
$DB_NAME = "whac_master"
$DB_USER = "postgres"
$DB_PASSWORD = "Admin123"
$BACKUP_DIR = ".\backups"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_FILE = "$BACKUP_DIR\backup_before_fixes_$TIMESTAMP.sql"

# Script files
$SCRIPT_FK = ".\fix_database_foreign_keys.sql"
$SCRIPT_USERNAME = ".\remove_username_redundancy.sql"

# =====================================================
# Step 1: Cek Container
# =====================================================
Write-Host "[1/5] Checking Docker container..." -ForegroundColor Yellow
$container = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
if (-not $container) {
    Write-Host "[ERROR] Container $CONTAINER_NAME is not running!" -ForegroundColor Red
    Write-Host "   Please start it with: docker-compose up -d postgres" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Container found: $container" -ForegroundColor Green
Write-Host ""

# =====================================================
# Step 2: Test Connection
# =====================================================
Write-Host "[2/5] Testing database connection..." -ForegroundColor Yellow
try {
    $result = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT current_database(), current_user;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database connection successful" -ForegroundColor Green
        Write-Host "   $result" -ForegroundColor Gray
    } else {
        Write-Host "[ERROR] Cannot connect to database" -ForegroundColor Red
        Write-Host "   $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Connection test failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =====================================================
# Step 3: Backup Database
# =====================================================
Write-Host "[3/5] Creating database backup..." -ForegroundColor Yellow

# Create backup directory if not exists
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR | Out-Null
    Write-Host "   Created backup directory: $BACKUP_DIR" -ForegroundColor Gray
}

try {
    Write-Host "   Backup file: $BACKUP_FILE" -ForegroundColor Gray
    docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $backupSize = (Get-Item $BACKUP_FILE).Length / 1KB
        Write-Host "[OK] Backup created successfully" -ForegroundColor Green
        Write-Host "   Size: $([math]::Round($backupSize, 2)) KB" -ForegroundColor Gray
        Write-Host "   Location: $BACKUP_FILE" -ForegroundColor Gray
    } else {
        Write-Host "[ERROR] Backup failed!" -ForegroundColor Red
        Write-Host "   Please check the error above" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERROR] Backup failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =====================================================
# Step 4: Run Foreign Keys Fix
# =====================================================
Write-Host "[4/5] Running Foreign Keys Fix..." -ForegroundColor Yellow

if (-not (Test-Path $SCRIPT_FK)) {
    Write-Host "[ERROR] Script not found: $SCRIPT_FK" -ForegroundColor Red
    Write-Host "   Please make sure you're running this from web_ui directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "   Script: $SCRIPT_FK" -ForegroundColor Gray
Write-Host "   This will:" -ForegroundColor Gray
Write-Host "   - Clean invalid user_id data" -ForegroundColor Gray
Write-Host "   - Add Foreign Key constraints to log_data, log_action, attendance" -ForegroundColor Gray
Write-Host ""

# Ask for confirmation
$confirmation = Read-Host "   Continue? (Y/N)"
if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
    Write-Host "[CANCELLED] Operation cancelled by user" -ForegroundColor Yellow
    exit 0
}

try {
    Write-Host "   Executing script..." -ForegroundColor Gray
    Get-Content $SCRIPT_FK | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME 2>&1 | Tee-Object -Variable output
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Foreign Keys Fix completed successfully" -ForegroundColor Green
        
        # Check if constraints were created
        $constraintCheck = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY' AND table_name IN ('log_data', 'log_action', 'attendance');" 2>&1
        if ($constraintCheck -match '\d+') {
            Write-Host "   Foreign Key constraints created: $constraintCheck" -ForegroundColor Gray
        }
    } else {
        Write-Host "[ERROR] Foreign Keys Fix failed!" -ForegroundColor Red
        Write-Host "   Check the output above for details" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   If you want to restore from backup:" -ForegroundColor Yellow
        Write-Host "   docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < $BACKUP_FILE" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "[ERROR] Error executing script: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =====================================================
# Step 5: Run Username Redundancy Fix
# =====================================================
Write-Host "[5/5] Running Username Redundancy Fix..." -ForegroundColor Yellow

if (-not (Test-Path $SCRIPT_USERNAME)) {
    Write-Host "[ERROR] Script not found: $SCRIPT_USERNAME" -ForegroundColor Red
    Write-Host "   Please make sure you're running this from web_ui directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "   Script: $SCRIPT_USERNAME" -ForegroundColor Gray
Write-Host "   This will:" -ForegroundColor Gray
Write-Host "   - Remove username column from log_action and attendance" -ForegroundColor Gray
Write-Host "   - Recreate views to use JOIN to store_001" -ForegroundColor Gray
Write-Host ""
Write-Host "   ⚠️  WARNING: This will modify table structure!" -ForegroundColor Yellow
Write-Host "   ⚠️  Make sure application code is updated to use JOIN!" -ForegroundColor Yellow
Write-Host ""

# Ask for confirmation
$confirmation = Read-Host "   Continue? (Y/N)"
if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
    Write-Host "[CANCELLED] Operation cancelled by user" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Note: Foreign Keys Fix has been applied" -ForegroundColor Gray
    Write-Host "   Username Redundancy Fix was skipped" -ForegroundColor Gray
    exit 0
}

try {
    Write-Host "   Executing script..." -ForegroundColor Gray
    Get-Content $SCRIPT_USERNAME | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME 2>&1 | Tee-Object -Variable output
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Username Redundancy Fix completed successfully" -ForegroundColor Green
        
        # Verify columns were removed
        $columnCheck = docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name IN ('log_action', 'attendance') AND column_name = 'username';" 2>&1
        if ($columnCheck -match '0') {
            Write-Host "   Username columns removed successfully" -ForegroundColor Gray
        }
    } else {
        Write-Host "[ERROR] Username Redundancy Fix failed!" -ForegroundColor Red
        Write-Host "   Check the output above for details" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   If you want to restore from backup:" -ForegroundColor Yellow
        Write-Host "   docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < $BACKUP_FILE" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "[ERROR] Error executing script: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# =====================================================
# Summary
# =====================================================
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ All Database Fixes Completed Successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Backup created: $BACKUP_FILE" -ForegroundColor Green
Write-Host "  ✓ Foreign Keys constraints added" -ForegroundColor Green
Write-Host "  ✓ Username redundancy removed" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart Web UI: docker-compose restart" -ForegroundColor Gray
Write-Host "  2. Test the application to ensure everything works" -ForegroundColor Gray
Write-Host "  3. Update application code if needed (see remove_username_redundancy.sql notes)" -ForegroundColor Gray
Write-Host ""
Write-Host "If you need to restore from backup:" -ForegroundColor Yellow
Write-Host "  docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < $BACKUP_FILE" -ForegroundColor Gray
Write-Host ""












