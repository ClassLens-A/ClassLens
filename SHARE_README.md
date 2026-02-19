# 📦 Sharing ClassLens Database Package

This folder contains everything needed to restore the ClassLens database on another machine.

## 📋 Files to Share

Share these files with your team:

```
📦 ClassLens_Database_Package/
├── 📄 ClassLens_backup.dump              (Database backup - REQUIRED)
├── 📄 DATABASE_SETUP_INSTRUCTIONS.md     (Detailed setup guide)
├── 📄 restore_database.bat               (Windows restoration script)
├── 📄 restore_database.sh                (Linux/Mac restoration script)
└── 📄 SHARE_README.md                    (This file)
```

## 🚀 Quick Start for Recipients

### **Windows Users:**

1. Install PostgreSQL 17 or 18 from https://www.postgresql.org/download/
2. Extract all files to a folder
3. Double-click `restore_database.bat`
4. Follow the prompts (enter postgres password)
5. Done! Database is restored.

### **Linux/Mac Users:**

1. Install PostgreSQL (see instructions in DATABASE_SETUP_INSTRUCTIONS.md)
2. Extract all files to a folder
3. Make script executable: `chmod +x restore_database.sh`
4. Run: `./restore_database.sh`
5. Follow the prompts (enter postgres password)
6. Done! Database is restored.

### **Manual Restoration:**

If scripts don't work, follow the detailed guide in `DATABASE_SETUP_INSTRUCTIONS.md`

## 📊 Database Information

- **Database Name:** ClassLens
- **PostgreSQL Version:** 17.x or 18.x
- **Encoding:** UTF8
- **Extensions Required:** pgvector (included in dump)
- **Locale:** English_India.1252 (will adapt to system locale)

## 📁 What's Included in the Backup?

✅ **Complete database schema:**
- All tables with proper structure
- All columns with correct data types
- Primary keys, foreign keys, unique constraints
- Check constraints and default values
- Indexes for optimal performance

✅ **All data:**
- Student records
- Teacher information
- Class sessions
- Attendance data
- Grades and assessments
- All related data

✅ **Extensions:**
- pgvector (for AI/ML vector operations)

✅ **Sequences:**
- Auto-increment configurations preserved

## 🔧 System Requirements

### **Minimum:**
- PostgreSQL 17.x or 18.x
- 500 MB free disk space (adjust based on your database size)
- Windows 10/11, Linux, or macOS
- Python 3.8+ (for Django application)

### **Recommended:**
- PostgreSQL 18.x
- 2 GB free disk space
- 4 GB RAM
- SSD for better database performance

## 🐍 Django Application Setup (After Database Restoration)

1. **Install Python dependencies:**
   ```bash
   cd ClassLens_DB
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```env
   DEBUG=True
   SECRET_KEY=django-insecure-change-this
   
   DB_NAME=ClassLens
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_HOST=localhost
   DB_PORT=5432
   
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

3. **Test and run:**
   ```bash
   python manage.py check
   python manage.py runserver
   ```

4. **Access:** http://127.0.0.1:8000/

## 📤 How to Create Package for Sharing

### **Option 1: ZIP Archive**

Compress all files into a single ZIP:
```powershell
# Windows PowerShell
Compress-Archive -Path ClassLens_backup.dump, DATABASE_SETUP_INSTRUCTIONS.md, restore_database.bat, restore_database.sh, SHARE_README.md -DestinationPath ClassLens_Database_Package.zip
```

```bash
# Linux/Mac
zip -r ClassLens_Database_Package.zip ClassLens_backup.dump DATABASE_SETUP_INSTRUCTIONS.md restore_database.bat restore_database.sh SHARE_README.md
```

### **Option 2: Cloud Storage**

Upload to:
- Google Drive
- Dropbox
- OneDrive
- AWS S3
- GitHub (for private repositories only - don't expose sensitive data!)

### **Option 3: Network Share**

Place files on a shared network drive accessible to your team.

## ⚠️ Security Considerations

### **Before Sharing:**

1. **Review sensitive data:**
   - Check if database contains production passwords
   - Remove or anonymize personal information if needed
   - Sanitize email addresses if sharing publicly

2. **Create sanitized version (if needed):**
   ```sql
   -- Connect to database
   psql -U postgres -d ClassLens
   
   -- Anonymize sensitive data (example)
   UPDATE public."Home_student" 
   SET email = 'student' || id || '@example.com',
       phone = NULL;
   
   -- Then create new backup
   pg_dump -U postgres -Fc -f ClassLens_backup_sanitized.dump ClassLens
   ```

3. **Don't include:**
   - Production API keys
   - Real passwords
   - Firebase service account keys
   - AWS credentials

### **For Recipients:**

1. **Change default passwords** after restoration
2. **Use strong passwords** for PostgreSQL
3. **Don't commit `.env` files** to version control
4. **Use environment-specific configurations**

## 🆘 Support & Troubleshooting

### **Common Issues:**

1. **"psql: command not found"**
   - Solution: Add PostgreSQL to system PATH (see instructions)

2. **"Extension vector is not available"**
   - Solution: Install pgvector extension (see DATABASE_SETUP_INSTRUCTIONS.md)

3. **"Password authentication failed"**
   - Solution: Use correct postgres password from installation

4. **"Database already exists"**
   - Solution: Drop existing database or use different name

### **Get Help:**

- Check detailed instructions: `DATABASE_SETUP_INSTRUCTIONS.md`
- PostgreSQL docs: https://www.postgresql.org/docs/
- pgvector: https://github.com/pgvector/pgvector

## ✅ Verification Checklist (For Recipients)

After restoration, verify:

- [ ] PostgreSQL service is running
- [ ] Database `ClassLens` exists
- [ ] Tables are visible (run `\dt` in psql)
- [ ] pgvector extension is enabled (run `\dx` in psql)
- [ ] Sample data is present (check table counts)
- [ ] Django application can connect
- [ ] Application runs without errors

## 📊 Database Statistics

To check database size after restoration:

```sql
-- Total database size
SELECT pg_size_pretty(pg_database_size('ClassLens'));

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 📝 Version History

- **Version:** 1.0
- **Created:** February 2026
- **PostgreSQL Version:** 18.1
- **Backup Format:** Custom (pg_dump -Fc)

---

**Happy coding!** 🚀
