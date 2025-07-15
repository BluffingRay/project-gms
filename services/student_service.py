from database_client import supabase

def get_all_students():
    return supabase.table('students').select('*').execute().data

def add_student(data):
    return supabase.table('students').insert(data).execute()

def update_student(student_id, updates):
    return supabase.table('students').update(updates).eq("StudentID", student_id).execute()

def get_student_by_id(student_id):
    return supabase.table('students').select('*').eq('StudentID', student_id).single().execute().data

def update_student_info(student_id, data: dict):
    return (
        supabase.table("students")
        .update(data)
        .eq("studentid", student_id)
        .execute()
    )
