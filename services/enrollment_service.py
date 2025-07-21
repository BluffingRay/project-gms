from database_client import supabase
from datetime import date


def add_enrollment(student_id, curriculum_id, semester_id, enrollment_status="Enrolled - Regular", remarks="Regular"):
    data = {
        "studentid": student_id,
        "curriculumid": curriculum_id,
        "semesterid": semester_id,
        "enrollmentdate": date.today().isoformat(),
        "enrollmentstatus": enrollment_status,
        "remarks": remarks
    }
    return supabase.table("enrollments").insert(data).execute()


def get_all_students():
    response = supabase.table("students").select("*").execute()
    return response.data


def get_curriculum_subjects(program, yearlevel, term):
    response = supabase.table("curriculum_subjects").select("*").eq("program", program).eq("yearlevel", yearlevel).eq("term", term).execute()
    return response.data


def get_all_semesters():
    response = supabase.table("semesters").select("*").execute()
    return response.data

def get_all_enrollments():
    response = supabase.from_("enrollments_view").select("*").execute()
    return response.data

def delete_enrollment(enrollment_id):
    supabase.table("enrollments").delete().eq("enrollmentid", enrollment_id).execute()

def delete_all_enrollments_for_student_semester(student_id, semester_id):
    enrollment_ids = supabase.rpc("delete_enrollments_for_student_semester", {
        "param_studentid": student_id,
        "param_semesterid": semester_id
    }).execute()


    if enrollment_ids.data:
        for enrollment in enrollment_ids.data:
            delete_enrollment(enrollment["enrollmentid"])


def update_student_status(student_id, program, yearlevel, remarks="Enrolled", status="Regular"):
    supabase.table("students") \
        .update({
            "program": program,
            "yearlevel": yearlevel,
            "enrollmentstatus": remarks,
            "status": status
        }) \
        .eq("studentid", student_id) \
        .execute()

def get_all_regular_enrollments():
    response = supabase.from_("enrollments_view") \
        .select("*") \
        .eq("enrollmentstatus", "Enrolled - Regular") \
        .execute()
    return response.data

def update_enrollment_status_and_remarks(student_id, semester_id, enrollment_status, remarks):
    supabase.table("enrollments") \
        .update({
            "enrollmentstatus": enrollment_status,
            "remarks": remarks
        }) \
        .eq("studentid", student_id) \
        .eq("semesterid", semester_id) \
        .execute()


def migrate_student_to_semester_subjects(student_id, target_semester_id):
    semester_subjects = get_subjects_for_semester(target_semester_id)
    if not semester_subjects:
        return "No subjects offered for the selected semester."

    migrated = 0
    skipped = 0

    for subject in semester_subjects:
        curriculum_id = subject["curriculum_subject_id"]

        # Check if already enrolled
        existing = supabase.table("enrollments").select("enrollmentid") \
            .eq("studentid", student_id) \
            .eq("semesterid", target_semester_id) \
            .eq("curriculumid", curriculum_id) \
            .execute()

        if existing.data:
            skipped += 1
            continue

        add_enrollment(
            student_id=student_id,
            curriculum_id=curriculum_id,
            semester_id=target_semester_id
        )
        migrated += 1

    return f"Enrolled {migrated} subjects. Skipped {skipped} (already enrolled)."



def get_students_in_semester(semester_id):
    # Get enrollments for the semester, including student info
    response = supabase.from_("enrollments_view") \
        .select("studentid, studentname") \
        .eq("semesterid", semester_id) \
        .execute()

    # Remove duplicates by studentid because one student can have many enrollments
    if response.data:
        unique_students = {s['studentid']: s for s in response.data}
        return list(unique_students.values())
    return []


def get_subjects_for_semester(semester_id):
    response = supabase.table("semester_subjects").select("""
        id,
        semester_id,
        curriculum_subject_id,
        curriculum_subjects(name, code, units, program, yearlevel, term)
    """).eq("semester_id", semester_id).execute()

    return response.data






