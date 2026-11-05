from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

tables = [
    "student_accounts",
    "students",
    "skills",
    "student_skills",
    "placements",
    "placement_submissions"
]

for table in tables:
    cursor.execute(f"SHOW CREATE TABLE {table}")
    result = cursor.fetchone()
    print(f"\n--- {table} ---")
    print(result[1])

cursor.close()
conn.close()