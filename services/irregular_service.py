from database_client import supabase

def get_irregular_students():
    response = supabase.from_("enrollments_view") \
        .select("studentid, studentname, program, yearlevel, enrollmentstatus") \
        .eq("enrollmentstatus", "Enrolled - Irregular") \
        .execute()

    if not response.data:
        return []

    seen = set()
    unique_students = []
    for row in response.data:
        sid = row["studentid"]
        if sid not in seen:
            seen.add(sid)
            unique_students.append({
                "studentid": sid,
                "studentname": row.get("studentname", ""),
                "program": row.get("program", ""),
                "yearlevel": row.get("yearlevel", ""),
                "status": "Irregular",
                "remarks": row.get("enrollmentstatus", "")
            })
    return unique_students


def get_irregular_subjects(student_id, schoolyear, semester_term):
    response = supabase.table("enrollments_view") \
        .select("*") \
        .eq("studentid", student_id) \
        .eq("schoolyear", schoolyear) \
        .eq("semester_term", semester_term) \
        .execute()
    return response.data if response.data else []


def add_manual_subject(student_id, semester_id, subjectname, units, grade):
    from services.semester_service import get_all_semesters
    semesters = get_all_semesters()
    semester = next((s for s in semesters if s["semesterid"] == semester_id), None)
    if not semester:
        raise ValueError("Invalid semester ID")

    return supabase.table("manual_subjects").insert({
        "studentid": student_id,
        "semesterid": semester_id,
        "schoolyear": semester["schoolyear"],
        "semester_term": semester["term"],
        "subjectname": subjectname,
        "units": units,
        "grade": grade or None
    }).execute()


def delete_manual_subject(subject_id):
    return supabase.table("manual_subjects") \
        .delete() \
        .eq("subjectid", subject_id) \
        .execute()