from database_client import supabase


def get_all_curriculum_subjects():
    response = supabase.table('curriculum_subjects').select("*").execute()
    return response.data


def add_curriculum_subject(data):
    return supabase.table('curriculum_subjects').insert(data).execute()


def delete_curriculum_subject(subject_id):
    return supabase.table('curriculum_subjects').delete().eq('id', subject_id).execute()
