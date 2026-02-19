# 🗄️ ClassLens Database Setup Guide

This guide will help you restore the ClassLens PostgreSQL database on your local machine.

## 📋 Prerequisites

1. **PostgreSQL 17 or 18** installed on your machine
   - Download from: https://www.postgresql.org/download/
   - During installation, remember the password you set for the `postgres` user
   - Keep default port: **5432**

2. **Files needed:**
   - `ClassLens_backup.dump` (the database backup file)

---

## 🚀 Step-by-Step Restoration

### **Step 1: Add PostgreSQL to PATH (Windows)**

1. Find your PostgreSQL installation path:
   - Usually: `C:\Program Files\PostgreSQL\18\bin` or `C:\Program Files\PostgreSQL\17\bin`

2. Add to PATH temporarily (open PowerShell):
   ```powershell
   $env:Path += ";C:\Program Files\PostgreSQL\18\bin"
   ```

   **OR** Add permanently:
   - Right-click **This PC** → **Properties** → **Advanced system settings**
   - Click **Environment Variables**
   - Under **System variables**, find **Path** → Click **Edit**
   - Click **New** → Add: `C:\Program Files\PostgreSQL\18\bin`
   - Click **OK** on all dialogs
   - **Restart your terminal**

### **Step 2: Verify PostgreSQL Installation**

```powershell
# Check PostgreSQL version
psql --version

# Should show: psql (PostgreSQL) 18.x or 17.x
```

### **Step 3: Create the Database**

```powershell
# Connect to PostgreSQL
psql -U postgres

# You'll be prompted for the postgres password you set during installation
```

Inside the PostgreSQL prompt (`postgres=#`), run:

```sql
-- Create the database
CREATE DATABASE "ClassLens";

-- Exit
\q
```

### **Step 4: Restore the Database**

```powershell
# Navigate to the folder containing ClassLens_backup.dump
cd "C:\path\to\backup\folder"

# Restore the database
pg_restore -U postgres -d ClassLens -v ClassLens_backup.dump
```

**Enter your postgres password when prompted.**

### **Step 5: Verify the Restoration**

```powershell
# Connect to the database
psql -U postgres -d ClassLens

# Inside psql, check tables
\dt

# Check extensions (should show 'vector')
\dx

# Check sample data (example)
SELECT COUNT(*) FROM public."Home_student";

# Exit
\q
```

---

## 🔍 What's Included in the Backup?

- ✅ All database tables with proper structure
- ✅ All constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK)
- ✅ All indexes for performance
- ✅ All data (students, teachers, sessions, etc.)
- ✅ pgvector extension (for AI/ML vector operations)
- ✅ Sequences and auto-increment configurations

---

## 🐍 Django Application Setup

After restoring the database, set up the Django application:

### **1. Install Python Dependencies**

```powershell
cd ClassLens_DB

# Install required packages
pip install -r requirements.txt

# Or install manually:
pip install Django psycopg2-binary python-dotenv djangorestframework pillow
```

### **2. Create `.env` File**

Create a `.env` file in the `ClassLens_DB` folder:

```env
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production

DB_NAME=ClassLens
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
DB_HOST=localhost
DB_PORT=5432

ALLOWED_HOSTS=localhost,127.0.0.1
```

### **3. Test Django Connection**

```powershell
# Check for errors
python manage.py check

# Run the development server
python manage.py runserver
```

Visit: **http://127.0.0.1:8000/**

---

## ⚠️ Troubleshooting

### **Error: `pg_restore: error: could not execute query: ERROR: extension "vector" is not available`**

**Solution:** Install pgvector extension

1. **Check if vector extension exists:**
   ```powershell
   psql -U postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
   ```

2. **If not available, install from:**
   - https://github.com/pgvector/pgvector/releases
   - Download the Windows version matching your PostgreSQL version
   - Extract and copy files to PostgreSQL directories

### **Error: `psql: command not found` or `pg_restore: command not found`**

**Solution:** PostgreSQL is not in your PATH. Repeat Step 1 above.

### **Error: Password authentication failed**

**Solution:** 
- Make sure you're using the correct postgres password
- Try resetting: Open pgAdmin → Right-click postgres user → Properties → Set new password

### **Database connection issues in Django**

**Solution:**
- Verify database exists: `psql -U postgres -l`
- Check `.env` file credentials match your PostgreSQL setup
- Ensure PostgreSQL service is running

---

## 📊 Database Statistics

To view database size and table counts:

```powershell
psql -U postgres -d ClassLens -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 🔐 Security Notes

- **Change the SECRET_KEY** in production
- **Never commit `.env` file** to version control
- Use **strong passwords** for database users
- For production, create a dedicated database user (not postgres)

---

## 📞 Need Help?

If you encounter issues:
1. Check PostgreSQL service is running
2. Verify PostgreSQL version compatibility (17.x or 18.x)
3. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\18\data\log\`
4. Ensure all prerequisites are installed

---

## ✅ Success Checklist

- [ ] PostgreSQL installed and accessible via command line
- [ ] Database `ClassLens` created successfully
- [ ] Dump file restored without errors
- [ ] Tables are visible (`\dt` shows tables)
- [ ] pgvector extension enabled (`\dx` shows vector)
- [ ] Django can connect to database
- [ ] Application runs on http://127.0.0.1:8000/

---

**Database restored successfully!** 🎉
