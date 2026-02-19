# 🎯 ClassLens Database Quick Reference

Quick commands for common database operations.

---

## 🚀 Initial Setup (One-time)

### **Windows:**
```powershell
# Add PostgreSQL to PATH (restart terminal after)
$env:Path += ";C:\Program Files\PostgreSQL\18\bin"

# Create database
psql -U postgres -c "CREATE DATABASE \"ClassLens\";"

# Restore backup
pg_restore -U postgres -d ClassLens -v ClassLens_backup.dump
```

### **Linux/Mac:**
```bash
# Create database
psql -U postgres -c "CREATE DATABASE \"ClassLens\";"

# Restore backup
pg_restore -U postgres -d ClassLens -v ClassLens_backup.dump
```

---

## 📋 Database Information

### **List all databases:**
```bash
psql -U postgres -l
```

### **Connect to ClassLens database:**
```bash
psql -U postgres -d ClassLens
```

### **Inside psql:**
```sql
-- List all tables
\dt

-- List all extensions
\dx

-- Describe a specific table
\d "Home_student"

-- Show table with column details
\d+ "Home_student"

-- List all schemas
\dn

-- Show database size
\l+

-- Quit
\q
```

---

## 📊 Common Queries

### **Count records in tables:**
```sql
-- Count students
SELECT COUNT(*) FROM public."Home_student";

-- Count teachers
SELECT COUNT(*) FROM public."Home_teacher";

-- Count all tables
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

### **Database size:**
```sql
-- Total database size
SELECT pg_size_pretty(pg_database_size('ClassLens'));

-- Size by table
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size('public.' || tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.' || tablename) DESC;
```

### **Check tables:**
```sql
-- List all table names
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Table info with row counts
SELECT 
    relname as table_name,
    n_live_tup as row_count,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

---

## 🔄 Backup & Restore

### **Create new backup:**
```bash
# Full backup (custom format - recommended)
pg_dump -U postgres -Fc -f ClassLens_backup_$(date +%Y%m%d).dump ClassLens

# SQL format backup
pg_dump -U postgres -f ClassLens_backup_$(date +%Y%m%d).sql ClassLens

# Backup specific tables
pg_dump -U postgres -Fc -t "Home_student" -t "Home_teacher" -f partial_backup.dump ClassLens
```

### **Restore from backup:**
```bash
# From custom format
pg_restore -U postgres -d ClassLens -v -c ClassLens_backup.dump

# From SQL format
psql -U postgres -d ClassLens -f ClassLens_backup.sql

# Restore specific table
pg_restore -U postgres -d ClassLens -t "Home_student" ClassLens_backup.dump
```

---

## 🔐 User Management

### **Create new database user:**
```sql
-- Create user
CREATE USER classlens_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE "ClassLens" TO classlens_user;

-- Grant schema privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO classlens_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO classlens_user;

-- For future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO classlens_user;
```

### **List users:**
```sql
\du
```

---

## 🧹 Maintenance

### **Vacuum database (cleanup):**
```sql
VACUUM ANALYZE;
```

### **Reindex database:**
```sql
REINDEX DATABASE "ClassLens";
```

### **Check database connections:**
```sql
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity
WHERE datname = 'ClassLens';
```

### **Kill idle connections:**
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'ClassLens' 
  AND state = 'idle' 
  AND query_start < now() - interval '1 hour';
```

---

## 🔍 Troubleshooting

### **Check PostgreSQL service status:**
```powershell
# Windows
Get-Service postgresql*

# Linux
sudo systemctl status postgresql
```

### **Start/Stop PostgreSQL:**
```powershell
# Windows (PowerShell as Admin)
Start-Service postgresql-x64-18
Stop-Service postgresql-x64-18
Restart-Service postgresql-x64-18

# Linux
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql
```

### **Find PostgreSQL port:**
```sql
SHOW port;
```

### **Check if extension is available:**
```sql
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

### **Enable extension:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### **View PostgreSQL logs:**
```powershell
# Windows
Get-Content "C:\Program Files\PostgreSQL\18\data\log\*.log" -Tail 50

# Linux
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

## 🐍 Django Commands

### **Setup:**
```bash
cd ClassLens_DB

# Install dependencies
pip install -r requirements.txt

# Check configuration
python manage.py check

# Run migrations (if needed)
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8080
```

### **Database shell:**
```bash
# Django database shell
python manage.py dbshell

# Django shell (with ORM)
python manage.py shell
```

### **In Django shell:**
```python
from Home.models import Student, Teacher

# Count records
Student.objects.count()
Teacher.objects.count()

# Get all students
students = Student.objects.all()

# Filter students
active_students = Student.objects.filter(is_active=True)
```

---

## 📦 Export Data

### **Export to CSV:**
```sql
-- Export table to CSV
\copy (SELECT * FROM public."Home_student") TO 'students.csv' WITH CSV HEADER;

-- Export query results
\copy (SELECT id, username, email FROM public."Home_student" WHERE is_active = true) TO 'active_students.csv' WITH CSV HEADER;
```

### **Import from CSV:**
```sql
-- Import CSV to table
\copy public."Home_student" FROM 'students.csv' WITH CSV HEADER;
```

---

## 🔧 Performance

### **Analyze query performance:**
```sql
EXPLAIN ANALYZE SELECT * FROM public."Home_student" WHERE email = 'test@example.com';
```

### **List slow queries:**
```sql
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

### **Create index:**
```sql
CREATE INDEX idx_student_email ON public."Home_student"(email);
```

---

## 🚨 Emergency Commands

### **Drop database (CAREFUL!):**
```sql
-- First, disconnect all users
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'ClassLens';

-- Then drop
DROP DATABASE "ClassLens";
```

### **Reset database:**
```bash
# Drop and recreate
psql -U postgres -c "DROP DATABASE \"ClassLens\";"
psql -U postgres -c "CREATE DATABASE \"ClassLens\";"
pg_restore -U postgres -d ClassLens ClassLens_backup.dump
```

---

## 📞 Help Resources

- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Django Docs:** https://docs.djangoproject.com/
- **pgvector:** https://github.com/pgvector/pgvector
- **psql commands:** Type `\?` in psql prompt

---

**Keep this file handy for quick reference!** 📌
