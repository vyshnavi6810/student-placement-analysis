let departmentData = [];
let skillData = [];
let packageData = {};
let chartInstances = {};
let roleData = [];
let departmentPackageData = [];
// Fetch data from Flask API
async function getJSON(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Request failed: ${url} (${response.status})`);
    }

    return response.json();
}

// Display dashboard messages
function showMessage(message) {
    const box = document.getElementById("dashboardMessage");

    if (box) {
        box.textContent = message;
        box.classList.add("visible");
    } else {
        console.error(message);
    }
}

function hideMessage() {
    const box = document.getElementById("dashboardMessage");

    if (box) {
        box.classList.remove("visible");
    }
}

// Show the selected dashboard section
function showSection(sectionId, button) {
    document.querySelectorAll(".content-panel").forEach(panel => {
        panel.classList.remove("visible");
    });

    document.querySelectorAll(".feature-card").forEach(card => {
        card.classList.remove("active");
    });

    const section = document.getElementById(sectionId);

    if (!section) {
        showMessage(`Section not found: ${sectionId}`);
        return;
    }

    section.classList.add("visible");

    if (button) {
        button.classList.add("active");
    }

    hideMessage();
}

// Common chart options
function commonOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    usePointStyle: true,
                    boxWidth: 8
                }
            }
        }
    };
}

// Create or update a chart
function drawChart(id, config) {
    const canvas = document.getElementById(id);

    if (!canvas) {
        showMessage(`Chart element not found: ${id}`);
        return;
    }

    if (typeof Chart === "undefined") {
        showMessage("Chart.js is not loaded. Check index.html.");
        return;
    }

    const container = canvas.closest(".chart-container");

    if (container) {
        container.classList.add("chart-visible");
    }

    if (chartInstances[id]) {
        chartInstances[id].destroy();
    }

    chartInstances[id] = new Chart(canvas, config);
}

// Department placement chart
function renderDepartmentChart() {
    if (departmentData.length === 0) {
        showMessage("No department data available.");
        return;
    }

    hideMessage();

    drawChart("departmentChart", {
        type: "bar",
        data: {
            labels: departmentData.map(item => item.department),
            datasets: [{
                label: "Placement Rate (%)",
                data: departmentData.map(item =>
                    Number(item.placement_rate_percent ?? 0)
                ),
                backgroundColor: "#f0cc37",
                borderColor: "#d9b52a",
                borderWidth: 1,
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
                    ticks: {
                        callback: value => `${value}%`
                    }
                }
            }
        }
    });
}

// Package analysis chart
function showPackageView(view) {
    const overall = document.getElementById("packageChartContainer");
    const role = document.getElementById("rolePackageContainer");
    const department = document.getElementById("departmentPackageContainer");
    const title = document.getElementById("packageViewTitle");

    if (!overall || !role || !department || !title) {
        showMessage("Package Analysis HTML elements are missing.");
        return;
    }

    overall.hidden = view !== "overall";
    role.hidden = view !== "role";
    department.hidden = view !== "department";

    const titles = {
        overall: "Overall Package Distribution",
        role: "Average Package by Job Role",
        department: "Average Package by Department"
    };

    title.innerHTML = `<h3>${titles[view]}</h3>`;

    hideMessage();

    if (view === "overall") {
        renderPackageChart();
    } else if (view === "role") {
        renderRolePackageChart();
    } else if (view === "department") {
        renderDepartmentPackageChart();
    }
}


function renderPackageChart() {
    const mean = packageData.mean_lpa;
    const median = packageData.median_lpa;

    if (mean == null && median == null) {
        showMessage("No package data available.");
        return;
    }

    hideMessage();

    drawChart("packageChart", {
        type: "bar",
        data: {
            labels: ["Mean Package", "Median Package"],
            datasets: [{
                label: "Package (LPA)",
                data: [
                    mean == null ? null : Number(mean),
                    median == null ? null : Number(median)
                ],
                backgroundColor: ["#f0cc37", "#e5b72e"],
                borderRadius: 5
            }]
        },
        options: {
            ...commonOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Package (LPA)"
                    }
                }
            }
        }
    });
}


function renderRolePackageChart() {
    if (!roleData.length) {
        showMessage("No role-wise placement data available.");
        return;
    }

    hideMessage();

    drawChart("rolePackageChart", {
        type: "bar",
        data: {
            labels: roleData.map(item => item.role),
            datasets: [{
                label: "Average Package (LPA)",
                data: roleData.map(item =>
                    item.average_package_lpa == null
                        ? null
                        : Number(item.average_package_lpa)
                ),
                backgroundColor: "#f0cc37",
                borderColor: "#d9b52a",
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            ...commonOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Average Package (LPA)"
                    }
                }
            }
        }
    });

    const table = document.getElementById("rolePackageTable");

    if (table) {
        table.replaceChildren();

        roleData.forEach(item => {
            const row = document.createElement("tr");

            [
                item.role ?? "N/A",
                item.placement_count ?? 0,
                item.average_package_lpa == null
                    ? "N/A"
                    : Number(item.average_package_lpa).toFixed(2)
            ].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            table.appendChild(row);
        });
    }
}


function renderDepartmentPackageChart() {
    if (!departmentPackageData.length) {
        showMessage("No department-wise package data available.");
        return;
    }

    hideMessage();

    drawChart("departmentPackageChart", {
        type: "bar",
        data: {
            labels: departmentPackageData.map(item => item.department),
            datasets: [{
                label: "Average Package (LPA)",
                data: departmentPackageData.map(item =>
                    item.average_package_lpa == null
                        ? null
                        : Number(item.average_package_lpa)
                ),
                backgroundColor: "#e5b72e",
                borderRadius: 5
            }]
        },
        options: {
            ...commonOptions(),
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Average Package (LPA)"
                    }
                }
            }
        }
    });

    const table = document.getElementById("departmentPackageTable");

    if (table) {
        table.replaceChildren();

        departmentPackageData.forEach(item => {
            const row = document.createElement("tr");

            [
                item.department ?? "N/A",
                item.average_package_lpa == null
                    ? "N/A"
                    : Number(item.average_package_lpa).toFixed(2)
            ].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            table.appendChild(row);
        });
    }
}

// Skills analysis chart
function renderSkillChart() {
    if (skillData.length === 0) {
        showMessage("No skills data available.");
        return;
    }

    hideMessage();

    drawChart("skillChart", {
        type: "bar",
        data: {
            labels: skillData.map(item => item.skill_name),
            datasets: [{
                label: "Students",
                data: skillData.map(item =>
                    Number(item.student_count ?? 0)
                ),
                backgroundColor: "#f0cc37",
                borderRadius: 5
            }]
        },
        options: {
            ...commonOptions(),
            indexAxis: "y",
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Populate department and skills tables
function renderTables() {
    const departmentTable = document.getElementById("departmentTable");

    if (departmentTable) {
        departmentTable.replaceChildren();

        if (departmentData.length === 0) {
            departmentTable.innerHTML =
                '<tr><td colspan="4">No department data available.</td></tr>';
        } else {
            departmentData.forEach(item => {
                const row = document.createElement("tr");

                const values = [
                    item.department ?? "N/A",
                    item.eligible_students ?? 0,
                    item.placed_students ?? 0,
                    item.placement_rate_percent == null
                        ? "N/A"
                        : `${Number(item.placement_rate_percent).toFixed(2)}%`
                ];

                values.forEach(value => {
                    const cell = document.createElement("td");
                    cell.textContent = value;
                    row.appendChild(cell);
                });

                departmentTable.appendChild(row);
            });
        }
    }

    const skillTable = document.getElementById("skillTable");

    if (skillTable) {
        skillTable.replaceChildren();

        if (skillData.length === 0) {
            skillTable.innerHTML =
                '<tr><td colspan="2">No skills data available.</td></tr>';
        } else {
            skillData.forEach(item => {
                const row = document.createElement("tr");

                [item.skill_name ?? "N/A", item.student_count ?? 0]
                    .forEach(value => {
                        const cell = document.createElement("td");
                        cell.textContent = value;
                        row.appendChild(cell);
                    });

                skillTable.appendChild(row);
            });
        }
    }
}

// Safely update dashboard values
function updateText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}

// Load dashboard data
async function loadDashboard() {
    hideMessage();

    try {
        const [summary, departments, skills, roles, departmentPackages] =
    await Promise.all([
        getJSON("/api/summary"),
        getJSON("/api/departments"),
        getJSON("/api/skills"),
        getJSON("/api/roles"),
        getJSON("/api/department-packages")
    ]);

        departmentData = Array.isArray(departments) ? departments : [];
        skillData = Array.isArray(skills) ? skills : [];
        roleData = Array.isArray(roles) ? roles : [];

        packageData = summary.package ?? {};

        const placement = summary.placement ?? {};
        departmentPackageData = Array.isArray(departmentPackages)
             ? departmentPackages
             : [];
        updateText("eligible", placement.eligible_students ?? 0);
        updateText("placed", placement.placed_students ?? 0);

        updateText(
            "rate",
            placement.placement_rate == null
                ? "N/A"
                : `${placement.placement_rate}%`
        );

        updateText(
            "mean",
            packageData.mean_lpa == null
                ? "N/A"
                : `${packageData.mean_lpa} LPA`
        );

        updateText(
            "packageMean",
            packageData.mean_lpa == null
                ? "N/A"
                : `${packageData.mean_lpa} LPA`
        );

        updateText(
            "packageMedian",
            packageData.median_lpa == null
                ? "N/A"
                : `${packageData.median_lpa} LPA`
        );

        updateText("packageRecords", packageData.records ?? 0);

        updateText("reportEligible", placement.eligible_students ?? 0);
        updateText("reportPlaced", placement.placed_students ?? 0);

        updateText(
            "reportRate",
            placement.placement_rate == null
                ? "N/A"
                : `${placement.placement_rate}%`
        );

        updateText(
            "reportMean",
            packageData.mean_lpa == null
                ? "N/A"
                : `${packageData.mean_lpa} LPA`
        );

        updateText(
            "reportMedian",
            packageData.median_lpa == null
                ? "N/A"
                : `${packageData.median_lpa} LPA`
        );

        renderTables();

        console.log("Dashboard data loaded successfully.", {
            placement,
            package: packageData,
            departments: departmentData,
            skills: skillData,
            roles: roleData
        });

    } catch (error) {
        console.error("Dashboard loading error:", error);

        showMessage(
            "Could not load dashboard data. Check Flask, MySQL, and API routes."
        );
    }
}
// Download department or skills report as CSV
function downloadCSV(kind) {
    let headers;
    let rows;

    if (kind === "department") {
        headers = [
            "Department",
            "Eligible Students",
            "Placed Students",
            "Placement Rate (%)"
        ];

        rows = departmentData.map(item => [
            item.department,
            item.eligible_students,
            item.placed_students,
            item.placement_rate_percent
        ]);
    } else {
        headers = ["Skill", "Student Count"];

        rows = skillData.map(item => [
            item.skill_name,
            item.student_count
        ]);
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

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}

// Support existing inline onclick handlers in index.html
window.showSection = showSection;
window.renderDepartmentChart = renderDepartmentChart;
window.renderPackageChart = renderPackageChart;
window.renderSkillChart = renderSkillChart;
window.downloadCSV = downloadCSV;

// Load data after the HTML has been parsed
document.addEventListener("DOMContentLoaded", loadDashboard);