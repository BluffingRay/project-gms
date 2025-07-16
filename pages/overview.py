from services.curriculum_service import get_all_curriculum_subjects
import streamlit as st
import pandas as pd
from services.enrollment_service import get_all_enrollments

st.set_page_config(page_title="Overview", layout="wide")
st.title("Enrollment and Grades Overview")

# -------------------------
# Fetch Data
# -------------------------
data = get_all_enrollments()
df = pd.DataFrame(data)

if df.empty:
    st.warning("No data available.")
    st.stop()

# -------------------------
# Filters
# -------------------------
latest_school_year = sorted(df["schoolyear"].dropna().unique())[-1]
latest_year_level = sorted(df["yearlevel"].dropna().unique())[0]
latest_term = sorted(df["semester_term"].dropna().unique())[0]
latest_program = sorted(df["program"].dropna().unique())[0]

col1, col2, col3, col4 = st.columns(4)
school_year_filter = col1.selectbox("School Year", sorted(df["schoolyear"].unique()), index=sorted(df["schoolyear"].unique()).index(latest_school_year))
year_level_filter = col2.selectbox("Year Level", sorted(df["yearlevel"].unique()), index=0)
semester_filter = col3.selectbox("Semester Term", sorted(df["semester_term"].unique()), index=0)
program_filter = col4.selectbox("Program", sorted(df["program"].unique()), index=0)

filtered_df = df[
    (df["schoolyear"] == school_year_filter) &
    (df["yearlevel"] == year_level_filter) &
    (df["semester_term"] == semester_filter) &
    (df["program"] == program_filter)
]

if filtered_df.empty:
    st.info("No data to display after applying filters.")
    st.stop()

# -------------------------
# KPIs
# -------------------------
total_enrollment = filtered_df["studentname"].nunique()

def has_problematic_grade(grades):
    return any(
        (pd.isna(g) or str(g).strip().upper() == "INC" or str(g).strip() == "")
        for g in grades
    )

students_with_problems = (
    filtered_df.groupby("studentname")["grade"]
    .apply(has_problematic_grade)
)

problematic_students = students_with_problems.sum()
students_with_grades = total_enrollment - problematic_students

col1, col2, col3 = st.columns(3)
col1.metric("📊 Total Enrollment", total_enrollment)
col2.metric("✅ Students with Complete Grades", students_with_grades)
col3.metric("⚠️ Students with Issues", problematic_students)

# -------------------------
# Build Custom Table
# -------------------------
unique_subjects = sorted(filtered_df["subjectname"].dropna().unique())
students = filtered_df[["studentname", "studentremarks"]].drop_duplicates().reset_index(drop=True)

for subject in unique_subjects:
    subject_df = filtered_df[filtered_df["subjectname"] == subject][["studentname", "grade"]]
    subject_df = subject_df.drop_duplicates(subset=["studentname"], keep="last").set_index("studentname")["grade"]
    students[subject] = students["studentname"].map(subject_df).fillna("—")

# -------------------------
# GWA
# -------------------------
# Ensure subject_units is defined
curriculum_df = pd.DataFrame(get_all_curriculum_subjects())
subject_units = curriculum_df.set_index("name")["units"].to_dict()

# Compute GWA only if all subjects have valid numeric grades
def compute_gwa(row):
    total_gp = 0
    total_units = 0

    for subject in unique_subjects:
        value = row.get(subject, "—")
        try:
            grade = float(value)
            units = subject_units.get(subject, 0)
            if 1.0 <= grade <= 5.0 and units > 0:
                total_gp += grade * units
                total_units += units
            else:
                return "—"  # Incomplete or invalid grade
        except:
            return "—"  # Not a numeric grade

    if total_units == 0:
        return "—"
    
    return round(total_gp / total_units, 2)

# Add GWA and clean Remarks
students["GWA"] = students.apply(compute_gwa, axis=1)
students.rename(columns={"studentremarks": "Remarks"}, inplace=True)
students["Remarks"] = students["Remarks"].fillna("-")

# Final column order
columns_order = ["studentname"] + unique_subjects + ["GWA", "Remarks"]
missing_cols = [col for col in columns_order if col not in students.columns]
if missing_cols:
    st.error(f"Missing columns: {missing_cols}")
    st.stop()

# Rename display column
display_df = students[columns_order]
display_df.rename(columns={"studentname": "Name"}, inplace=True)


# -------------------------
# Checkbox Filters
# -------------------------
st.subheader("Additional Filters")
col1, col2, col3 = st.columns(3)
show_inc = col1.checkbox("Show INC")
show_dropped = col2.checkbox("Show Dropped or Failed")
show_missing = col3.checkbox("Show Missing Grades")

if show_inc or show_dropped or show_missing:
    def row_matches(row):
        values = list(row[unique_subjects])
        if show_inc and any("INC" in str(v) for v in values):
            return True
        if show_dropped and any(str(v).strip().upper() in ["5.0", "DROPPED", "DROP"] for v in values):
            return True
        if show_missing and any(v in ["", "—"] for v in values):
            return True
        return False

    display_df = display_df[display_df.apply(row_matches, axis=1)]

# -------------------------
# Final Display
# -------------------------
st.dataframe(display_df, use_container_width=True)
