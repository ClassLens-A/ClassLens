@echo off
REM Script to create a shareable database package
REM This bundles all necessary files for database sharing

echo ========================================
echo ClassLens Database Package Creator
echo ========================================
echo.

REM Check if backup file exists
if not exist "ClassLens_backup.dump" (
    echo [ERROR] ClassLens_backup.dump not found!
    echo.
    echo Please ensure the backup file exists in this directory.
    echo You can create one using:
    echo   pg_dump -U postgres -Fc -f ClassLens_backup.dump ClassLens
    echo.
    pause
    exit /b 1
)

echo [OK] Backup file found
echo.

REM Check required files
set MISSING=0

if not exist "DATABASE_SETUP_INSTRUCTIONS.md" (
    echo [WARNING] DATABASE_SETUP_INSTRUCTIONS.md not found
    set MISSING=1
)

if not exist "restore_database.bat" (
    echo [WARNING] restore_database.bat not found
    set MISSING=1
)

if not exist "restore_database.sh" (
    echo [WARNING] restore_database.sh not found
    set MISSING=1
)

if not exist "SHARE_README.md" (
    echo [WARNING] SHARE_README.md not found
    set MISSING=1
)

if not exist "DATABASE_QUICK_REFERENCE.md" (
    echo [WARNING] DATABASE_QUICK_REFERENCE.md not found
    set MISSING=1
)

if %MISSING%==1 (
    echo.
    echo Some documentation files are missing.
    echo The package will be created with available files only.
    echo.
    pause
)

REM Get backup file size
for %%A in ("ClassLens_backup.dump") do set FILESIZE=%%~zA
set /a FILESIZE_MB=%FILESIZE% / 1048576

echo Database backup size: %FILESIZE_MB% MB
echo.

REM Create package directory
set PACKAGE_DIR=ClassLens_Database_Package_%date:~-4,4%%date:~-10,2%%date:~-7,2%
set PACKAGE_DIR=%PACKAGE_DIR: =0%

if exist "%PACKAGE_DIR%" (
    echo [INFO] Package directory already exists. It will be replaced.
    rmdir /s /q "%PACKAGE_DIR%"
)

echo Creating package directory: %PACKAGE_DIR%
mkdir "%PACKAGE_DIR%"

REM Copy files
echo.
echo Copying files...

copy "ClassLens_backup.dump" "%PACKAGE_DIR%\" >nul
echo [OK] Copied: ClassLens_backup.dump

if exist "DATABASE_SETUP_INSTRUCTIONS.md" (
    copy "DATABASE_SETUP_INSTRUCTIONS.md" "%PACKAGE_DIR%\" >nul
    echo [OK] Copied: DATABASE_SETUP_INSTRUCTIONS.md
)

if exist "restore_database.bat" (
    copy "restore_database.bat" "%PACKAGE_DIR%\" >nul
    echo [OK] Copied: restore_database.bat
)

if exist "restore_database.sh" (
    copy "restore_database.sh" "%PACKAGE_DIR%\" >nul
    echo [OK] Copied: restore_database.sh
)

if exist "SHARE_README.md" (
    copy "SHARE_README.md" "%PACKAGE_DIR%\" >nul
    echo [OK] Copied: SHARE_README.md
)

if exist "DATABASE_QUICK_REFERENCE.md" (
    copy "DATABASE_QUICK_REFERENCE.md" "%PACKAGE_DIR%\" >nul
    echo [OK] Copied: DATABASE_QUICK_REFERENCE.md
)

REM Copy Django app files (optional)
if exist "ClassLens_DB" (
    echo.
    set /p INCLUDE_APP="Include Django application files? (yes/no): "
    if /i "%INCLUDE_APP%"=="yes" (
        echo Copying Django application...
        xcopy "ClassLens_DB" "%PACKAGE_DIR%\ClassLens_DB\" /E /I /Q >nul
        echo [OK] Copied: ClassLens_DB directory
        
        REM Create .env template
        echo Creating .env template...
        (
            echo # Environment Configuration Template
            echo # Copy this to .env and fill in your values
            echo.
            echo DEBUG=True
            echo SECRET_KEY=django-insecure-CHANGE-THIS-KEY
            echo.
            echo # Database Configuration
            echo DB_NAME=ClassLens
            echo DB_USER=postgres
            echo DB_PASSWORD=your_postgres_password_here
            echo DB_HOST=localhost
            echo DB_PORT=5432
            echo.
            echo ALLOWED_HOSTS=localhost,127.0.0.1
        ) > "%PACKAGE_DIR%\ClassLens_DB\.env.template"
        echo [OK] Created: .env.template
    )
)

echo.
echo Creating compressed archive...
echo.

REM Check if PowerShell is available for compression
where powershell >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    powershell -command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%PACKAGE_DIR%.zip' -Force"
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Package created: %PACKAGE_DIR%.zip
        
        REM Get ZIP size
        for %%A in ("%PACKAGE_DIR%.zip") do set ZIPSIZE=%%~zA
        set /a ZIPSIZE_MB=%ZIPSIZE% / 1048576
        
        echo.
        echo ========================================
        echo Package Information:
        echo ========================================
        echo Package name: %PACKAGE_DIR%.zip
        echo Package size: %ZIPSIZE_MB% MB
        echo Location: %CD%\%PACKAGE_DIR%.zip
        echo ========================================
        echo.
        echo Package contents:
        dir /b "%PACKAGE_DIR%"
        echo.
        echo ========================================
        echo [SUCCESS] Package ready for sharing!
        echo ========================================
        echo.
        echo Next steps:
        echo 1. Upload to cloud storage (Google Drive, Dropbox, etc.)
        echo 2. Share with your team
        echo 3. Recipients should extract and follow instructions
        echo.
        echo See SHARE_README.md for sharing instructions
        echo ========================================
    ) else (
        echo [ERROR] Failed to create ZIP archive
        echo Manual compression required: Compress the folder '%PACKAGE_DIR%'
    )
) else (
    echo [INFO] PowerShell compression not available
    echo.
    echo Package folder created: %PACKAGE_DIR%
    echo Please manually compress this folder using:
    echo - Right-click ^> Send to ^> Compressed (zipped) folder
    echo - Or use 7-Zip, WinRAR, etc.
)

echo.
pause
