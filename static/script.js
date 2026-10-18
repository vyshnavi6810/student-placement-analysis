
let departmentData = [];
let skillData = [];
let packageData = {};
let chartInstances = {};

async function getJSON(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Request failed: ${url}`);
    }

    return response.json();
}

function drawChart(id, config) {
    if (chartInstances[id]) {
        chartInstances[id].destroy();
    }

    const canvas = document.getElementById(id);
    chartInstances[id] = new Chart(canvas, config);
}

function commonOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { usePointStyle: true, boxWidth: 8 }
            }
        }
    };
}

function renderDepartmentChart() {
    drawChart("departmentChart", {
        type: "bar",
        data: {
            labels: departmentData.map(d => d.department),
            datasets: [{
                label: "Placement Rate (%)",
                data: departmentData.map(d => d.placement_rate_percent),
                backgroundColor: "#e87559",
                borderRadius: 5,
                maxBarThickness: 45
            }]
        },
        options: {
            ...commonOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback: value => value + "%" }
                }
            }
        }
    });
}

function renderPackageChart() {
    const hasData = packageData.mean_lpa !== null &&
                    packageData.median_lpa !== null;

    drawChart("packageChart", {
        type: "bar",
        data: {
            labels: ["Mean Package", "Median Package"],
            datasets: [{
                label: "Package (LPA)",
                data: hasData
                    ? [packageData.mean_lpa, packageData.median_lpa]
                    : [null, null],
                backgroundColor: ["#e87559", "#2f9d91"],
                borderRadius: 5
            }]
        },
        options: {
            ...commonOptions(),
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderSkillChart() {
    drawChart("skillChart", {
        type: "bar",
        data: {
            labels: skillData.map(s => s.skill_name),
            datasets: [{
                label: "Students",
                data: skillData.map(s => s.student_count),
                backgroundColor: "#2f9d91",
                borderRadius: 5
            }]
        },
        options: {
            ...commonOptions(),
            indexAxis: "y",
            scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

function renderTables() {
    const departmentTable = document.getElementById("departmentTable");

    departmentTable.replaceChildren();

    if (departmentData.length === 0) {
        departmentTable.innerHTML =
            '<tr><td colspan="4">No department data available.</td></tr>';
    } else {
        departmentData.forEach(d => {
            const row = document.createElement("tr");

            [d.department, d.eligible_students, d.placed_students,
             `${Number(d.placement_rate_percent).toFixed(2)}%`
            ].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            departmentTable.appendChild(row);
        });
    }

    const skillTable = document.getElementById("skillTable");
    skillTable.replaceChildren();

    if (skillData.length === 0) {
        skillTable.innerHTML =
            '<tr><td colspan="2">No skill data available.</td></tr>';
    } else {
        skillData.forEach(s => {
            const row = document.createElement("tr");

            [s.skill_name, s.student_count].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            skillTable.appendChild(row);
        });
    }
}

async function loadDashboard() {
    try {
        const [summary, departments, skills] = await Promise.all([
            getJSON("/api/summary"),
            getJSON("/api/departments"),
            getJSON("/api/skills")
        ]);

        departmentData = departments;
        skillData = skills;
        packageData = summary.package;

        document.getElementById("eligible").textContent =
            summary.placement.eligible_students;

        document.getElementById("placed").textContent =
            summary.placement.placed_students;

        document.getElementById("rate").textContent =
            `${summary.placement.placement_rate}%`;

        document.getElementById("mean").textContent =
            summary.package.mean_lpa === null
                ? "N/A"
                : `${summary.package.mean_lpa} LPA`;

        renderDepartmentChart();
        renderPackageChart();
        renderSkillChart();
        renderTables();
    } catch (error) {
        console.error(error);
        alert("Could not load dashboard data. Check Flask and the MySQL connection.");
    }
}

function downloadCSV(kind) {
    let headers;
    let rows;

    if (kind === "department") {
        headers = [
            "Department", "Eligible Students", "Placed Students",
            "Placement Rate (%)"
        ];

        rows = departmentData.map(d => [
            d.department, d.eligible_students, d.placed_students,
            d.placement_rate_percent
        ]);
    } else {
        headers = ["Skill", "Student Count"];
        rows = skillData.map(s => [s.skill_name, s.student_count]);
    }

    const quote = value =>
        `"${String(value ?? "").replaceAll('"', '""')}"`;

    const csv = [headers, ...rows]
        .map(row => row.map(quote).join(","))
        .join("\r\n");

    const blob = new Blob(["\uFEFF" + csv], {
        type: "text/csv;charset=utf-8;"
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${kind}_report.csv`;
    link.click();
    URL.revokeObjectURL(url);
}

loadDashboard();
