#!/bin/bash

# ClassLens Database Restoration Script for Linux/Mac
# This script automates the database restoration process

echo "========================================"
echo "ClassLens Database Restoration Script"
echo "========================================"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "[ERROR] PostgreSQL is not installed or not in PATH!"
    echo ""
    echo "Please install PostgreSQL:"
    echo "  - Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  - MacOS: brew install postgresql"
    echo "  - CentOS/RHEL: sudo yum install postgresql-server"
    echo ""
    exit 1
fi

echo "[OK] PostgreSQL found"
psql --version
echo ""

# Check if dump file exists
if [ ! -f "ClassLens_backup.dump" ]; then
    echo "[ERROR] ClassLens_backup.dump file not found!"
    echo "Please ensure the dump file is in the same directory as this script."
    echo ""
    exit 1
fi

echo "[OK] Backup file found"
echo ""

# Get PostgreSQL password
read -sp "Enter PostgreSQL 'postgres' user password: " PGPASSWORD
export PGPASSWORD
echo ""
echo ""

# Check if database already exists
if psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw ClassLens; then
    echo ""
    echo "[WARNING] Database 'ClassLens' already exists!"
    read -p "Do you want to drop and recreate it? (yes/no): " CONTINUE
    if [ "$CONTINUE" = "yes" ]; then
        echo "Dropping existing database..."
        psql -U postgres -c "DROP DATABASE \"ClassLens\";" 2>/dev/null
        echo "[OK] Database dropped"
    else
        echo "[INFO] Using existing database. Restoration may fail if tables already exist."
    fi
fi

echo ""
echo "Creating ClassLens database..."
psql -U postgres -c "CREATE DATABASE \"ClassLens\";" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] Database created successfully"
else
    echo "[INFO] Database already exists, proceeding with restoration..."
fi

echo ""
echo "Restoring database from backup..."
echo "This may take a few minutes depending on the database size..."
echo ""

pg_restore -U postgres -d ClassLens -v ClassLens_backup.dump

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "[SUCCESS] Database restored successfully!"
    echo "========================================"
    echo ""
    echo "Verifying restoration..."
    echo ""
    
    # Count tables
    psql -U postgres -d ClassLens -c "\dt"
    
    echo ""
    echo "========================================"
    echo "Next Steps:"
    echo "========================================"
    echo "1. Set up your Django environment"
    echo "2. Create .env file with database credentials"
    echo "3. Run: python manage.py check"
    echo "4. Run: python manage.py runserver"
    echo ""
    echo "See DATABASE_SETUP_INSTRUCTIONS.md for detailed steps"
    echo "========================================"
else
    echo ""
    echo "[ERROR] Database restoration failed!"
    echo "Please check the error messages above."
    echo ""
    echo "Common issues:"
    echo "- Wrong password"
    echo "- pgvector extension not installed"
    echo "- Insufficient permissions"
    echo ""
    echo "See DATABASE_SETUP_INSTRUCTIONS.md for troubleshooting"
fi

echo ""
unset PGPASSWORD
