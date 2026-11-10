# 🎓 Student Placement Analysis System

A web-based **Student Placement Analysis System** designed to analyze and visualize placement data across multiple universities. It helps administrators monitor placement performance, analyze student skills, compare packages, and manage placement submissions through an interactive dashboard.

## 🚀 Key Features

- **User Authentication:** Secure registration and login.
- **Multi-University Support:** Maintains separate placement data for different universities.
- **Interactive Dashboard:** Displays total students, placed students, average package, and placement percentage.
- **Department Analysis:** Visualizes department-wise placement statistics.
- **Skill Demand Analysis:** Identifies the most in-demand skills.
- **Package Analysis:** Analyzes average and median salary packages.
- **Role-Based Analysis:** Compares packages across job roles.
- **Student Self-Service:** Students can submit their placement details.
- **Admin Verification:** Administrators can review, approve, or reject submissions.
- **CSV Export:** Download analytical reports.

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | MySQL |
| Data Analysis | Pandas, NumPy |
| Data Visualization | Chart.js |
| Deployment | Render |
| Cloud Database | Aiven MySQL |
| Version Control | Git, GitHub |

## 🏗️ System Architecture

1. **Frontend:** HTML, CSS, and JavaScript provide the user interface.
2. **Backend:** Flask handles authentication, application logic, and API requests.
3. **Database:** MySQL stores university, student, skill, and placement information.
4. **Analysis:** Pandas and NumPy process placement data.
5. **Visualization:** Chart.js displays analytical results.

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/vyshnavi6810/student-placement-analysis.git
```

### 2. Navigate to the Project Folder

```bash
cd student-placement-analysis
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file and configure your database connection details.

Do not upload passwords, secret keys, or database credentials to GitHub.

### 5. Run the Application

```bash
python app.py
```

Open the application in your browser using the local URL displayed in the terminal.

## 📊 Main Modules

- Authentication and User Management
- Student Placement Data Management
- Admin Submission Verification
- Department-wise Analytics
- Skill Demand Analysis
- Package and Role Analysis
- CSV Report Generation

## 🌐 Live Demo

[Student Placement Analysis System] (https://student-placement-analysis-ez63.onrender.com)

## 👩‍💻 Team Contributions

The project was developed collaboratively, covering database design, backend development, frontend design, JavaScript integration, testing, and deployment.

## 🎯 Project Objective

To provide a centralized platform for analyzing student placement performance across multiple universities and support data-driven placement decisions.

## 📌 Future Enhancements

- Advanced placement prediction.
- More interactive analytical reports.
- Additional university-level comparisons.
- Enhanced student and administrator features.

---

