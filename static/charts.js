
// charts.js - Interactive charts for admin pages

let placementCharts = {};

async function loadPlacementAnalytics() {
    try {
        const response = await fetch(
            "/api/analytics" + window.location.search
        );

        if (!response.ok) {
            throw new Error("Unable to load analytics");
        }

        const data = await response.json();

        renderAllPlacementCharts(data);

    } catch (error) {
        console.error("Chart loading error:", error);
    }
}

function createPlacementChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    if (placementCharts[canvasId]) {
        placementCharts[canvasId].destroy();
    }

    placementCharts[canvasId] = new Chart(
        canvas,
        config
    );
}

function chartOptions(title, yTitle = "") {
    return {
        responsive: true,
        maintainAspectRatio: true,
        interaction: {
            intersect: false,
            mode: "index"
        },
        plugins: {
            title: {
                display: true,
                text: title
            },
            legend: {
                display: true,
                position: "bottom"
            },
            tooltip: {
                enabled: true
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: !!yTitle,
                    text: yTitle
                }
            }
        }
    };
}

function renderAllPlacementCharts(data) {

    const departments = data.departments || [];
    const years = data.years || [];
    const skills = data.skills || [];
    const packages = data.packages || [];

    // Department-wise Placement
    const departmentLabels = departments.map(
        item => item.department
    );

    const departmentRates = departments.map(
        item => Number(item.placement_rate_percent || 0)
    );

    const departmentCanvas =
        document.getElementById("departmentChart");

    if (departmentCanvas) {
        createPlacementChart("departmentChart", {
            type: "bar",
            data: {
                labels: departmentLabels,
                datasets: [{
                    label: "Placement Rate (%)",
                    data: departmentRates,
                    borderWidth: 1
                }]
            },
            options: chartOptions(
                "Department-wise Placement",
                "Placement Rate (%)"
            )
        });
    }

    // Year-wise Placement Trend
    if (document.getElementById("yearChart")) {
        createPlacementChart("yearChart", {
            type: "line",
            data: {
                labels: years.map(item => item.year),
                datasets: [{
                    label: "Placements",
                    data: years.map(item => Number(item.placements)),
                    tension: 0.3,
                    fill: false
                }]
            },
            options: chartOptions(
                "Year-wise Placement Trend",
                "Number of Placements"
            )
        });
    }

    // Skill Demand
    if (document.getElementById("skillChart")) {
        createPlacementChart("skillChart", {
            type: "bar",
            data: {
                labels: skills.map(item => item.skill_name),
                datasets: [{
                    label: "Number of Students",
                    data: skills.map(
                        item => Number(item.student_count)
                    ),
                    borderWidth: 1
                }]
            },
            options: chartOptions(
                "Student Skill Demand",
                "Number of Students"
            )
        });
    }

    // Package Analysis
    if (document.getElementById("packageChart")) {
        createPlacementChart("packageChart", {
            type: "bar",
            data: {
                labels: packages.map(
                    item => item.company + " - " + item.role
                ),
                datasets: [{
                    label: "Average Package (LPA)",
                    data: packages.map(
                        item => Number(item.avg_package || 0)
                    ),
                    borderWidth: 1
                }]
            },
            options: chartOptions(
                "Company and Role-wise Packages",
                "Package (LPA)"
            )
        });
    }

    // Dynamic chart for individual admin sections
    const sectionCanvas = document.getElementById("sectionChart");

    if (sectionCanvas) {
        const section = sectionCanvas.dataset.section;

        let labels = [];
        let values = [];
        let title = "";
        let valueLabel = "";

        if (section === "departments") {
            labels = departmentLabels;
            values = departmentRates;
            title = "Department-wise Placement Rate";
            valueLabel = "Placement Rate (%)";

        } else if (section === "skills") {
            labels = skills.map(item => item.skill_name);
            values = skills.map(item => Number(item.student_count));
            title = "Skill Demand";
            valueLabel = "Number of Students";

        } else if (section === "packages") {
            labels = packages.map(
                item => item.company + " - " + item.role
            );
            values = packages.map(
                item => Number(item.avg_package || 0)
            );
            title = "Package Analysis";
            valueLabel = "Average Package (LPA)";

        } else if (section === "placements") {
            labels = years.map(item => item.year);
            values = years.map(item => Number(item.placements));
            title = "Year-wise Placement Trend";
            valueLabel = "Placements";

        } else if (section === "students") {
            labels = departmentLabels;
            values = departments.map(
                item => Number(item.students || 0)
            );
            title = "Students by Department";
            valueLabel = "Number of Students";
        }

        createPlacementChart("sectionChart", {
            type: section === "placements" ? "line" : "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: valueLabel,
                    data: values,
                    tension: 0.3,
                    borderWidth: 1
                }]
            },
            options: chartOptions(title, valueLabel)
        });
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadPlacementAnalytics
);


async function downloadSectionCSV(section) {
    try {
        if (!section || section === "undefined") {
            throw new Error("Section name is missing");
        }

        const params = new URLSearchParams(window.location.search);

        const response = await fetch(
            `/admin/${section}/export?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`CSV download failed: ${response.status}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = `${section}_records.csv`;

        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(url);

    } catch (error) {
        console.error(error);
        alert("Unable to download CSV. Please try again.");
    }
}

window.downloadSectionCSV = downloadSectionCSV;