from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT TABLE_NAME, COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND COLUMN_NAME IN (
          'university_id', 'user_id', 'admin_remarks'
      )
    ORDER BY TABLE_NAME, COLUMN_NAME
""")

print("EXISTING COLUMNS:")
for row in cursor.fetchall():
    print(row)

cursor.execute("""
    SELECT TABLE_NAME, CONSTRAINT_NAME
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND CONSTRAINT_TYPE = 'FOREIGN KEY'
    ORDER BY TABLE_NAME
""")

print("\nEXISTING FOREIGN KEYS:")
for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()