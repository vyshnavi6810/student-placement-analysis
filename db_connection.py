
import os
import mysql.connector
from dotenv import load_dotenv

from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("db_host"),
        user=os.getenv("username"),
        password=os.getenv("my_password"),
        database=os.getenv("databse_name")
    )


if __name__ == "__main__":
    try:
        conn = get_connection()
        print("MySQL connection successful!")
        conn.close()
    except mysql.connector.Error as error:
        print("Database connection failed:", error)
