
import os
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

if __name__ == "__main__":
    try:
        conn = get_connection()
        print("MySQL connection successful!")
        conn.close()
    except mysql.connector.Error as error:
        print("Database connection failed:", error)
