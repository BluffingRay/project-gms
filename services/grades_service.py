from database_client import supabase

def upsert_grade(enrollment_id, grade):
    existing = supabase.table("grades").select("gradeid").eq("enrollmentid", enrollment_id).execute()
    if existing.data and len(existing.data) > 0:
        grade_id = existing.data[0]["gradeid"]
        return supabase.table("grades").update({"grade": grade}).eq("gradeid", grade_id).execute()
    else:
        return supabase.table("grades").insert({"enrollmentid": enrollment_id, "grade": grade}).execute()
