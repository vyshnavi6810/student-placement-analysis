
import os
import sys
import mysql.connector
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "16211")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        ssl_ca=str(BASE_DIR / "ca.pem"),
        ssl_verify_cert=True
    )


def run_sql_file():
    sql_file = BASE_DIR / "database.sql"

    if not sql_file.exists():
        print("database.sql file not found!")
        return

    print("WARNING: This setup will delete the existing project tables and records.")
    confirm = input("Type RESET to continue: ")

    if confirm != "RESET":
        print("Setup cancelled.")
        return

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql_script = sql_file.read_text(encoding="utf-8")

        statements = [
            statement.strip()
            for statement in sql_script.split(";")
            if statement.strip()
        ]

        for statement in statements:
            cursor.execute(statement)

            if cursor.with_rows:
                for row in cursor.fetchall():
                    print(row)

        conn.commit()
        print("\nDatabase setup completed successfully!")

    except Exception as error:
        print("Database setup failed:", error)
        if conn:
            conn.rollback()

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        run_sql_file()
    else:
        try:
            conn = get_connection()
            print("MySQL connection successful!")
            print("Connected database:", conn.database)
            conn.close()
        except mysql.connector.Error as error:
            print("Database connection failed:", error)
