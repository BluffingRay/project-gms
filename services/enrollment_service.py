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


def migrate_enrollments_for_student(student_id, source_semester_id, target_semester_id):
    # 1. Get all enrollments for the student in the source semester
    response = supabase.table("enrollments").select("*") \
        .eq("studentid", student_id) \
        .eq("semesterid", source_semester_id) \
        .execute()

    if response.status_code != 200:
        raise Exception(f"Failed to fetch enrollments: status {response.status_code}")

    source_enrollments = response.data
    if not source_enrollments:
        return "No enrollments found to migrate."

    migrated_count = 0
    skipped_count = 0

    for enrollment in source_enrollments:
        curriculum_id = enrollment["curriculumid"]

        # 2. Check if enrollment already exists for target semester and curriculum_id
        check_resp = supabase.table("enrollments").select("enrollmentid") \
            .eq("studentid", student_id) \
            .eq("semesterid", target_semester_id) \
            .eq("curriculumid", curriculum_id) \
            .execute()

        if check_resp.status_code != 200:
            raise Exception(f"Failed to check existing enrollment: status {check_resp.status_code}")

        if check_resp.data and len(check_resp.data) > 0:
            # Already enrolled in this subject for the target semester
            skipped_count += 1
            continue

        # 3. Insert new enrollment for target semester
        new_enrollment = {
            "studentid": student_id,
            "curriculumid": curriculum_id,
            "semesterid": target_semester_id,
            "enrollmentdate": date.today().isoformat(),
            "enrollmentstatus": enrollment.get("enrollmentstatus", "Enrolled"),
            "remarks": enrollment.get("remarks", "Regular")
        }

        insert_resp = supabase.table("enrollments").insert(new_enrollment).execute()
        if insert_resp.status_code != 201:  # 201 Created
            raise Exception(f"Failed to insert enrollment for curriculum {curriculum_id}: status {insert_resp.status_code}")

        migrated_count += 1

    return f"Migration complete: {migrated_count} enrollments migrated, {skipped_count} enrollments skipped (already exist)."


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
