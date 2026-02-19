@echo off
echo ==========================================
echo ClassLens Database Verification
echo ==========================================
echo.

cd C:\Dhriti\ClassLens
set "PSQL=C:\Program Files\PostgreSQL\18\bin\psql.exe"

echo [1/5] Checking vector extension installation...
"%PSQL%" -U postgres -d ClassLens -c "\dx vector"
echo.

echo [2/5] Listing all tables...
"%PSQL%" -U postgres -d ClassLens -c "\dt"
echo.

echo [3/5] Checking Home_student table structure (with face_embedding vector column)...
"%PSQL%" -U postgres -d ClassLens -c "\d \"Home_student\""
echo.

echo [4/5] Counting records in main tables...
"%PSQL%" -U postgres -d ClassLens -c "SELECT 'Students' as table_name, COUNT(*) as count FROM \"Home_student\" UNION ALL SELECT 'Teachers', COUNT(*) FROM \"Home_teacher\" UNION ALL SELECT 'Departments', COUNT(*) FROM \"Home_department\" UNION ALL SELECT 'Subjects', COUNT(*) FROM \"Home_subject\" UNION ALL SELECT 'Class Sessions', COUNT(*) FROM \"Home_classsession\";"
echo.

echo [5/5] Testing a simple query on Home_student...
"%PSQL%" -U postgres -d ClassLens -c "SELECT id, name, email, year FROM \"Home_student\" LIMIT 3;"
echo.

echo ==========================================
echo Verification Complete!
echo ==========================================
echo.
echo If you see:
echo  - vector extension installed
echo  - Home_student table with face_embedding column (vector type)
echo  - Record counts showing data
echo.
echo Then your database is working correctly!
echo ==========================================
pause
