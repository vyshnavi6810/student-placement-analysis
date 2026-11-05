
document.addEventListener("DOMContentLoaded", function () {
    const analyticsElement = document.getElementById("student-analytics");

    if (!analyticsElement) {
        console.warn("Student analytics data not found on this page.");
        return;
    }

    if (typeof Chart === "undefined") {
        console.error("Chart.js is not loaded.");
        return;
    }

    let data;

    try {
        data = JSON.parse(analyticsElement.textContent);
    } catch (error) {
        console.error("Invalid analytics JSON:", error);
        return;
    }

    function createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);

        if (!canvas) return;

        // Prevent duplicate chart instances
        const existingChart = Chart.getChart(canvas);
        if (existingChart) existingChart.destroy();

        new Chart(canvas, config);
    }

    // 1. Department Placement Chart
    createChart("studentDepartmentChart", {
        type: "bar",
        data: {
            labels: (data.departments || []).map(r => r.department),
            datasets: [
                {
                    label: "Eligible Students",
                    data: (data.departments || []).map(r => r.eligible || 0),
                    backgroundColor: "#8b9dc3"
                },
                {
                    label: "Placed Students",
                    data: (data.departments || []).map(r => r.placed || 0),
                    backgroundColor: "#36a2a0"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // 2. Skills Chart
    createChart("studentSkillChart", {
        type: "bar",
        data: {
            labels: (data.skills || []).map(r => r.skill_name),
            datasets: [{
                label: "Students",
                data: (data.skills || []).map(r => r.student_count),
                backgroundColor: "#9274bd"
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            scales: {
                x: { beginAtZero: true }
            }
        }
    });

    // 3. Year-wise Placement Chart
    createChart("studentYearChart", {
        type: "line",
        data: {
            labels: (data.years || []).map(r => r.year),
            datasets: [{
                label: "Placement Records",
                data: (data.years || []).map(r => r.placements),
                borderColor: "#36a2a0",
                backgroundColor: "rgba(54, 162, 160, 0.2)",
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // 4. Job Roles Chart
    createChart("studentRoleChart", {
        type: "bar",
        data: {
            labels: (data.roles || []).map(r => r.role),
            datasets: [{
                label: "Placement Records",
                data: (data.roles || []).map(r => r.placement_count),
                backgroundColor: "#d18b68"
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            scales: {
                x: { beginAtZero: true }
            }
        }
    });

    console.log("Student charts initialized successfully.");
});
