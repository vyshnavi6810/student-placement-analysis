
from flask import Flask, jsonify, render_template
from analysis import (
    get_placement_rate,
    get_department_report,
    get_package_summary,
    get_skill_demand
)

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/api/summary")
def summary():
    return jsonify({
        "placement": get_placement_rate(),
        "package": get_package_summary()
    })

@app.route("/api/departments")
def departments():
    df = get_department_report()
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/skills")
def skills():
    df = get_skill_demand()
    return jsonify(df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
