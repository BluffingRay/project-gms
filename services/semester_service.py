from database_client import supabase


def get_all_semesters():
    return supabase.table('semesters').select('*').execute().data


def add_semester(semester_data):
    return supabase.table('semesters').insert(semester_data).execute()


def update_semester(semesterid, updated_data):
    return supabase.table('semesters').update(updated_data).eq('semesterid', semesterid).execute()


def delete_semester(semesterid):
    return supabase.table('semesters').delete().eq('semesterid', semesterid).execute()
