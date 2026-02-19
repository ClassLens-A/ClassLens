@echo off
echo Installing pgvector to PostgreSQL 18...
echo.

REM Initialize Visual Studio environment
call "C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvarsall.bat" x64

REM Set PostgreSQL root
set "PGROOT=C:\Program Files\PostgreSQL\18"

REM Navigate to pgvector directory
cd C:\Users\Pc\AppData\Local\Temp\pgvector

REM Install pgvector
nmake /F Makefile.win install

echo.
echo Installation complete!
echo Now you can run: CREATE EXTENSION vector; in your ClassLens database
pause
