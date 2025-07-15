# Project GMS: Grade Management System

A simple system designed to manage student enrollment, grades, and academic performance records in streamlit.

## Key Features

- **Enrollment Overview**
  - View student enrollments by year, program, and semester.
  - Quick KPIs: Total enrolled students, grade completion status, problematic records.

- **Grade Management**
  - Edit, update, and manage student grades per semester.
  - Compute General Weighted Averages (GWA) automatically.

- **Student Information**
  - Easily update student information such as year level, program, and other details.
  - Editable field.

## Technologies Used

- Python 3.x
- Streamlit for the web interface
- Supabase for database services
  
## Notes

- Grade arrangement heavily based on University of Southeastern Philippine's system.
- Might only be usable for semester and grading system similar to USePs.

## Developer Setup Note
This project uses **Streamlit `secrets.toml`** for managing database credentials securely.

To run locally, create your own `.streamlit/secrets.toml` file:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-secret-key"
```

## Status
In Progress: Core functionalities are in place. Feature testing and error-handling, and design in the works.
