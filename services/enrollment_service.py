from database_client import supabase
from datetime import date


def add_enrollment(student_id, curriculum_id, semester_id, enrollment_status="Enrolled", remarks="Regular"):
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


def update_student_status(student_id, program, yearlevel, remarks="Enrolled"):
    supabase.table("students") \
        .update({
            "program": program,
            "yearlevel": yearlevel,
            "enrollmentstatus": remarks
        }) \
        .eq("studentid", student_id) \
        .execute()

