@echo off
REM ClassLens Database Restoration Script for Windows
REM This script automates the database restoration process

echo ========================================
echo ClassLens Database Restoration Script
echo ========================================
echo.

REM Check if PostgreSQL is in PATH
where psql >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PostgreSQL is not in your PATH!
    echo.
    echo Please add PostgreSQL to your PATH:
    echo 1. Find your PostgreSQL installation: C:\Program Files\PostgreSQL\18\bin
    echo 2. Add it to System Environment Variables
    echo 3. Restart this terminal and run this script again
    echo.
    pause
    exit /b 1
)

echo [OK] PostgreSQL found in PATH
psql --version
echo.

REM Check if dump file exists
if not exist "ClassLens_backup.dump" (
    echo [ERROR] ClassLens_backup.dump file not found!
    echo Please ensure the dump file is in the same directory as this script.
    echo.
    pause
    exit /b 1
)

echo [OK] Backup file found
echo.

REM Get PostgreSQL password
set /p PGPASSWORD="Enter PostgreSQL 'postgres' user password: "
echo.

REM Check if database already exists
echo Checking if ClassLens database exists...
psql -U postgres -lqt 2>nul | findstr /C:"ClassLens" >nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo [WARNING] Database 'ClassLens' already exists!
    set /p CONTINUE="Do you want to drop and recreate it? (yes/no): "
    if /i "%CONTINUE%"=="yes" (
        echo Dropping existing database...
        psql -U postgres -c "DROP DATABASE \"ClassLens\";" 2>nul
        echo [OK] Database dropped
    ) else (
        echo [INFO] Using existing database. Restoration may fail if tables already exist.
    )
)

echo.
echo Creating ClassLens database...
psql -U postgres -c "CREATE DATABASE \"ClassLens\";" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Database created successfully
) else (
    echo [INFO] Database already exists, proceeding with restoration...
)

echo.
echo Restoring database from backup...
echo This may take a few minutes depending on the database size...
echo.

pg_restore -U postgres -d ClassLens -v ClassLens_backup.dump

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [SUCCESS] Database restored successfully!
    echo ========================================
    echo.
    echo Verifying restoration...
    echo.
    
    REM Count tables
    psql -U postgres -d ClassLens -c "\dt"
    
    echo.
    echo ========================================
    echo Next Steps:
    echo ========================================
    echo 1. Set up your Django environment
    echo 2. Create .env file with database credentials
    echo 3. Run: python manage.py check
    echo 4. Run: python manage.py runserver
    echo.
    echo See DATABASE_SETUP_INSTRUCTIONS.md for detailed steps
    echo ========================================
) else (
    echo.
    echo [ERROR] Database restoration failed!
    echo Please check the error messages above.
    echo.
    echo Common issues:
    echo - Wrong password
    echo - pgvector extension not installed
    echo - Insufficient permissions
    echo.
    echo See DATABASE_SETUP_INSTRUCTIONS.md for troubleshooting
)

echo.
pause
