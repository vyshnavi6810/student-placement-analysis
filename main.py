
import os
import pandas as pd

from analysis import (
    get_placement_rate,
    get_department_report,
    get_package_summary,
    get_skill_demand
)

from charts import (
    plot_department_placement,
    plot_package_summary,
    plot_skill_demand
)


def main():
    os.makedirs("reports", exist_ok=True)

    print("\n===== STUDENT PLACEMENT DATA ANALYSIS =====")

    # 1. Overall placement statistics
    placement = get_placement_rate()

    print("\n--- Overall Placement Rate ---")
    print(f"Eligible Students: {placement['eligible_students']}")
    print(f"Placed Students: {placement['placed_students']}")
    print(f"Placement Rate: {placement['placement_rate']}%")

    # 2. Department report
    department_df = get_department_report()

    print("\n--- Department Report ---")
    print(department_df.to_string(index=False))

    if not department_df.empty:
        department_df.to_csv(
            "reports/department_report.csv",
            index=False
        )

    # 3. Skill-demand report
    skills_df = get_skill_demand()

    print("\n--- Skill Demand Report ---")
    print(skills_df.to_string(index=False))

    if not skills_df.empty:
        skills_df.to_csv(
            "reports/skill_demand_report.csv",
            index=False
        )

    # 4. Package summary
    package = get_package_summary()

    print("\n--- Package Summary ---")
    print(package)

    pd.DataFrame([package]).to_csv(
        "reports/package_summary.csv",
        index=False
    )

    # 5. Generate charts
    print("\n--- Generating Charts ---")

    plot_department_placement()
    plot_package_summary()
    plot_skill_demand()

    print("\nProject execution completed!")


if __name__ == "__main__":
    main()
