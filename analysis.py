
import pandas as pd
import numpy as np
from db_connection import get_connection


def get_placement_rate():
    """Calculate placement rate among eligible students."""
    conn = get_connection()

    query = """
        SELECT
            COUNT(*) AS eligible_students,
            SUM(
                CASE WHEN EXISTS (
                    SELECT 1
                    FROM placements p
                    WHERE p.student_id = s.student_id
                      AND p.status = 'PLACED'
                ) THEN 1 ELSE 0 END
            ) AS placed_students
        FROM students s
        WHERE s.is_eligible = TRUE
    """

    try:
        df = pd.read_sql(query, conn)
        eligible = int(df.loc[0, "eligible_students"])
        placed = int(df.loc[0, "placed_students"] or 0)

        rate = (placed / eligible * 100) if eligible else 0

        return {
            "eligible_students": eligible,
            "placed_students": placed,
            "placement_rate": round(rate, 2)
        }
    finally:
        conn.close()


def get_department_report():
    """Compare placement outcomes by department."""
    conn = get_connection()

    query = """
        SELECT
            s.department,
            COUNT(*) AS eligible_students,
            SUM(
                CASE WHEN EXISTS (
                    SELECT 1
                    FROM placements p
                    WHERE p.student_id = s.student_id
                      AND p.status = 'PLACED'
                ) THEN 1 ELSE 0 END
            ) AS placed_students
        FROM students s
        WHERE s.is_eligible = TRUE
        GROUP BY s.department
        ORDER BY s.department
    """

    try:
        df = pd.read_sql(query, conn)
        df["placed_students"] = df["placed_students"].fillna(0).astype(int)

        df["placement_rate_percent"] = np.where(
            df["eligible_students"] > 0,
            df["placed_students"] / df["eligible_students"] * 100,
            0
        ).round(2)

        return df
    finally:
        conn.close()


def get_package_summary():
    """Calculate mean and median of recorded placed packages."""
    conn = get_connection()

    query = """
        SELECT package_lpa
        FROM placements
        WHERE status = 'PLACED'
          AND package_lpa IS NOT NULL
    """

    try:
        df = pd.read_sql(query, conn)
        packages = pd.to_numeric(
            df["package_lpa"], errors="coerce"
        ).dropna()

        if packages.empty:
            return {
                "records": 0,
                "mean_lpa": None,
                "median_lpa": None
            }

        return {
            "records": len(packages),
            "mean_lpa": round(float(np.mean(packages)), 2),
            "median_lpa": round(float(np.median(packages)), 2)
        }
    finally:
        conn.close()



def get_skill_demand():
    """Count students who have each recorded skill."""
    conn = get_connection()

    query = """
        SELECT
            sk.skill_name,
            COUNT(DISTINCT ss.student_id) AS student_count
        FROM skills sk
        JOIN student_skills ss
            ON sk.skill_id = ss.skill_id
        GROUP BY sk.skill_id, sk.skill_name
        ORDER BY student_count DESC, sk.skill_name
    """

    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()


if __name__ == "__main__":
    print("\n--- Placement Rate ---")
    print(get_placement_rate())

    print("\n--- Department Report ---")
    print(get_department_report().to_string(index=False))

    print("\n--- Package Summary ---")
    print(get_package_summary())

    print("\n--- Skill Demand Report ---")
    print(get_skill_demand().to_string(index=False))