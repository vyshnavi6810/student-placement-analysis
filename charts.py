
import os
import matplotlib.pyplot as plt

from analysis import (
    get_department_report,
    get_package_summary,
    get_skill_demand
)


def create_reports_folder():
    os.makedirs("reports", exist_ok=True)


def plot_department_placement():
    df = get_department_report()

    if df.empty:
        print("No department data available yet.")
        return

    create_reports_folder()

    plt.figure(figsize=(9, 5))
    plt.bar(
        df["department"],
        df["placement_rate_percent"]
    )

    plt.title("Department-wise Placement Rate")
    plt.xlabel("Department")
    plt.ylabel("Placement Rate (%)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    plt.savefig("reports/department_placement.png")
    plt.show()
    plt.close()


def plot_package_summary():
    summary = get_package_summary()

    if summary["records"] == 0:
        print("No package data available yet.")
        return

    create_reports_folder()

    labels = ["Mean Package", "Median Package"]
    values = [summary["mean_lpa"], summary["median_lpa"]]

    plt.figure(figsize=(7, 5))
    plt.bar(labels, values)

    plt.title("Mean vs Median Placement Package")
    plt.ylabel("Package (LPA)")
    plt.tight_layout()

    plt.savefig("reports/package_summary.png")
    plt.show()
    plt.close()


def plot_skill_demand():
    df = get_skill_demand()

    if df.empty:
        print("No skill data available yet.")
        return

    create_reports_folder()

    plt.figure(figsize=(9, 5))
    plt.barh(df["skill_name"], df["student_count"])

    plt.title("Student Skill Demand")
    plt.xlabel("Number of Students")
    plt.ylabel("Skill")
    plt.gca().invert_yaxis()
    plt.tight_layout()

    plt.savefig("reports/skill_demand.png")
    plt.show()
    plt.close()



if __name__ == "__main__":
    plot_department_placement()
    plot_package_summary()
    plot_skill_demand()

